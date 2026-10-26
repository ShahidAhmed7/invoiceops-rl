"""Recompute available saved runs and check committed summary arithmetic; no model calls."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from invoiceops.episode import Episode
from invoiceops.evaluation.metrics import summarise
from invoiceops.runs import load_episodes
from invoiceops.tasks.store import load_bundle
from invoiceops.verification.verifier import verify

ROOT = Path(__file__).resolve().parents[1]


def _close(a: Any, b: Any) -> bool:
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(_close(x, y) for x, y in zip(a, b, strict=True))
    if a is None or b is None:
        return a is b
    return math.isclose(a, b, abs_tol=1e-12)


def main() -> None:
    raw_runs = []
    for episodes in sorted((ROOT / "runs").rglob("episodes")):
        folder = episodes.parent
        if not (folder / "summary.json").exists():
            continue
        records = load_episodes(folder)
        old = json.loads((folder / "summary.json").read_text())
        bundles = {r.task_id: load_bundle(r.task_id) for r in records}
        assert len(bundles) == old["tasks"], folder
        new = summarise(
            records, {t: b.private for t, b in bundles.items()}, old["attempts_per_task"]
        )
        keys = ["strict_success", "task_mean_success", "task_mean_success_ci95"]
        keys += [f"pass@{old['attempts_per_task']}", f"pass^{old['attempts_per_task']}"]
        changes = {k: [old[k], new[k]] for k in keys if not _close(old[k], new[k])}
        regraded = legacy = 0
        verifier_differences = []
        for record in records:
            if record.verifier is None or not record.verifier.scorable:
                continue
            # The pre-review suite used a different clarification schema and verifier.
            # Its stored outcomes can be recounted, but not regraded as current-suite results.
            if record.created_at < "2026-10-23T00:00:00Z":
                legacy += 1
                continue
            bundle = bundles[record.task_id]
            episode = Episode(bundle.public.world, record.task_id)
            try:
                verdict = verify(
                    bundle.public.world,
                    bundle.private,
                    episode.initial_snapshot,
                    record.final_snapshot,
                )
                assert verdict.scorable, (folder, record.task_id, verdict.error)
                if (
                    verdict.passed != record.verifier.passed
                    or verdict.critical_violations != record.verifier.critical_violations
                ):
                    verifier_differences.append(
                        {
                            "task": record.task_id,
                            "attempt": record.attempt,
                            "passed_before": record.verifier.passed,
                            "passed_current": verdict.passed,
                            "critical_before": record.verifier.critical_violations,
                            "critical_current": verdict.critical_violations,
                        }
                    )
                regraded += 1
            finally:
                episode.close()
        assert not changes, (folder, changes)
        raw_runs.append(
            {
                "run": str(folder.relative_to(ROOT)),
                "records": len(records),
                "current_snapshots_regraded": regraded,
                "pre_review_snapshots_not_regraded": legacy,
                "stored_verifier_differences": verifier_differences,
                "headline_changes": changes,
                "blocked_attempts_before": old["blocked_attempts"],
                "blocked_attempts_after": new["blocked_attempts"],
            }
        )

    summaries = []

    def inspect(value: Any, location: str) -> None:
        if isinstance(value, dict):
            if {"task_mean_success", "attempts_per_task", "scored_attempts"} <= value.keys():
                n, k = value["tasks"], value["attempts_per_task"]
                if value["unscorable_attempts"] == 0 and value["scored_attempts"] == n * k:
                    mean = value["task_mean_success"]
                    assert _close(mean, value["strict_success"]), location
                    assert _close(mean * n * k, round(mean * n * k)), location
                    assert value[f"pass^{k}"] <= mean + 1e-12 <= value[f"pass@{k}"] + 1e-12
                    lo, hi = value["task_mean_success_ci95"]
                    assert 0 <= lo <= mean <= hi <= 1
                    summaries.append(location)
            for key, item in value.items():
                inspect(item, f"{location}/{key}")
        elif isinstance(value, list):
            for index, item in enumerate(value):
                inspect(item, f"{location}/{index}")

    for file in sorted((ROOT / "reports/modal").glob("*.json")):
        inspect(json.loads(file.read_text()), str(file.relative_to(ROOT)))

    tau = []
    for name in ("tau2_before", "tau2_reference"):
        data = json.loads((ROOT / f"reports/modal/{name}.json").read_text())
        means = list(data["per_task_mean_reward"].values())
        assert len(means) == data["tasks"]
        assert data["simulations"] == data["tasks"] * data["trials"]
        assert not data["simulations_without_reward"]
        assert _close(sum(means) / len(means), data["pass_1"])
        assert _close(sum(m == 1 for m in means) / len(means), data[f"pass^{data['trials']}"])
        tau.append(name)

    result = {
        "date": "2026-10-26",
        "raw_runs": raw_runs,
        "raw_records_recomputed": sum(r["records"] for r in raw_runs),
        "current_snapshots_regraded": sum(r["current_snapshots_regraded"] for r in raw_runs),
        "pre_review_snapshots_not_regraded": sum(
            r["pre_review_snapshots_not_regraded"] for r in raw_runs
        ),
        "raw_headline_changes": 0,
        "current_verifier_pass_changes": sum(
            d["passed_before"] != d["passed_current"]
            for r in raw_runs
            for d in r["stored_verifier_differences"]
        ),
        "current_verifier_critical_label_changes": sum(
            d["critical_before"] != d["critical_current"]
            for r in raw_runs
            for d in r["stored_verifier_differences"]
        ),
        "committed_complete_summary_arithmetic_checks": summaries,
        "tau2_summary_arithmetic_checks": tau,
        "no_model_calls_or_gpu_jobs": True,
        "limitations": [
            "Only local episode records were recomputed; other runs were checked from summaries.",
            "Bootstrap intervals resample tasks, not companies; test contains only four companies.",
            "The test split has already been inspected in prior prompt work.",
        ],
    }
    (ROOT / "reports/evaluation_audit_checks.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k not in ("raw_runs",)}, indent=2))


if __name__ == "__main__":
    main()
