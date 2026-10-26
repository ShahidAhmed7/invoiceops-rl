"""Durable raw-trajectory recording for GRPO tool-loop rollouts (TRL 1.16.0).

One ``RolloutRecorder`` lives for the whole training run. The trainer wrapper
(``modal_app.grpo_safety``) reports batch boundaries and generation results; the
environment (``InvoiceOpsToolEnv``) reports resets, tool executions, rewards and
cutoffs through the module-level handle installed by ``set_rollout_recorder``.
The vLLM ``llm.generate`` wrapper reports raw backend calls. Nothing here
imports torch/trl/modal, so the whole pipeline is testable locally.

Run-directory layout::

    meta.json                     model/revision/prompt/seed/stack snapshot
    manifest.json                 rewritten atomically after every finalized shard
    dataset/manifest.jsonl        one line per dataset row (index, ids, spec, bundle hash)
    dataset/bundles.jsonl.gz      frozen TaskBundle dump per row (replay source)
    logs/steps.jsonl              trainer.state.log_history entries, appended per batch
    model_calls/batch-NNNN.jsonl.gz   one line per raw llm.generate call
    trajectories/batch-NNNN.jsonl.gz  one line per rollout (all outcomes)

Every shard is staged as ``<name>.tmp`` and renamed atomically; ``.tmp`` files
are never complete shards.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import time
import traceback
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from invoiceops.tasks.model import TaskBundle
    from invoiceops.verification.verifier import VerifierResult


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds")


def canonical_bytes(obj: Any) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_json(obj: Any) -> str:
    return sha256_bytes(canonical_bytes(obj))


def _runs(mask: list[int]) -> list[tuple[int, int, int]]:
    """Contiguous (start, end, value) runs of a 0/1 mask."""
    out: list[tuple[int, int, int]] = []
    i = 0
    while i < len(mask):
        j = i + 1
        while j < len(mask) and mask[j] == mask[i]:
            j += 1
        out.append((i, j, mask[i]))
        i = j
    return out


def _zero_run_ends(mask: list[int]) -> list[int]:
    return [e for _, e, v in _runs(mask) if v == 0]


def _env_observation(content: Any) -> dict[str, Any] | None:
    """Parse a tool message's content back to an env observation dict, if it is one.

    Env-executed calls produce content ``json.dumps({"ok": ...})``; calls rejected
    before dispatch produce the Python repr of ``{"error": ...}``, which is not JSON.
    """
    if isinstance(content, str):
        try:
            obj = json.loads(content)
        except ValueError:
            return None
        if isinstance(obj, dict) and "ok" in obj:
            return obj
    return None


class ShardWriter:
    """Write a ``*.jsonl.gz`` shard via an atomic ``.tmp`` staging file."""

    def __init__(self, final_path: Path) -> None:
        self.final_path = final_path
        self.tmp_path = final_path.with_name(final_path.name + ".tmp")
        self._raw = open(self.tmp_path, "wb")  # noqa: SIM115 - closed in finalize/abort
        self._gz = gzip.GzipFile(fileobj=self._raw, mode="wb")
        self.records = 0

    def write(self, obj: Any) -> None:
        self._gz.write(canonical_bytes(obj) + b"\n")
        self.records += 1

    def finalize(self) -> dict[str, Any]:
        """Close, fsync and rename; return the manifest entry for the shard."""
        self._gz.close()
        self._raw.flush()
        os.fsync(self._raw.fileno())
        self._raw.close()
        os.replace(self.tmp_path, self.final_path)
        data = self.final_path.read_bytes()
        return {"sha256": sha256_bytes(data), "bytes": len(data), "records": self.records}

    def abort(self) -> None:
        try:
            self._gz.close()
            self._raw.close()
        finally:
            self.tmp_path.unlink(missing_ok=True)


@dataclass
class _Batch:
    ordinal: int
    global_step_before: int
    micro_step: int
    epoch: float | None
    started_utc: str
    started_monotonic: float
    inputs: list[dict[str, Any]]
    tool_specs: dict[str, Any]
    env_order: list[Any] = field(default_factory=list)  # index = rollout ordinal
    env_rows: dict[int, dict[str, Any]] = field(default_factory=dict)  # id(env) -> reset row
    events: dict[int, list[dict[str, Any]]] = field(default_factory=dict)  # id(env) -> events
    rewards: dict[int, dict[str, Any]] = field(default_factory=dict)  # id(env) -> reward record
    truncated: set[int] = field(default_factory=set)  # id(env) marked by safety wrapper
    reset_errors: list[dict[str, Any]] = field(default_factory=list)
    calls: list[dict[str, Any]] = field(default_factory=list)  # raw llm.generate records
    gen: dict[str, Any] | None = None  # capture_generation payload
    anomalies: list[str] = field(default_factory=list)


class RolloutRecorder:
    """Collect per-batch events and emit per-rollout trajectory shards."""

    def __init__(
        self,
        run_dir: Path,
        meta: dict[str, Any],
        *,
        commit: Callable[[], None] | None = None,
        resume: bool = False,
    ) -> None:
        self.run_dir = Path(run_dir)
        for sub in (
            "trajectories",
            "model_calls",
            "dataset",
            "logs",
            "checkpoints",
            "final_adapter",
        ):
            (self.run_dir / sub).mkdir(parents=True, exist_ok=True)
        self.commit_hook = commit
        self._batch: _Batch | None = None
        self._logged_steps = 0
        manifest_path = self.run_dir / "manifest.json"
        if resume and manifest_path.exists():
            # Continue an interrupted attempt in place: keep every committed
            # shard/batch, continue ordinal numbering, and mark a new attempt.
            self.manifest = json.loads(manifest_path.read_text())
            # Ordinals must stay unique across attempts, including interrupted
            # shards that never made the manifest's batch list.
            ordinals = [b["ordinal"] for b in self.manifest.get("batches", [])]
            for shard in (self.run_dir / "trajectories").glob("batch-*.jsonl.gz"):
                tail = shard.name.split("-", 2)[1]
                if tail.isdigit():
                    ordinals.append(int(tail))
            self._batch_count = (max(ordinals) + 1) if ordinals else 0
            prior_meta = self.manifest.get("meta") or {}
            prior_started = prior_meta.get("started_epoch")
            if not isinstance(prior_started, (int, float)):
                try:
                    prior_started = datetime.fromisoformat(
                        str(self.manifest.get("created_utc", "")).replace("Z", "+00:00")
                    ).timestamp()
                except ValueError:
                    prior_started = time.time()
            meta = dict(meta)
            meta["started_epoch"] = prior_started
            attempts = self.manifest.setdefault("attempts", [])
            attempts.append(
                {
                    "attempt": len(attempts) + 1,
                    "resumed_utc": utc_now(),
                    "first_batch_ordinal": self._batch_count,
                }
            )
            self.manifest["meta"] = {**prior_meta, **meta}
            self.manifest["status"] = "running"
            self.manifest.pop("status_detail", None)
            self.manifest.pop("closed_utc", None)
            self.meta = self.manifest["meta"]
            # The restarted trainer rebuilds log_history from the checkpoint, so
            # flush_step_logs replays it fully; lines are tagged per attempt.
            self._logged_steps = 0
        else:
            meta = dict(meta)
            meta["started_epoch"] = time.time()
            self.meta = meta
            self._batch_count = 0
            self.manifest = {
                "kind": "grpo-run-manifest",
                "version": 1,
                "run_name": meta.get("run_name"),
                "created_utc": utc_now(),
                "meta": meta,
                "status": "running",
                "files": {},
                "batches": [],
                "counters": {"rollouts": 0, "model_calls": 0, "tool_events": 0},
                "attempts": [{"attempt": 1, "started_utc": utc_now()}],
            }
        self._write_json(self.run_dir / "meta.json", self.meta)
        self._write_manifest()

    # -- file helpers --------------------------------------------------------

    @staticmethod
    def _write_json(path: Path, obj: Any) -> None:
        tmp = path.with_name(path.name + ".tmp")
        tmp.write_bytes(canonical_bytes(obj))
        os.replace(tmp, path)

    def _register(self, relpath: str, info: dict[str, Any]) -> None:
        self.manifest["files"][relpath] = info

    def _write_manifest(self) -> None:
        self._write_json(self.run_dir / "manifest.json", self.manifest)

    def _commit(self) -> None:
        if self.commit_hook is not None:
            self.commit_hook()

    # -- dataset freeze --------------------------------------------------------

    def record_dataset(
        self, rows: list[dict[str, Any]], bundle_resolver: Callable[[dict[str, Any]], TaskBundle]
    ) -> None:
        """Freeze the exact dataset rows plus every task bundle used (fixed or generated)."""
        index = self.run_dir / "dataset" / "manifest.jsonl"
        bundles = ShardWriter(self.run_dir / "dataset" / "bundles.jsonl.gz")
        index_tmp = index.with_name(index.name + ".tmp")
        with open(index_tmp, "w", encoding="utf-8") as fh:
            for i, row in enumerate(rows):
                bundle = bundle_resolver(row)
                dump = bundle.model_dump(mode="json")
                line = {
                    "row_index": row.get("row_index", i),
                    "task_id": row.get("task_id"),
                    "generated": row.get("generated"),
                    "bundle_sha256": sha256_json(dump),
                    "private_task_id": bundle.private.task_id,
                    "family": bundle.private.family,
                    "variant": bundle.private.variant,
                    "split": bundle.private.split,
                    "prompt_sha256": sha256_json(row.get("prompt")),
                }
                fh.write(json.dumps(line, ensure_ascii=False, sort_keys=True) + "\n")
                bundles.write({"row_index": line["row_index"], "bundle": dump})
        prior = self.manifest["files"].get("dataset/manifest.jsonl")
        if prior is not None:
            # Resumed attempt: the regenerated freeze must match byte-for-byte.
            new_sha = sha256_bytes(index_tmp.read_bytes())
            index_tmp.unlink()
            bundles.abort()
            if prior.get("sha256") != new_sha:
                raise RuntimeError("frozen dataset differs between attempts; refusing resume")
            self._write_manifest()
            self._commit()
            return
        os.replace(index_tmp, index)
        info = bundles.finalize()
        self._register(
            "dataset/manifest.jsonl",
            {
                "sha256": sha256_bytes(index.read_bytes()),
                "bytes": index.stat().st_size,
                "records": len(rows),
            },
        )
        self._register("dataset/bundles.jsonl.gz", info)
        self.manifest["dataset"] = {"rows": len(rows)}
        self._write_manifest()
        self._commit()

    # -- env-facing events (called by InvoiceOpsToolEnv) ------------------------

    def env_reset(self, env: Any, row: dict[str, Any]) -> None:
        b = self._batch
        if b is None:
            return
        b.env_order.append(env)
        b.env_rows[id(env)] = row
        b.events.setdefault(id(env), [])
        b.rewards.pop(id(env), None)
        b.truncated.discard(id(env))

    def env_reset_error(self, env: Any, row: dict[str, Any], error: str) -> None:
        b = self._batch
        if b is None:
            return
        ordinal = next((i for i, e in enumerate(b.env_order) if e is env), len(b.env_order))
        b.reset_errors.append({"ordinal": ordinal, "row": row, "error": error})

    def env_dispatch(
        self,
        env: Any,
        tool: str,
        arguments: dict[str, Any],
        observation: dict[str, Any],
        seconds: float,
    ) -> None:
        b = self._batch
        if b is None:
            return
        events = b.events.setdefault(id(env), [])
        events.append(
            {
                "seq": len(events),
                "ts": utc_now(),
                "tool": tool,
                "arguments": arguments,
                "observation": observation,
                "seconds": round(seconds, 4),
                "ok": bool(observation.get("ok")),
                "rolled_back": False,  # recomputed at finalize
            }
        )
        self.manifest["counters"]["tool_events"] += 1

    def env_dispatch_error(
        self, env: Any, tool: str, arguments: dict[str, Any], error: str, seconds: float
    ) -> None:
        b = self._batch
        if b is None:
            return
        events = b.events.setdefault(id(env), [])
        events.append(
            {
                "seq": len(events),
                "ts": utc_now(),
                "tool": tool,
                "arguments": arguments,
                "raised": error,
                "seconds": round(seconds, 4),
                "ok": False,
                "rolled_back": False,
            }
        )
        self.manifest["counters"]["tool_events"] += 1

    def env_reward(self, env: Any, verifier: VerifierResult | None, reward: float | None) -> None:
        b = self._batch
        if b is None:
            return
        b.rewards[id(env)] = {
            "reward": reward,
            "verifier": verifier.model_dump(mode="json") if verifier is not None else None,
        }

    def env_mark_truncated(self, env: Any) -> None:
        b = self._batch
        if b is None:
            return
        b.truncated.add(id(env))

    # -- trainer-facing events --------------------------------------------------

    def begin_batch(
        self,
        *,
        global_step: int,
        micro_step: int,
        epoch: float | None,
        inputs: list[dict[str, Any]],
        tool_specs: dict[str, Any],
    ) -> None:
        if self._batch is not None:
            # A previous batch never finalized: keep it as an interrupted shard.
            self.abort_batch(RuntimeError("begin_batch called while a batch was open"))
        self._batch = _Batch(
            ordinal=self._batch_count,
            global_step_before=global_step,
            micro_step=micro_step,
            epoch=epoch,
            started_utc=utc_now(),
            started_monotonic=time.monotonic(),
            inputs=[dict(r) for r in inputs],
            tool_specs=tool_specs,
        )
        self._batch_count += 1

    def model_call(self, record: dict[str, Any]) -> None:
        """Append one raw ``llm.generate`` call record (built by the modal-side glue)."""
        b = self._batch
        record = dict(record)
        if b is None:
            record["batch_ordinal"] = None
            # Calls outside a batch (unexpected) still go to a standalone shard.
            path = self.run_dir / "model_calls" / f"orphan-{int(time.time() * 1000)}.jsonl.gz"
            w = ShardWriter(path)
            w.write(record)
            self._register(f"model_calls/{path.name}", w.finalize())
            self._write_manifest()
            self._commit()
            return
        record["call_index"] = len(b.calls)
        b.calls.append(record)
        self.manifest["counters"]["model_calls"] += 1

    def capture_generation(
        self,
        *,
        prompts: list[Any],
        prompt_ids: list[list[int]],
        completion_ids: list[list[int]],
        tool_mask_raw: list[list[int]] | None,
        tool_mask_final: list[list[int]] | None,
        completions: list[Any],
        logprobs: list[Any] | None,
        safety_masked: list[int],
        decoded: list[str] | None = None,
    ) -> None:
        b = self._batch
        if b is None:
            return
        b.gen = {
            "prompts": prompts,
            "prompt_ids": prompt_ids,
            "completion_ids": completion_ids,
            "tool_mask_raw": tool_mask_raw,
            "tool_mask_final": tool_mask_final,
            "completions": completions,
            "logprobs": logprobs,
            "safety_masked": list(safety_masked),
            "decoded": decoded,
        }

    def flush_step_logs(self, log_history: list[dict[str, Any]]) -> None:
        """Append any new trainer log_history entries so they survive a crash."""
        new = log_history[self._logged_steps :]
        if not new:
            return
        path = self.run_dir / "logs" / "steps.jsonl"
        attempt = len(self.manifest.get("attempts") or [None])
        with open(path, "a", encoding="utf-8") as fh:
            for entry in new:
                line = {**entry, "attempt": attempt}
                fh.write(json.dumps(line, ensure_ascii=False, default=str) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        self._logged_steps += len(new)
        self._register(
            "logs/steps.jsonl",
            {"sha256": sha256_bytes(path.read_bytes()), "bytes": path.stat().st_size},
        )

    # -- batch finalization ------------------------------------------------------

    def finish_batch(
        self,
        *,
        advantages: list[Any] | None,
        environments: list[Any] | None,
        eos_token_ids: list[int] | set[int],
        num_generations: int,
        global_step_after: int,
        log_history: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Assemble per-rollout records, write both shards, update the manifest."""
        b = self._batch
        if b is None or b.gen is None:
            return {}
        gen = b.gen
        n = len(gen["prompt_ids"])
        mask_raw: list[list[int]] = gen["tool_mask_raw"] or [
            [1] * len(c) for c in gen["completion_ids"]
        ]
        mask_final: list[list[int]] = gen["tool_mask_final"] or mask_raw
        call_map, call_anomalies = _attribute_calls(
            b.calls, gen["prompt_ids"], gen["completion_ids"], mask_raw
        )
        b.anomalies.extend(call_anomalies)
        if environments is not None:
            if len(environments) != n:
                b.anomalies.append(f"environments length {len(environments)} != rollouts {n}")
            for i in range(min(n, len(b.env_order), len(environments))):
                if b.env_order[i] is not environments[i]:
                    b.anomalies.append(f"rollout {i}: bound env is not trainer.environments[i]")
        if len(b.env_order) != n:
            b.anomalies.append(f"{len(b.env_order)} env resets for {n} rollouts")
        for g in range(0, n, max(1, num_generations)):
            idxs = {b.inputs[i].get("row_index") for i in range(g, min(g + num_generations, n))}
            if len(idxs) > 1:
                b.anomalies.append(
                    f"reward group {g // num_generations} "
                    f"mixes dataset rows {sorted(idxs, key=repr)}"
                )

        safety_masked = set(gen["safety_masked"])
        traj_path = self.run_dir / "trajectories" / f"batch-{b.ordinal:04d}.jsonl.gz"
        traj = ShardWriter(traj_path)
        eos = set(eos_token_ids)
        for i in range(n):
            try:
                rec = self._assemble(b, i, call_map.get(i, {}), advantages, eos, num_generations)
            except Exception as exc:  # never lose the batch over one record
                b.anomalies.append(f"rollout {i} assembly failed: {exc!r}")
                rec = self._skeleton_record(b, i)
                rec["assembly_error"] = traceback.format_exc()
            rec["safety_masked"] = i in safety_masked
            rec["mask_final_all_zero"] = bool(mask_final[i]) and not any(mask_final[i])
            traj.write(rec)
        calls_path = self.run_dir / "model_calls" / f"batch-{b.ordinal:04d}.jsonl.gz"
        calls = ShardWriter(calls_path)
        for call in b.calls:
            calls.write(call)
        cinfo = calls.finalize()
        tinfo = traj.finalize()

        seconds = round(time.monotonic() - b.started_monotonic, 3)
        summary = {
            "ordinal": b.ordinal,
            "global_step_before": b.global_step_before,
            "global_step_after": global_step_after,
            "micro_step": b.micro_step,
            "epoch": b.epoch,
            "rollouts": n,
            "model_calls": len(b.calls),
            "tool_events": sum(len(v) for v in b.events.values()),
            "safety_masked": sorted(safety_masked),
            "seconds": seconds,
            "anomalies": b.anomalies,
            "trajectories": f"trajectories/{traj_path.name}",
            "model_calls_shard": f"model_calls/{calls_path.name}",
        }
        self.manifest["batches"].append(summary)
        self.manifest["counters"]["rollouts"] += n
        self._register(f"trajectories/{traj_path.name}", tinfo)
        self._register(f"model_calls/{calls_path.name}", cinfo)
        self.flush_step_logs(log_history)
        self._write_manifest()
        self._commit()
        self._batch = None
        return summary

    def abort_batch(self, exc: BaseException) -> None:
        """Persist whatever was collected for the in-flight batch, marked interrupted."""
        b = self._batch
        self._batch = None
        if b is None:
            return
        path = self.run_dir / "trajectories" / f"batch-{b.ordinal:04d}-interrupted.jsonl.gz"
        w = ShardWriter(path)
        n = len(b.inputs)
        gen = b.gen or {}
        prompt_ids = gen.get("prompt_ids") or []
        completion_ids = gen.get("completion_ids") or []
        for i in range(n):
            rec = {
                "rollout_id": f"{self.meta.get('run_name')}/b{b.ordinal:04d}/r{i:02d}",
                "status": "interrupted",
                "batch_ordinal": b.ordinal,
                "rollout_index": i,
                "input": b.inputs[i],
                "prompt_ids": prompt_ids[i] if i < len(prompt_ids) else None,
                "completion_ids": completion_ids[i] if i < len(completion_ids) else None,
                "env_events": b.events.get(id(b.env_order[i]), []) if i < len(b.env_order) else [],
            }
            w.write(rec)
        info = w.finalize()
        self.manifest["batches"].append(
            {
                "ordinal": b.ordinal,
                "global_step_before": b.global_step_before,
                "status": "interrupted",
                "error": repr(exc),
                "rollouts": n,
                "model_calls": len(b.calls),
                "env_resets": len(b.env_order),
                "trajectories": f"trajectories/{path.name}",
            }
        )
        if b.calls:
            cpath = self.run_dir / "model_calls" / f"batch-{b.ordinal:04d}-interrupted.jsonl.gz"
            cw = ShardWriter(cpath)
            for call in b.calls:
                cw.write(call)
            self._register(f"model_calls/{cpath.name}", cw.finalize())
        self._register(f"trajectories/{path.name}", info)
        self.manifest["counters"]["rollouts"] += n
        self._write_manifest()
        self._commit()

    def finalize_aux_files(self) -> None:
        """Hash every file under the run dir that shards did not already register.

        Covers config.json, meta.json, logs, checkpoint-*/ and final_adapter/ contents.
        ``manifest.json`` is excluded (it cannot hash itself); ``*.tmp`` staging files
        are excluded (a leftover .tmp means its shard never finalized).
        """
        leftovers = []
        rewritten: dict[str, Any] = dict(self.manifest.get("files_rewritten") or {})
        for path in sorted(self.run_dir.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(self.run_dir).as_posix()
            if rel == "manifest.json":
                continue
            if path.name.endswith(".tmp"):
                leftovers.append(rel)
                continue
            data = path.read_bytes()
            new = {"sha256": sha256_bytes(data), "bytes": len(data)}
            old = self.manifest["files"].get(rel)
            if old is None:
                self._register(rel, new)
            elif old.get("sha256") != new["sha256"]:
                # Aux files (meta.json, TRL completion dumps) may be rewritten by
                # a later attempt; shards are immutable and never land here.
                rewritten[rel] = {"previous": old, "current": new}
                self._register(rel, new)
        if rewritten:
            self.manifest["files_rewritten"] = rewritten
        if leftovers:
            self.manifest["unfinished_tmp_files"] = leftovers

    def close(self, status: str, detail: str | None = None) -> None:
        if self._batch is not None:
            self.abort_batch(RuntimeError("run closed with an open batch"))
        self.manifest["status"] = status
        if detail:
            self.manifest["status_detail"] = detail
        self.manifest["closed_utc"] = utc_now()
        self.finalize_aux_files()
        self._write_manifest()
        self._commit()

    # -- per-rollout assembly -----------------------------------------------------

    def _skeleton_record(self, b: _Batch, i: int) -> dict[str, Any]:
        return {
            "rollout_id": f"{self.meta.get('run_name')}/b{b.ordinal:04d}/r{i:02d}",
            "batch_ordinal": b.ordinal,
            "rollout_index": i,
            "global_step_before": b.global_step_before,
            "status": "assembly_error",
        }

    def _assemble(
        self,
        b: _Batch,
        i: int,
        call_assignment: dict[int, tuple[int, int]],
        advantages: list[Any] | None,
        eos: set[int],
        num_generations: int,
    ) -> dict[str, Any]:
        gen = b.gen
        assert gen is not None
        row = b.inputs[i] if i < len(b.inputs) else {}
        prompt_ids = gen["prompt_ids"][i]
        completion_ids = gen["completion_ids"][i]
        mask_raw = gen["tool_mask_raw"][i] if gen["tool_mask_raw"] else [1] * len(completion_ids)
        completions = gen["completions"][i]
        env = b.env_order[i] if i < len(b.env_order) else None
        runs = _runs(mask_raw)
        zero_runs = [(s, e) for s, e, v in runs if v == 0]
        one_runs = [(s, e) for s, e, v in runs if v == 1]
        bounds = [0] + [e for _, e in zero_runs]

        # Per-turn structure: the call that generated turn t received input
        # len(prompt_ids)+bounds[t] (bounds[t] = end of the preceding 0-run; bounds[0]=0
        # for the initial prompt). A rollout can end on a trailing 0-run when the last
        # generation was fully truncated to zero tokens: the call exists but no 1-run.
        turns: list[dict[str, Any]] = []
        for t in range(len(bounds)):
            gs, ge = one_runs[t] if t < len(one_runs) else (bounds[t], bounds[t])
            call_ref = call_assignment.get(t)
            call = b.calls[call_ref[0]] if call_ref is not None else None
            outs = (
                call["outputs"][call_ref[1]] if call is not None and call_ref is not None else None
            )
            # Each input slot yields a list of completions (n=1 in TRL's tool loop).
            out = outs[0] if outs else None
            turns.append(
                {
                    "turn": t,
                    "gen_span": [gs, ge],
                    "gen_tokens": ge - gs,
                    "call_index": call_ref[0] if call_ref else None,
                    "call_slot": call_ref[1] if call_ref else None,
                    "input_tokens": len(prompt_ids) + (bounds[t] if t < len(bounds) else gs),
                    "finish_reason": out.get("finish_reason") if out else None,
                    "stop_reason": out.get("stop_reason") if out else None,
                    "ambiguous_match": bool(
                        call is not None
                        and call_ref is not None
                        and call.get("ambiguous_slots", {}).get(str(call_ref[1]))
                    ),
                }
            )
        tool_blocks = [{"span": [s, e], "tokens": e - s} for s, e in zero_runs]

        last = completions[-1] if completions else {}
        last_pending = last.get("role") == "assistant" and bool(last.get("tool_calls"))

        # Environment section
        env_section: dict[str, Any] = {"env_present": env is not None}
        events = list(b.events.get(id(env), [])) if env is not None else []
        if env is not None:
            ep = getattr(env, "_episode", None)
            bundle = getattr(env, "_bundle", None)
            kept_rounds = len(zero_runs)

            # Align env events to model-visible tool messages. A call that reached
            # the env produces a tool message whose content is json.dumps(observation);
            # a call rejected before dispatch (unknown tool name, bad kwargs) produces
            # a Python-repr error dict and no env event. TRL rolls back a dropped
            # round's tool messages atomically, so rolled-back env events are always
            # the unmatched tail.
            tool_msgs = [m for m in completions if m.get("role") == "tool"]
            msg_round: list[int] = []  # round index per kept tool message
            pending = 0
            round_idx = -1
            for m in completions:
                if m.get("role") == "assistant" and m.get("tool_calls"):
                    round_idx += 1
                    pending = len(m["tool_calls"])
                elif m.get("role") == "tool" and pending:
                    msg_round.append(round_idx)
                    pending -= 1
            ptr = 0
            pre_dispatch_failures = 0
            for mi, m in enumerate(tool_msgs):
                obs = _env_observation(m.get("content"))
                if obs is None:
                    pre_dispatch_failures += 1
                    continue
                if ptr < len(events) and events[ptr]["observation"] == obs:
                    events[ptr]["round"] = msg_round[mi] if mi < len(msg_round) else None
                    ptr += 1
                else:
                    b.anomalies.append(
                        f"rollout {i}: tool message {mi} does not match env event {ptr}"
                    )
            rolled_events = events[ptr:]
            for ev in events[:ptr]:
                ev["rolled_back"] = False
            for ev in rolled_events:
                ev["rolled_back"] = True
                ev["round"] = kept_rounds  # the dropped round follows all kept rounds
            executed_rounds = (max((ev.get("round") or 0) for ev in events) + 1) if events else 0
            last_executed_rolled_back = bool(rolled_events)
            if last_executed_rolled_back and not last_pending:
                b.anomalies.append(f"rollout {i}: rolled-back env events but no pending tool calls")
            if pre_dispatch_failures and not events:
                pass  # model called nothing executable; transcript still records it
            env_section = {
                "env_present": True,
                "events": events,
                "kept_tool_rounds": kept_rounds,
                "executed_rounds": max(executed_rounds, kept_rounds),
                "pre_dispatch_failures": pre_dispatch_failures,
                "last_tool_calls_executed_but_rolled_back": last_executed_rolled_back,
            }
            if ep is not None:
                env_section.update(
                    {
                        "episode_id": ep.episode_id,
                        "done": ep.done,
                        "end_reason": ep.end_reason,
                        "step_count": ep.step_count,
                        "max_steps": ep.max_steps,
                        "action_log": [e.model_dump(mode="json") for e in ep.log],
                        "initial_state_hash": sha256_json(ep.initial_snapshot),
                        "final_snapshot": ep.snapshot(),
                    }
                )
            if bundle is not None:
                env_section["bundle_sha256"] = sha256_json(bundle.model_dump(mode="json"))
                env_section["private_task_id"] = bundle.private.task_id
                env_section["task"] = {
                    "family": bundle.private.family,
                    "variant": bundle.private.variant,
                    "split": bundle.private.split,
                    "world_id": bundle.private.world_id,
                }
            env_section["rollout_truncated_flag"] = bool(getattr(env, "_rollout_truncated", False))

        # Reward: what get_reward reported; diagnostic verifier for unscored rollouts.
        reward_rec = b.rewards.get(id(env), {}) if env is not None else {}
        verifier_record = reward_rec.get("verifier")
        reward = reward_rec.get("reward")
        verifier_role = "reward" if "reward" in reward_rec else None
        if verifier_record is None and env is not None:
            ep = getattr(env, "_episode", None)
            bundle = getattr(env, "_bundle", None)
            if ep is not None and bundle is not None:
                from invoiceops.verification.verifier import verify_episode

                try:
                    probe = verify_episode(ep, bundle.private)
                    verifier_record = probe.model_dump(mode="json")
                    verifier_role = "diagnostic_only"
                except Exception as exc:  # verifier should never throw, but record if it does
                    verifier_record = {"scorable": False, "error": f"verify raised: {exc!r}"}
                    verifier_role = "diagnostic_only"

        last_tok = completion_ids[-1] if completion_ids else None
        status = _status(
            env_section,
            last_pending,
            mask_raw,
            mask_final=gen["tool_mask_final"][i] if gen["tool_mask_final"] else mask_raw,
            last_tok=last_tok,
            eos=eos,
            truncated_flag=bool(env_section.get("rollout_truncated_flag")),
        )
        return {
            "rollout_id": f"{self.meta.get('run_name')}/b{b.ordinal:04d}/r{i:02d}",
            "run_name": self.meta.get("run_name"),
            "batch_ordinal": b.ordinal,
            "rollout_index": i,
            "group_index": i // max(1, num_generations),
            "in_group_index": i % max(1, num_generations),
            "global_step_before": b.global_step_before,
            "micro_step": b.micro_step,
            "epoch": b.epoch,
            "row_index": row.get("row_index"),
            "task_id": row.get("task_id"),
            "generated": row.get("generated"),
            "input": row,
            "prompt_messages": (gen["prompts"][i] if gen["prompts"] else None),
            "prompt_ids": prompt_ids,
            "completion_ids": completion_ids,
            "decoded_completion": (gen["decoded"][i] if gen["decoded"] else None),
            "tool_mask_raw": mask_raw,
            "tool_mask_final": gen["tool_mask_final"][i] if gen["tool_mask_final"] else mask_raw,
            "sampling_logprobs": (gen["logprobs"][i] if gen["logprobs"] else None),
            "messages": completions,
            "turns": turns,
            "tool_blocks": tool_blocks,
            "env": env_section,
            "reward": reward,
            "advantage": (
                advantages[i] if advantages is not None and i < len(advantages) else None
            ),
            "verifier": verifier_record,
            "verifier_role": verifier_role,
            "status": status,
            "completion_tokens": len(completion_ids),
            "model_generated_tokens": sum(mask_raw),
            "tool_result_tokens": len(mask_raw) - sum(mask_raw),
            "ended_on_eos": last_tok in eos if last_tok is not None else None,
            "tool_calls_pending_at_end": last_pending,
        }


def _status(
    env_section: dict[str, Any],
    last_pending: bool,
    mask_raw: list[int],
    *,
    mask_final: list[int],
    last_tok: int | None,
    eos: set[int],
    truncated_flag: bool,
) -> str:
    if not env_section.get("env_present"):
        return "no_environment"
    if env_section.get("done"):
        return f"terminal_{env_section.get('end_reason')}"
    if truncated_flag or not any(mask_final):
        if last_pending:
            if last_tok is not None and last_tok not in eos:
                return "cutoff_budget_tool_pending"
            return "cutoff_tool_pending"
        return "cutoff_unfinished"
    if last_tok is not None and last_tok not in eos and mask_raw:
        return "truncated_budget"
    if last_pending:
        return "unfinished_tool_pending"
    return "unfinished_other"


def _attribute_calls(
    calls: list[dict[str, Any]],
    prompt_ids: list[list[int]],
    completion_ids: list[list[int]],
    mask_raw: list[list[int]],
) -> tuple[dict[int, dict[int, tuple[int, int]]], list[str]]:
    """Match every raw call input to the (rollout, turn) whose prefix it equals.

    For rollout r, the call that generated turn t>0 received
    ``prompt_ids[r] + completion_ids[r][:end of the t-th 0-run]`` as input; turn 0
    received ``prompt_ids[r]``. Returns {rollout: {turn: (call_index, slot)}}.
    """
    n = len(prompt_ids)
    anomalies: list[str] = []
    key_index: dict[tuple[int, ...], list[tuple[int, int]]] = {}
    for r in range(n):
        stream = list(prompt_ids[r]) + list(completion_ids[r])
        plen = len(prompt_ids[r])
        bounds = [0] + _zero_run_ends(mask_raw[r])
        for turn, e in enumerate(bounds):
            key_index.setdefault(tuple(stream[: plen + e]), []).append((r, turn))

    matched: set[tuple[int, int]] = set()
    result: dict[int, dict[int, tuple[int, int]]] = {}
    for j, call in enumerate(calls):
        last_r = -1
        ambiguous: dict[str, int] = {}
        for s, inp in enumerate(call["inputs"]):
            key = tuple(inp)
            cands = [
                (r, t) for (r, t) in key_index.get(key, []) if (r, t) not in matched and r > last_r
            ]
            if not cands:
                anomalies.append(
                    f"model_call {j} slot {s}: input does not match any recorded rollout prefix"
                )
                continue
            if len(cands) > 1:
                ambiguous[str(s)] = len(cands)
            r, t = cands[0]
            matched.add((r, t))
            result.setdefault(r, {})[t] = (j, s)
            last_r = r
        if ambiguous:
            call["ambiguous_slots"] = ambiguous

    expected = 0
    for r in range(n):
        bounds = [0] + _zero_run_ends(mask_raw[r])
        expected += len(bounds)
        missing = [t for t in range(len(bounds)) if t not in result.get(r, {})]
        if missing:
            anomalies.append(f"rollout {r}: turns {missing} have no matching model call")
    if len(matched) != expected:
        anomalies.append(
            f"matched {len(matched)} call inputs but {expected} rollout-turn inputs expected"
        )
    return result, anomalies
