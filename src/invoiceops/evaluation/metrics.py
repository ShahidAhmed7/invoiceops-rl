"""Evaluation metrics, computed from saved episodes.

pass@k and pass^k are counted directly from the k attempts made per task (never inferred
from a per-attempt rate). Confidence intervals use a task-clustered bootstrap: tasks are
resampled with all their attempts, so repeated attempts on one task are not treated as
independent evidence.

Infrastructure errors remain outside the success denominator. pass@k/pass^k include only
tasks with all k scheduled attempts scored, and publish that denominator explicitly.
"""

from __future__ import annotations

import random
from collections import defaultdict
from collections.abc import Iterable
from typing import Any

from invoiceops.runs import EpisodeRecord
from invoiceops.tasks.model import PrivateTask

PAYABLE = "ready_for_payment"


def _ci(
    task_scores: list[float], seed: int = 0, samples: int = 2000
) -> tuple[float | None, float | None]:
    if not task_scores:
        return (None, None)
    rng = random.Random(seed)
    n = len(task_scores)
    means = sorted(sum(rng.choice(task_scores) for _ in range(n)) / n for _ in range(samples))
    return (means[int(0.025 * samples)], means[int(0.975 * samples) - 1])


def summarise(
    records: Iterable[EpisodeRecord],
    privates: dict[str, PrivateTask],
    expected_attempts: int | None = None,
) -> dict[str, Any]:
    if expected_attempts is not None and expected_attempts < 1:
        raise ValueError("expected_attempts must be positive")
    by_task: dict[str, list[EpisodeRecord]] = {task_id: [] for task_id in privates}
    seen: set[tuple[str, int]] = set()
    for record in records:
        if record.task_id not in by_task:
            raise ValueError(f"unexpected task {record.task_id}")
        if record.attempt < 0 or (
            expected_attempts is not None and record.attempt >= expected_attempts
        ):
            raise ValueError(f"unexpected attempt {record.attempt} for {record.task_id}")
        key = (record.task_id, record.attempt)
        if key in seen:
            raise ValueError(f"duplicate task/attempt: {key}")
        seen.add(key)
        by_task[record.task_id].append(record)
    scored = [r for rs in by_task.values() for r in rs if r.verifier and r.verifier.scorable]
    unscorable = [
        r for rs in by_task.values() for r in rs if not (r.verifier and r.verifier.scorable)
    ]
    k = expected_attempts or max((attempt + 1 for _, attempt in seen), default=0)

    task_rates: list[float] = []
    pass_at_k = pass_hat_k = repeat_tasks = 0
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
        # A run with missing/unscorable attempts is not an observed k-attempt experiment.
        # Do not compress away infrastructure errors and label fewer attempts as pass@k.
        if k and {r.attempt for r in rs} == set(range(k)) and len(outcomes) == k:
            repeat_tasks += 1
            pass_at_k += any(outcomes)
            pass_hat_k += all(outcomes)

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
        invoice_id = privates[r.task_id].expectation.invoice_id
        case = next(c for c in r.final_snapshot["cases"] if c["invoice_id"] == invoice_id)
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
    timing: dict[str, Any] = {}
    if any(r.usage.get("requests") for r in scored):  # wall-clock only for model runs
        timing["mean_seconds"] = sum(r.seconds for r in scored) / n_scored
    return {
        **timing,
        "tasks": len(by_task),
        "attempts_per_task": k,
        "scheduled_attempts": len(by_task) * k,
        "recorded_attempts": len(seen),
        "missing_attempts": len(by_task) * k - len(seen),
        "scored_tasks": len(task_rates),
        "repeat_metric_tasks": repeat_tasks,
        "incomplete_repeat_metric_tasks": len(by_task) - repeat_tasks,
        "scored_attempts": n_scored,
        "unscorable_attempts": len(unscorable),
        "strict_success": (sum(bool(r.verifier and r.verifier.passed) for r in scored) / n_scored)
        if n_scored
        else None,
        "task_mean_success": sum(task_rates) / len(task_rates) if task_rates else None,
        "task_mean_success_ci95": [lo, hi],
        f"pass@{k}": pass_at_k / repeat_tasks if repeat_tasks else None,
        f"pass^{k}": pass_hat_k / repeat_tasks if repeat_tasks else None,
        "critical_violations": dict(sorted(critical.items())),
        "attempts_with_critical_violation": sum(
            1 for r in scored if r.verifier and r.verifier.critical_violations
        ),
        "false_completions": sum(1 for r in scored if r.verifier and r.verifier.false_completion),
        "blocked_attempts": sum(
            1
            for r in scored
            if any(e.result_code in ("forbidden", "invalid_arguments") for e in r.log)
        ),
        "blocked_tool_calls": sum(
            1 for r in scored for e in r.log if e.result_code in ("forbidden", "invalid_arguments")
        ),
        "tool_call_limit_stops": sum(
            1 for r in scored if r.usage.get("stopped") == "tool_call_limit"
        ),
        "exception_cases_not_paid": f"{exc_ok}/{exc_total}",
        "clean_cases_paid_correctly": f"{clean_ok}/{clean_total}",
        "mean_tool_calls": sum(r.steps for r in scored) / n_scored if n_scored else None,
        "tokens": {
            "prompt": sum(int(r.usage.get("prompt_tokens", 0)) for r in scored),
            "completion": sum(int(r.usage.get("completion_tokens", 0)) for r in scored),
            "max_context": max(
                (int(r.usage.get("max_context_tokens", 0)) for r in scored), default=0
            ),
            "truncated_turns": sum(int(r.usage.get("truncated_turns", 0)) for r in scored),
            "context_limit_stops": sum(
                1 for r in scored if r.usage.get("stopped") == "context_limit"
            ),
        },
        "by_family": {f: sum(v) / len(v) for f, v in sorted(family.items())},
        "infrastructure_errors": [
            r.infrastructure_error for r in unscorable if r.infrastructure_error
        ],
        "verifier_errors": [
            r.verifier.error for r in unscorable if r.verifier and r.verifier.error
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
        f"| Unscorable attempts (infrastructure or verifier) | {summary['unscorable_attempts']} |",
        f"| Missing attempts | {summary.get('missing_attempts', 0)} |",
        f"| Tasks with all {k} attempts scored (pass metrics denominator) | "
        f"{summary.get('repeat_metric_tasks', summary['tasks'])}/{summary['tasks']} |",
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
