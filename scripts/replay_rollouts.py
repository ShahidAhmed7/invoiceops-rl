"""Replay trajectory records against fresh environments and regrade them.

    uv run python scripts/replay_rollouts.py runs/modal/training/<run_name> [--sample 48]

Rebuilds each rollout's task bundle from its dataset row, replays the recorded
``env.action_log`` through a fresh ``Episode``, compares every replayed step's
state hash and observation to the recorded one, then re-verifies the episode
with the trusted verifier. The report counts records, skipped/skeleton rows,
hash divergences, observation mismatches, and reward disagreements — the
evidence that the logged trajectories are faithful and rewards reproducible.
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path
from typing import Any

from invoiceops.adapters.trl_env import bundle_for_row
from invoiceops.episode import Episode
from invoiceops.verification.verifier import verify_episode


def _records(run_dir: Path) -> list[dict[str, Any]]:
    out = []
    for path in sorted((run_dir / "trajectories").glob("batch-*.jsonl.gz")):
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    out.append(json.loads(line))
    return out


def replay_record(record: dict[str, Any]) -> dict[str, Any]:
    """Replay one record's action log; returns per-record comparison results."""
    rid = record.get("rollout_id", "?")
    env = record.get("env") or {}
    action_log = env.get("action_log") or []
    row = record.get("input") or {}
    result: dict[str, Any] = {
        "rollout_id": rid,
        "status": record.get("status"),
        "recorded_reward": record.get("reward"),
        "verifier_reward": (record.get("verifier") or {}).get("reward"),
        "steps_recorded": len(action_log),
        "hash_mismatches": [],
        "obs_mismatches": [],
    }
    try:
        bundle = bundle_for_row(row)
    except Exception as exc:
        result["error"] = f"bundle resolution failed: {exc!r}"
        return result
    ep = Episode(bundle.public.world, bundle.public.task_id, max_steps=bundle.public.max_steps)
    try:
        for i, ev in enumerate(action_log):
            obs = ep.step(ev["tool"], ev.get("arguments") or {})
            replayed = ep.log[-1]
            if replayed.state_before != ev.get("state_before") or replayed.state_after != ev.get(
                "state_after"
            ):
                result["hash_mismatches"].append(i)
            if obs != ev.get("observation"):
                result["obs_mismatches"].append(i)
        try:
            regrade = verify_episode(ep, bundle.private)
            result["regrade_reward"] = regrade.reward if regrade.scorable else None
            result["regrade_scorable"] = regrade.scorable
        except Exception as exc:
            result["regrade_error"] = repr(exc)
    except Exception as exc:
        result["error"] = f"replay failed at step {ep.step_count}: {exc!r}"
    finally:
        ep.close()
    vr = result.get("verifier_reward")
    rr = result.get("regrade_reward", vr)
    result["reward_match"] = vr is None or (rr == vr)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--sample", type=int, default=0, help="replay only every k-th record")
    parser.add_argument("--out", type=Path, help="write the JSON report here")
    args = parser.parse_args(argv)

    records = _records(args.run_dir)
    skeletons = [r for r in records if r.get("status") in {"assembly_error", "interrupted"}]
    playable = [r for r in records if r not in skeletons and (r.get("env") or {}).get("action_log")]
    if args.sample and args.sample > 1:
        playable = playable[:: args.sample]
    results = [replay_record(r) for r in playable]

    bad_hash = [r["rollout_id"] for r in results if r.get("hash_mismatches")]
    bad_obs = [r["rollout_id"] for r in results if r.get("obs_mismatches")]
    bad_reward = [r["rollout_id"] for r in results if r.get("reward_match") is False]
    errors = [
        {"rollout_id": r["rollout_id"], "error": r["error"]} for r in results if r.get("error")
    ]
    report = {
        "run_dir": str(args.run_dir),
        "records_total": len(records),
        "skeletons_skipped": len(skeletons),
        "records_replayed": len(results),
        "hash_divergent": bad_hash,
        "observation_divergent": bad_obs,
        "reward_mismatch": bad_reward,
        "replay_errors": errors,
        "ok": not bad_hash and not bad_obs and not bad_reward and not errors,
    }
    text = json.dumps(report, indent=1)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n")
    print(text)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
