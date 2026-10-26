from __future__ import annotations

import gzip
import json
from pathlib import Path
from typing import Any

import pytest
from modal_app.sync_run import sync_once, verify_manifest
from modal_app.train_grpo import DEFAULTS, build_rows, merge

from invoiceops.adapters import trl_env
from invoiceops.adapters.rollout_log import (
    RolloutRecorder,
    ShardWriter,
    _attribute_calls,
    sha256_bytes,
)
from invoiceops.adapters.trl_env import InvoiceOpsToolEnv, bundle_for_row
from invoiceops.agents.oracle import solve

from .conftest import by_family


def _meta() -> dict[str, Any]:
    return {"run_name": "t-run", "model": "m", "revision": "r", "prompt_version": "v3d"}


def _read_jsonl_gz(path: Path) -> list[dict[str, Any]]:
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


@pytest.fixture
def recorder(tmp_path: Path):
    rec = RolloutRecorder(tmp_path / "run", _meta())
    trl_env.set_rollout_recorder(rec)
    yield rec, tmp_path / "run"
    trl_env.set_rollout_recorder(None)


def _env() -> InvoiceOpsToolEnv:
    return InvoiceOpsToolEnv()


def _rows(n: int) -> list[dict[str, Any]]:
    task = by_family("F01", 0).public.task_id
    return [
        {
            "prompt": [{"role": "user", "content": "p"}],
            "task_id": task,
            "generated": "",
            "row_index": 0,
        }
        for _ in range(n)
    ]


def _generation(
    n: int,
    *,
    completion_ids: list[list[int]] | None = None,
    masks: list[list[int]] | None = None,
    completions: list[Any] | None = None,
) -> dict[str, Any]:
    return {
        "prompts": [[{"role": "user", "content": "p"}] for _ in range(n)],
        "prompt_ids": [[11, 12] for _ in range(n)],
        "completion_ids": completion_ids or [[100, 999] for _ in range(n)],
        "tool_mask_raw": masks or [[1, 1] for _ in range(n)],
        "tool_mask_final": masks or [[1, 1] for _ in range(n)],
        "completions": completions or [[{"role": "assistant", "content": "x"}] for _ in range(n)],
        "logprobs": [[-0.1, -0.2] for _ in range(n)],
        "safety_masked": [],
        "decoded": ["text"] * n,
    }


def _finish(rec: RolloutRecorder, envs: list[Any]) -> dict[str, Any]:
    return rec.finish_batch(
        advantages=[0.0] * len(envs),
        environments=envs,
        eos_token_ids={999},
        num_generations=8,
        global_step_after=1,
        log_history=[{"step": 1, "loss": 0.5}],
    )


def test_shard_writer_is_atomic_and_hashed(tmp_path: Path) -> None:
    path = tmp_path / "s.jsonl.gz"
    w = ShardWriter(path)
    w.write({"a": 1})
    w.write({"b": 2})
    info = w.finalize()
    assert not w.tmp_path.exists()
    assert info["records"] == 2
    assert info["sha256"] == sha256_bytes(path.read_bytes())
    assert _read_jsonl_gz(path) == [{"a": 1}, {"b": 2}]

    w2 = ShardWriter(tmp_path / "gone.jsonl.gz")
    w2.write({"x": 1})
    w2.abort()
    assert not w2.tmp_path.exists()
    assert not (tmp_path / "gone.jsonl.gz").exists()


def test_batch_records_identity_and_all_outcomes(recorder: Any) -> None:
    rec, run = recorder
    envs = [_env() for _ in range(4)]
    rec.begin_batch(global_step=0, micro_step=0, epoch=0.0, inputs=_rows(4), tool_specs={})
    for i, env in enumerate(envs):
        env.reset(task_id=by_family("F01", 0).public.task_id, generated="", row_index=i)
    # Drive real tool traffic on two envs; leave two untouched.
    envs[0].list_queue()
    envs[1].list_queue()
    solve(envs[1]._episode)
    envs[0]._mark_rollout_truncated()  # safety-wrapper path: excluded from reward
    for env in envs:
        env.get_reward()
    gen = _generation(4)
    gen["safety_masked"] = [0]
    gen["tool_mask_final"] = [[0, 0], [1, 1], [1, 1], [1, 1]]
    rec.capture_generation(**gen)
    summary = _finish(rec, envs)
    assert summary["rollouts"] == 4 and summary["tool_events"] == 2

    records = _read_jsonl_gz(run / "trajectories" / "batch-0000.jsonl.gz")
    assert [r["rollout_id"] for r in records] == [
        "t-run/b0000/r00",
        "t-run/b0000/r01",
        "t-run/b0000/r02",
        "t-run/b0000/r03",
    ]
    assert [r["group_index"] for r in records] == [0] * 4  # num_generations=8 > n
    truncated, solved, *rest = records
    assert truncated["status"].startswith("cutoff")
    assert truncated["reward"] is None
    assert truncated["safety_masked"] is True
    assert truncated["mask_final_all_zero"] is True
    assert truncated["verifier_role"] == "diagnostic_only"  # still regraded for the record
    assert solved["status"] == "terminal_submitted"
    assert solved["reward"] == 1.0
    assert solved["verifier"]["reward"] == 1.0
    assert solved["env"]["action_log"], "episode action log must be preserved"
    for r in rest:
        assert r["status"] == "terminal_submitted" or r["verifier"] is not None
    manifest = json.loads((run / "manifest.json").read_text())
    assert manifest["counters"]["rollouts"] == 4
    shard_rel = "trajectories/batch-0000.jsonl.gz"
    assert manifest["files"][shard_rel]["records"] == 4
    for env in envs:
        env._episode.close()


def test_second_batch_rebinds_pooled_envs(recorder: Any) -> None:
    rec, run = recorder
    envs = [_env(), _env()]
    for b in range(2):
        rec.begin_batch(global_step=b, micro_step=b, epoch=0.0, inputs=_rows(2), tool_specs={})
        for env in envs:
            env.reset(task_id=by_family("F01", 0).public.task_id)
        rec.capture_generation(**_generation(2))
        _finish(rec, envs)
    assert (run / "trajectories" / "batch-0001.jsonl.gz").exists()
    r0 = _read_jsonl_gz(run / "trajectories" / "batch-0001.jsonl.gz")[0]
    assert r0["batch_ordinal"] == 1 and r0["rollout_id"].startswith("t-run/b0001/")
    for env in envs:
        env._episode.close()


def test_call_attribution_matches_prefixes_and_flags_ambiguity() -> None:
    prompt_ids = [[1, 2], [1, 2], [3, 4]]
    completion_ids = [[10, 50, 60, 20], [10, 50, 60, 20], [7]]
    masks = [[1, 0, 0, 1], [1, 0, 0, 1], [1]]
    calls = [
        {"inputs": [[1, 2], [1, 2], [3, 4]], "outputs": []},
        {"inputs": [[1, 2, 10, 50, 60], [1, 2, 10, 50, 60]], "outputs": []},
    ]
    result, anomalies = _attribute_calls(calls, prompt_ids, completion_ids, masks)
    assert not anomalies
    assert result[0] == {0: (0, 0), 1: (1, 0)}
    assert result[1] == {0: (0, 1), 1: (1, 1)}
    assert result[2] == {0: (0, 2)}
    assert calls[1]["ambiguous_slots"] == {"0": 2}  # identical rollouts: first free wins

    missing_call = [{"inputs": [[1, 2], [1, 2], [3, 4]], "outputs": []}]
    result, anomalies = _attribute_calls(missing_call, prompt_ids, completion_ids, masks)
    assert anomalies  # turns 1 of rollouts 0,1 have no call
    assert result[0] == {0: (0, 0)}


def test_call_attribution_with_partial_second_turn() -> None:
    # Rollout 1 ended after turn 0 (no 0-run): it only participates in the first call.
    prompt_ids = [[1], [1]]
    completion_ids = [[5, 9], [5]]
    masks = [[1, 0], [1]]
    calls = [{"inputs": [[1], [1]], "outputs": []}, {"inputs": [[1, 5, 9]], "outputs": []}]
    result, anomalies = _attribute_calls(calls, prompt_ids, completion_ids, masks)
    assert not anomalies
    assert result[1] == {0: (0, 1)}


def test_turn_finish_reason_read_from_call_outputs(recorder: Any) -> None:
    """call.outputs[slot] is a list of completions (vLLM n=1); read element 0."""
    rec, run = recorder
    env = _env()
    rec.begin_batch(global_step=0, micro_step=0, epoch=0.0, inputs=_rows(1), tool_specs={})
    env.reset(task_id=by_family("F01", 0).public.task_id)
    env.get_reward()
    rec.model_call(
        {
            "kind": "vllm_generate",
            "ts": 0.0,
            "seconds": 0.1,
            "n_inputs": 1,
            "sampling": {"n": 1, "temperature": 1.0},
            "inputs": [[11, 12]],
            "outputs": [
                [
                    {
                        "token_ids": [100, 999],
                        "finish_reason": "stop",
                        "stop_reason": None,
                        "cumulative_logprob": -0.3,
                        "sampled_logprobs": [-0.1, -0.2],
                    }
                ]
            ],
        }
    )
    rec.capture_generation(**_generation(1))
    _finish(rec, [env])
    record = _read_jsonl_gz(run / "trajectories" / "batch-0000.jsonl.gz")[0]
    assert record["status"] != "assembly_error", record.get("assembly_error")
    assert record["turns"][0]["finish_reason"] == "stop"
    assert record["turns"][0]["call_index"] == 0
    calls = _read_jsonl_gz(run / "model_calls" / "batch-0000.jsonl.gz")
    assert calls[0]["outputs"][0][0]["finish_reason"] == "stop"
    env._episode.close()


def test_rolled_back_env_events_are_marked(recorder: Any) -> None:
    """Two executed tool rounds; TRL kept only the first (one 0-run in the mask)."""
    rec, run = recorder
    env = _env()
    rec.begin_batch(global_step=0, micro_step=0, epoch=0.0, inputs=_rows(1), tool_specs={})
    env.reset(task_id=by_family("F01", 0).public.task_id)
    obs1 = json.loads(env.list_queue())
    obs2 = json.loads(env.check_inbox())
    # Two sequential assistant turns, one tool call each. The second round's tool
    # message was rolled back by TRL's overlong check: its assistant message stays
    # last with pending tool_calls, the env event survives as a rolled-back tail.
    gen = _generation(
        1,
        completion_ids=[[10, 50, 60, 20]],
        masks=[[1, 0, 0, 1]],
        completions=[
            [
                {
                    "role": "assistant",
                    "tool_calls": [{"function": {"name": "list_queue", "arguments": "{}"}}],
                },
                {"role": "tool", "name": "list_queue", "content": json.dumps(obs1)},
                {
                    "role": "assistant",
                    "tool_calls": [{"function": {"name": "check_inbox", "arguments": "{}"}}],
                },
            ]
        ],
    )
    rec.capture_generation(**gen)
    _finish(rec, [env])
    record = _read_jsonl_gz(run / "trajectories" / "batch-0000.jsonl.gz")[0]
    events = record["env"]["events"]
    assert [e["tool"] for e in events] == ["list_queue", "check_inbox"]
    assert events[0]["rolled_back"] is False and events[0]["round"] == 0
    assert events[1]["rolled_back"] is True  # executed but its result was dropped
    assert events[1]["observation"] == obs2
    assert record["env"]["kept_tool_rounds"] == 1
    assert record["env"]["last_tool_calls_executed_but_rolled_back"] is True
    env._episode.close()


def test_abort_batch_writes_interrupted_shard(recorder: Any) -> None:
    rec, run = recorder
    rec.begin_batch(global_step=5, micro_step=5, epoch=0.0, inputs=_rows(3), tool_specs={})
    env = _env()
    env.reset(task_id=by_family("F01", 0).public.task_id)
    env.list_queue()
    rec.abort_batch(RuntimeError("boom"))
    path = run / "trajectories" / "batch-0000-interrupted.jsonl.gz"
    records = _read_jsonl_gz(path)
    assert len(records) == 3
    assert records[0]["status"] == "interrupted"
    assert records[0]["env_events"] and records[0]["env_events"][0]["tool"] == "list_queue"
    assert json.loads((run / "manifest.json").read_text())["batches"][0]["status"] == "interrupted"
    env._episode.close()


def test_record_dataset_freezes_bundles(recorder: Any) -> None:
    rec, run = recorder
    rows = build_rows(merge(DEFAULTS, {"generated_variants": 6}))
    rec.record_dataset(rows, bundle_for_row)
    index = (run / "dataset" / "manifest.jsonl").read_text().splitlines()
    assert len(index) == len(rows) == 36 + 6
    bundles = _read_jsonl_gz(run / "dataset" / "bundles.jsonl.gz")
    assert len(bundles) == len(rows)
    generated = json.loads(index[-1])
    assert generated["generated"] and generated["split"] == "train"
    assert bundles[-1]["bundle"]["private"]["task_id"] == generated["private_task_id"]


def test_dispatch_failure_and_error_paths_are_recorded(recorder: Any) -> None:
    rec, run = recorder
    env = _env()
    rec.begin_batch(global_step=0, micro_step=0, epoch=0.0, inputs=_rows(1), tool_specs={})
    env.reset(task_id=by_family("F01", 0).public.task_id)
    # A call after the episode ended still reaches the env and is recorded.
    env._episode.done = True
    env._episode.end_reason = "submitted"
    env.list_queue()
    env.get_reward()
    gen = _generation(1)
    rec.capture_generation(**gen)
    _finish(rec, [env])
    record = _read_jsonl_gz(run / "trajectories" / "batch-0000.jsonl.gz")[0]
    assert record["env"]["events"][0]["observation"]["error"]["code"] == "episode_finished"
    assert record["env"]["events"][0]["ok"] is False
    assert record["status"] == "terminal_submitted"
    env._episode.close()


def test_dispatch_exception_is_recorded_then_reraised(recorder: Any) -> None:
    rec, run = recorder
    env = _env()
    rec.begin_batch(global_step=0, micro_step=0, epoch=0.0, inputs=_rows(1), tool_specs={})
    env.reset(task_id=by_family("F01", 0).public.task_id)
    assert env._episode is not None

    def boom(tool: str, arguments: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError("disk on fire")

    env._episode.step = boom  # type: ignore[method-assign]
    with pytest.raises(RuntimeError, match="disk on fire"):
        env.list_queue()  # TRL would catch this into an error tool message
    rec.capture_generation(**_generation(1))
    _finish(rec, [env])
    record = _read_jsonl_gz(run / "trajectories" / "batch-0000.jsonl.gz")[0]
    event = record["env"]["events"][0]
    assert event["tool"] == "list_queue" and "disk on fire" in event["raised"]
    env._episode.close()


def test_manifest_tracks_every_finalized_file(recorder: Any) -> None:
    rec, run = recorder
    rec.begin_batch(global_step=0, micro_step=0, epoch=0.0, inputs=_rows(1), tool_specs={})
    env = _env()
    env.reset(task_id=by_family("F01", 0).public.task_id)
    rec.capture_generation(**_generation(1))
    _finish(rec, [env])
    (run / "checkpoints" / "checkpoint-1").mkdir(parents=True)
    (run / "checkpoints" / "checkpoint-1" / "adapter.bin").write_bytes(b"x")
    rec.close("completed")
    manifest = json.loads((run / "manifest.json").read_text())
    assert manifest["status"] == "completed"
    files = manifest["files"]
    assert "manifest.json" not in files
    assert files["checkpoints/checkpoint-1/adapter.bin"]["sha256"] == sha256_bytes(b"x")
    env._episode.close()


# -- downloader ---------------------------------------------------------------


class _Entry:
    def __init__(self, path: str, content: bytes, mtime: int = 1) -> None:
        self.path = path
        self.size = len(content)
        self.mtime = mtime
        self.type = 1  # FileEntryType.FILE
        self._content = content


class _FakeVolume:
    def __init__(self, files: dict[str, bytes]) -> None:
        self.files = {k: _Entry(k, v) for k, v in files.items()}

    def listdir(self, path: str, recursive: bool = False) -> list[_Entry]:
        root = path.strip("/")
        return [e for p, e in sorted(self.files.items()) if p.startswith(root)]

    def read_file_into_fileobj(self, path: str, fh: Any) -> int:
        data = self.files[path]._content
        fh.write(data)
        return len(data)


def test_sync_once_downloads_new_and_changed_only(tmp_path: Path) -> None:
    vol = _FakeVolume(
        {
            "train/run/manifest.json": b"{}",
            "train/run/trajectories/batch-0000.jsonl.gz": b"shard1",
            "train/run/trajectories/pending.jsonl.gz.tmp": b"ignore me",
        }
    )
    local = tmp_path / "run"
    state: dict[str, Any] = {"files": {}}
    stats = sync_once(vol, "train/run", local, state)
    assert sorted(stats["downloaded"]) == [
        "manifest.json",
        "trajectories/batch-0000.jsonl.gz",
    ]
    assert (local / "trajectories" / "batch-0000.jsonl.gz").read_bytes() == b"shard1"
    assert not (local / "trajectories" / "pending.jsonl.gz.tmp").exists()

    stats = sync_once(vol, "train/run", local, state)
    assert stats["downloaded"] == [] and stats["skipped"] == 2

    vol.files["train/run/manifest.json"] = _Entry("train/run/manifest.json", b'{"x":1}', mtime=2)
    stats = sync_once(vol, "train/run", local, state)
    assert stats["downloaded"] == ["manifest.json"]
    assert json.loads((local / "manifest.json").read_text()) == {"x": 1}


def test_verify_manifest_reports_missing_and_mismatch(tmp_path: Path) -> None:
    local = tmp_path / "run"
    (local / "a").mkdir(parents=True)
    (local / "a" / "f.bin").write_bytes(b"good")
    manifest = {
        "status": "completed",
        "files": {
            "a/f.bin": {"sha256": sha256_bytes(b"good")},
            "a/g.bin": {"sha256": sha256_bytes(b"lost")},
            "a/bad.bin": {"sha256": sha256_bytes(b"nope")},
        },
    }
    (local / "a" / "bad.bin").write_bytes(b"bad")
    (local / "manifest.json").write_text(json.dumps(manifest))
    report = verify_manifest(local)
    assert report["manifest_status"] == "completed"
    assert report["ok"] == 1
    assert report["missing"] == ["a/g.bin"]
    assert report["mismatched"] == ["a/bad.bin"]
