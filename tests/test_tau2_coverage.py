from __future__ import annotations

import pytest
from modal_app.tau2_driver import validate_summary


def test_tau2_requires_complete_reward_and_task_coverage() -> None:
    summary = {
        "tasks": 2,
        "trials": 4,
        "simulations": 8,
        "simulations_without_reward": 0,
        "complete_tasks": 2,
        "unexpected_task_ids": [],
        "per_task_mean_reward": {"a": 0.25, "b": 1.0},
    }
    validate_summary(summary)
    for change in (
        {"simulations": 7},
        {"simulations_without_reward": 1},
        {"complete_tasks": 1},
        {"unexpected_task_ids": ["c"]},
        {"per_task_mean_reward": {"a": float("nan"), "b": 1.0}},
    ):
        with pytest.raises(ValueError, match="every scheduled"):
            validate_summary({**summary, **change})
