from __future__ import annotations

import json
from pathlib import Path

import pytest

from invoiceops.agents.oracle import solve
from invoiceops.episode import Episode
from invoiceops.evaluation.metrics import summarise, to_markdown
from invoiceops.evaluation.run import evaluate
from invoiceops.runs import EpisodeRecord, record_episode
from invoiceops.tasks.model import TaskBundle
from invoiceops.verification.verifier import verify_episode

from .conftest import by_family


def _record(bundle: TaskBundle, attempt: int, passed: bool) -> EpisodeRecord:
    ep = Episode(bundle.public.world, bundle.public.task_id)
    try:
        if passed:
            solve(ep)
        return record_episode(
            ep, "metrics-test", "oracle", attempt, verify_episode(ep, bundle.private)
        )
    finally:
        ep.close()


def test_success_and_reliability_match_hand_calculated_outcomes() -> None:
    a, b = by_family("F01", 0), by_family("F02", 0)
    records = [_record(a, 0, True), _record(a, 1, False), _record(b, 0, True), _record(b, 1, True)]
    privates = {x.public.task_id: x.private for x in (a, b)}
    result = summarise(records, privates, expected_attempts=2)
    assert result["strict_success"] == result["task_mean_success"] == 0.75
    assert result["pass@2"] == 1.0
    assert result["pass^2"] == 0.5  # directly observed; not 0.75 squared
    assert result["task_mean_success_ci95"] == [0.5, 1.0]
    assert result["repeat_metric_tasks"] == 2
    assert result == summarise(reversed(records), privates, expected_attempts=2)


def test_unscorable_attempt_does_not_turn_one_success_into_pass_at_two() -> None:
    bundle = by_family("F01", 0)
    passed = _record(bundle, 0, True)
    unavailable = passed.model_copy(
        update={"attempt": 1, "verifier": None, "infrastructure_error": "endpoint unavailable"}
    )
    result = summarise([passed, unavailable], {bundle.public.task_id: bundle.private}, 2)
    assert result["strict_success"] == 1.0  # explicitly conditional on scorable attempts
    assert result["scored_attempts"] == result["unscorable_attempts"] == 1
    assert result["pass@2"] is None and result["pass^2"] is None
    assert result["repeat_metric_tasks"] == 0
    assert result["incomplete_repeat_metric_tasks"] == 1


def test_task_mean_does_not_overweight_tasks_with_more_scored_attempts() -> None:
    a, b = by_family("F01", 0), by_family("F02", 0)
    records = [_record(a, 0, True), _record(a, 1, True), _record(b, 0, False)]
    privates = {x.public.task_id: x.private for x in (a, b)}
    result = summarise(records, privates, 2)
    assert result["strict_success"] == pytest.approx(2 / 3)
    assert result["task_mean_success"] == 0.5
    assert result["scheduled_attempts"] == 4 and result["missing_attempts"] == 1
    assert result["repeat_metric_tasks"] == 1


def test_entirely_missing_task_is_visible_in_coverage() -> None:
    a, b = by_family("F01", 0), by_family("F02", 0)
    result = summarise([_record(a, 0, True)], {x.public.task_id: x.private for x in (a, b)}, 1)
    assert result["tasks"] == 2 and result["scored_tasks"] == 1
    assert result["missing_attempts"] == result["incomplete_repeat_metric_tasks"] == 1


def test_blocked_attempts_counts_episodes_not_calls() -> None:
    bundle = by_family("F01", 0)
    ep = Episode(bundle.public.world, bundle.public.task_id)
    try:
        for _ in range(3):
            ep.step("get_invoice", {})
        record = record_episode(ep, "blocked", "test", verifier=verify_episode(ep, bundle.private))
        result = summarise([record], {bundle.public.task_id: bundle.private}, 1)
        assert result["blocked_attempts"] == 1
        assert result["blocked_tool_calls"] == 3
    finally:
        ep.close()


def test_no_scorable_attempts_produce_valid_json_and_na_intervals() -> None:
    bundle = by_family("F01", 0)
    record = _record(bundle, 0, False)
    assert record.verifier is not None
    record = record.model_copy(
        update={
            "verifier": record.verifier.model_copy(
                update={"scorable": False, "reward": None, "error": "test verifier failure"}
            )
        }
    )
    result = summarise([record], {bundle.public.task_id: bundle.private}, 1)
    assert result["task_mean_success_ci95"] == [None, None]
    assert result["verifier_errors"] == ["test verifier failure"]
    json.dumps(result, allow_nan=False)
    markdown = to_markdown("No scores", {}, result)
    assert "nan%" not in markdown and "n/a" in markdown


def test_duplicate_attempts_are_rejected() -> None:
    bundle = by_family("F01", 0)
    record = _record(bundle, 0, True)
    with pytest.raises(ValueError, match="duplicate"):
        summarise([record, record], {bundle.public.task_id: bundle.private}, 1)


@pytest.mark.parametrize("attempts", [0, -1])
def test_evaluation_rejects_invalid_trial_counts(tmp_path: Path, attempts: int) -> None:
    with pytest.raises(ValueError, match="attempts"):
        evaluate("oracle", [by_family("F01", 0).public.task_id], tmp_path, attempts=attempts)


def test_evaluation_rejects_duplicate_tasks(tmp_path: Path) -> None:
    task_id = by_family("F01", 0).public.task_id
    with pytest.raises(ValueError, match="unique"):
        evaluate("oracle", [task_id, task_id], tmp_path)
