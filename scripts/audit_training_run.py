"""Audit a mirrored GRPO run directory for logging completeness and integrity.

    uv run python scripts/audit_training_run.py runs/modal/training/<run_name> [--out FILE]

Checks, without any GPU or network access:
* every manifest-listed file exists locally and its sha256 matches;
* every batch shard's record count matches its manifest entry, and totals match
  ``manifest.counters``;
* per-rollout identity: unique rollout_ids, row_index present, groups of
  ``num_generations`` share one row_index, reward/verifier/mask fields present;
* raw model-call coverage: the calls shard count matches the manifest, and
  re-running prefix attribution over the recorded call inputs finds no
  unmatched rollout-turns beyond those already flagged;
* mask accounting: tool_mask_raw sums equal model+tool token splits;
* ledger: allocation-scoped spend entries for this run.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from modal_app.budget import LEDGER, read_ledger
from modal_app.sync_run import verify_manifest

from invoiceops.adapters.rollout_log import _attribute_calls

REQUIRED_KEYS = {
    "rollout_id",
    "batch_ordinal",
    "rollout_index",
    "row_index",
    "prompt_ids",
    "completion_ids",
    "tool_mask_raw",
    "tool_mask_final",
    "messages",
    "turns",
    "env",
    "status",
}


def _read_gz(path: Path) -> list[dict[str, Any]]:
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def audit(run_dir: Path) -> dict[str, Any]:
    report: dict[str, Any] = {"run_dir": str(run_dir), "checks": {}, "issues": []}
    issues: list[str] = report["issues"]  # type: ignore[assignment]

    manifest_path = run_dir / "manifest.json"
    if not manifest_path.exists():
        report["issues"].append("manifest.json missing locally")
        report["ok"] = False
        return report
    manifest = json.loads(manifest_path.read_text())
    report["manifest_status"] = manifest.get("status")
    report["manifest_counters"] = manifest.get("counters")

    # 1. Manifest file integrity (sha256 + presence), both directions.
    #    Trajectory/model_call/dataset shards are immutable once registered, so a
    #    mismatch is always a hard issue. Aux files (meta.json, checkpoint side
    #    files, TRL completion dumps) may be rewritten by a later attempt while
    #    the run is live -> downgrade those to notes until the run closes.
    verify = verify_manifest(run_dir)
    report["checks"]["manifest_verify"] = verify
    shard_dirs = ("trajectories/", "model_calls/", "dataset/")
    running = manifest.get("status") == "running"
    hard_missing = [m for m in verify.get("missing", [])]
    hard_mismatch = [m for m in verify.get("mismatched", []) if m.startswith(shard_dirs)]
    soft_mismatch = [m for m in verify.get("mismatched", []) if m not in hard_mismatch]
    if hard_missing or hard_mismatch:
        issues.append(f"manifest files missing={hard_missing} mismatched={hard_mismatch}")
    if running and soft_mismatch:
        report.setdefault("notes", []).append(
            f"aux files rewritten after registration (expected while running): {soft_mismatch}"
        )
    elif soft_mismatch:
        issues.append(f"aux files mismatched after close: {soft_mismatch}")
    remote_listed = set((manifest.get("files") or {}).keys())
    local_extra = []
    for path in sorted(run_dir.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(run_dir).as_posix()
        if rel in {".sync_state.json", "sync_verify.json", "replay_report.json"}:
            continue
        if rel not in remote_listed and rel != "manifest.json":
            local_extra.append(rel)
    report["checks"]["local_files_not_in_manifest"] = local_extra
    if local_extra and not running:
        issues.append(f"local files never registered in manifest: {local_extra[:10]}")

    # 2. Per-batch shards: counts, identities, re-attribution.
    rollouts_total = 0
    calls_total = 0
    status_counts: Counter[str] = Counter()
    task_counts: Counter[str] = Counter()
    rewards: Counter[str] = Counter()
    rollout_ids: set[str] = set()
    row_indexes: set[int] = set()
    group_violations: list[str] = []
    missing_keys: list[str] = []
    mask_token_mismatch: list[str] = []
    skeleton_rollouts: list[str] = []

    for batch in manifest.get("batches", []):
        ordinal = batch["ordinal"]
        traj_rel = batch.get("trajectories")
        calls_rel = batch.get("model_calls_shard")
        if not traj_rel:
            issues.append(f"batch {ordinal}: no trajectories shard in manifest")
            continue
        recs = _read_gz(run_dir / traj_rel)
        calls = _read_gz(run_dir / calls_rel) if calls_rel else []
        rollouts_total += len(recs)
        calls_total += len(calls)
        if len(recs) != batch.get("rollouts"):
            issues.append(f"batch {ordinal}: {len(recs)} records != {batch.get('rollouts')}")
        if len(calls) != batch.get("model_calls"):
            issues.append(f"batch {ordinal}: {len(calls)} calls != {batch.get('model_calls')}")

        # Group integrity: consecutive groups of 8 share one row_index.
        for g in range(0, len(recs), 8):
            idxs = {recs[i].get("row_index") for i in range(g, min(g + 8, len(recs)))}
            if len(idxs) > 1:
                group_violations.append(f"batch {ordinal} group {g // 8}: rows {idxs}")

        for rec in recs:
            rid = rec.get("rollout_id", "?")
            rollout_ids.add(rid)
            status_counts[rec.get("status", "?")] += 1
            rewards[str(rec.get("reward"))] += 1
            task_counts[str(rec.get("task_id"))] += 1
            if isinstance(rec.get("row_index"), int):
                row_indexes.add(rec["row_index"])
            missing = REQUIRED_KEYS - set(rec)
            if missing:
                missing_keys.append(f"{rid}: {sorted(missing)}")
            mask = rec.get("tool_mask_raw") or []
            if mask and isinstance(mask, list):
                model_t = sum(mask)
                total_t = len(mask)
                if model_t != rec.get("model_generated_tokens") or total_t - model_t != rec.get(
                    "tool_result_tokens"
                ):
                    mask_token_mismatch.append(rid)
            if rec.get("status") in {"assembly_error", "interrupted"}:
                skeleton_rollouts.append(rid)

        # Re-attribute calls per batch (only for non-interrupted batches with a full gen).
        if (
            calls
            and recs
            and all(r.get("prompt_ids") and r.get("completion_ids") is not None for r in recs)
        ):
            try:
                _map, attr_issues = _attribute_calls(
                    calls,
                    [r["prompt_ids"] for r in recs],
                    [r["completion_ids"] for r in recs],
                    [r["tool_mask_raw"] or [] for r in recs],
                )
                unexpected = [a for a in attr_issues if a not in (batch.get("anomalies") or [])]
                if unexpected:
                    issues.append(f"batch {ordinal} re-attribution: {unexpected[:3]}")
            except Exception as exc:
                issues.append(f"batch {ordinal} re-attribution crashed: {exc!r}")

    report["checks"]["rollouts"] = rollouts_total
    report["checks"]["model_calls"] = calls_total
    counters = manifest.get("counters") or {}
    if counters.get("rollouts") not in (None, rollouts_total):
        issues.append(
            f"manifest counters.rollouts={counters['rollouts']} != {rollouts_total} records"
        )
    if counters.get("model_calls") not in (None, calls_total):
        issues.append(
            f"manifest counters.model_calls={counters['model_calls']} != {calls_total} calls"
        )
    report["checks"]["status_counts"] = dict(status_counts)
    report["checks"]["reward_distribution"] = dict(rewards)
    report["checks"]["unique_row_indexes"] = len(row_indexes)
    report["checks"]["unique_rollout_ids"] = len(rollout_ids)
    report["checks"]["group_violations"] = group_violations
    report["checks"]["missing_required_keys"] = missing_keys[:20]
    report["checks"]["mask_token_mismatches"] = mask_token_mismatch[:20]
    report["checks"]["skeleton_rollouts"] = skeleton_rollouts
    if len(rollout_ids) != rollouts_total:
        issues.append("duplicate rollout_ids across shards")
    report["checks"]["task_distribution"] = dict(task_counts.most_common(20))

    # 3. Ledger: campaign spend (all grpo_training entries) and this run's entries.
    ledger = read_ledger(LEDGER)
    campaign = [e for e in ledger if e.get("allocation") == "grpo_training"]
    run_name = manifest.get("run_name")
    run_entries = [e for e in campaign if e.get("run_name") == run_name]
    report["checks"]["campaign_ledger_entries"] = campaign
    report["checks"]["this_run_ledger_entries"] = run_entries
    report["checks"]["campaign_spend_usd"] = round(
        sum(float(e.get("cost_usd", 0.0)) for e in campaign), 4
    )

    report["ok"] = not issues
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    report = audit(args.run_dir)
    text = json.dumps(report, indent=1, default=str)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n")
    print(text)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
