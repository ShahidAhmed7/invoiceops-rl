"""Evaluation metrics, computed from saved episodes.

pass@k and pass^k are counted directly from the k attempts made per task (never inferred
from a per-attempt rate). Confidence intervals use a task-clustered bootstrap: tasks are
resampled with all their attempts, so repeated attempts on one task are not treated as
independent evidence.
"""

from __future__ import annotations

import random
from collections import defaultdict
from collections.abc import Iterable
from typing import Any

from invoiceops.runs import EpisodeRecord
from invoiceops.tasks.model import PrivateTask

PAYABLE = "ready_for_payment"


def _ci(task_scores: list[float], seed: int = 0, samples: int = 2000) -> tuple[float, float]:
    if not task_scores:
        return (float("nan"), float("nan"))
    rng = random.Random(seed)
    n = len(task_scores)
    means = sorted(sum(rng.choice(task_scores) for _ in range(n)) / n for _ in range(samples))
    return (means[int(0.025 * samples)], means[int(0.975 * samples) - 1])


def summarise(records: Iterable[EpisodeRecord], privates: dict[str, PrivateTask]) -> dict[str, Any]:
    by_task: dict[str, list[EpisodeRecord]] = defaultdict(list)
    for record in records:
        by_task[record.task_id].append(record)
    scored = [r for rs in by_task.values() for r in rs if r.verifier and r.verifier.scorable]
    unscorable = [
        r for rs in by_task.values() for r in rs if not (r.verifier and r.verifier.scorable)
    ]
    k = min((len(rs) for rs in by_task.values()), default=0)

    task_rates: list[float] = []
    pass_at_k = pass_hat_k = 0
    family: dict[str, list[float]] = defaultdict(list)
    for task_id, rs in sorted(by_task.items()):
        outcomes = [
            bool(r.verifier and r.verifier.passed) for r in rs if r.verifier and r.verifier.scorable
        ]
        if not outcomes:
            continue
        rate = sum(outcomes) / len(outcomes)
        task_rates.append(rate)
        family[privates[task_id].family].append(rate)
        first_k = outcomes[:k]
        pass_at_k += any(first_k)
        pass_hat_k += all(first_k) and len(first_k) == k

    critical: dict[str, int] = defaultdict(int)
    for r in scored:
        assert r.verifier is not None
        for name in r.verifier.critical_violations:
            critical[name] += 1

    # Appropriateness: exception tasks must not be paid; clean tasks must be paid correctly.
    exc_total = exc_ok = clean_total = clean_ok = 0
    for r in scored:
        assert r.verifier is not None
        expect_pay = privates[r.task_id].expectation.outcomes[0].status.value == PAYABLE
        case = next(c for c in r.final_snapshot["cases"])
        if expect_pay:
            clean_total += 1
            clean_ok += r.verifier.passed
        else:
            exc_total += 1
            exc_ok += case["status"] != PAYABLE and not any(
                p["invoice_id"] == case["invoice_id"] for p in r.final_snapshot["proposals"]
            )

    n_scored = len(scored)
    lo, hi = _ci(task_rates)
    return {
        "tasks": len(by_task),
        "attempts_per_task": k,
        "scored_attempts": n_scored,
        "unscorable_attempts": len(unscorable),
        "strict_success": (sum(bool(r.verifier and r.verifier.passed) for r in scored) / n_scored)
        if n_scored
        else None,
        "task_mean_success": sum(task_rates) / len(task_rates) if task_rates else None,
        "task_mean_success_ci95": [lo, hi],
        f"pass@{k}": pass_at_k / len(task_rates) if task_rates else None,
        f"pass^{k}": pass_hat_k / len(task_rates) if task_rates else None,
        "critical_violations": dict(sorted(critical.items())),
        "attempts_with_critical_violation": sum(
            1 for r in scored if r.verifier and r.verifier.critical_violations
        ),
        "false_completions": sum(1 for r in scored if r.verifier and r.verifier.false_completion),
        "blocked_attempts": sum(
            1 for r in scored for e in r.log if e.result_code in ("forbidden", "invalid_arguments")
        ),
        "exception_cases_not_paid": f"{exc_ok}/{exc_total}",
        "clean_cases_paid_correctly": f"{clean_ok}/{clean_total}",
        "mean_tool_calls": sum(r.steps for r in scored) / n_scored if n_scored else None,
        "mean_seconds": sum(r.seconds for r in scored) / n_scored if n_scored else None,
        "tokens": {
            "prompt": sum(int(r.usage.get("prompt_tokens", 0)) for r in scored),
            "completion": sum(int(r.usage.get("completion_tokens", 0)) for r in scored),
        },
        "by_family": {f: sum(v) / len(v) for f, v in sorted(family.items())},
        "infrastructure_errors": [
            r.infrastructure_error for r in unscorable if r.infrastructure_error
        ],
    }


def to_markdown(title: str, config: dict[str, Any], summary: dict[str, Any]) -> str:
    k = summary["attempts_per_task"]

    def pct(value: Any) -> str:
        return "n/a" if value is None else f"{100 * value:.1f}%"

    lo, hi = summary["task_mean_success_ci95"]
    lines = [
        f"# {title}",
        "",
        "## Configuration",
        "",
        *(f"- **{key}:** `{value}`" for key, value in sorted(config.items())),
        "",
        "## Results",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Tasks x attempts | {summary['tasks']} x {k} |",
        f"| Strict success (all scored attempts) | {pct(summary['strict_success'])} |",
        f"| Task-mean success (95% task-bootstrap CI) | {pct(summary['task_mean_success'])} "
        f"({pct(lo)} to {pct(hi)}) |",
        f"| pass@{k} | {pct(summary.get(f'pass@{k}'))} |",
        f"| pass^{k} | {pct(summary.get(f'pass^{k}'))} |",
        f"| Attempts with a critical violation | {summary['attempts_with_critical_violation']} |",
        f"| False completions | {summary['false_completions']} |",
        f"| Exception cases not paid | {summary['exception_cases_not_paid']} |",
        f"| Clean cases paid correctly | {summary['clean_cases_paid_correctly']} |",
        f"| Unscorable attempts (infrastructure) | {summary['unscorable_attempts']} |",
        f"| Mean tool calls per attempt | {summary['mean_tool_calls']:.1f} |"
        if summary["mean_tool_calls"] is not None
        else "| Mean tool calls per attempt | n/a |",
        "",
        "## Success by family",
        "",
        "| Family | Task-mean success |",
        "|---|---|",
        *(f"| {f} | {pct(v)} |" for f, v in summary["by_family"].items()),
        "",
    ]
    if summary["critical_violations"]:
        lines += ["## Critical violations", "", "| Violation | Attempts |", "|---|---|"]
        lines += [f"| {k_} | {v} |" for k_, v in summary["critical_violations"].items()]
        lines.append("")
    return "\n".join(lines)
