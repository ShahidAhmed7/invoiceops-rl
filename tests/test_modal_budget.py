from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest
from modal_app.budget import Budget, BudgetError, check_launch, load_budget, signoff_approved


@pytest.fixture
def budget() -> Budget:
    return replace(load_budget(), rates_confirmed=True)


def test_caps_fit_total_with_reserve() -> None:
    b = load_budget()
    caps = sum(j.cap_usd for j in b.jobs.values())
    assert b.total_usd == 50.0
    assert caps == pytest.approx(39.65)
    assert b.total_usd - caps == pytest.approx(10.35)


def test_unconfirmed_rates_refuse_everything() -> None:
    with pytest.raises(BudgetError, match="rates_confirmed"):
        check_launch(load_budget(), "inspect_models", [], signed_off=True)


def test_task_jobs_need_signoff_but_external_benchmarks_do_not(budget: Budget) -> None:
    check_launch(budget, "tau2_before", [], signed_off=False)
    check_launch(budget, "bfcl_before", [], signed_off=False)
    for job in ("smoke_train", "probe_and_dev", "train_grpo", "test_reference"):
        with pytest.raises(BudgetError, match="sign"):
            check_launch(budget, job, [], signed_off=False)


def test_succeeded_job_needs_explicit_rerun(budget: Budget) -> None:
    ledger = [{"job": "inspect_models", "status": "succeeded", "cost_usd": 0.01}]
    with pytest.raises(BudgetError, match="already succeeded"):
        check_launch(budget, "inspect_models", ledger, signed_off=True)
    check_launch(budget, "inspect_models", ledger, signed_off=True, rerun=True)


def test_overspending_blocks_jobs_that_would_eat_other_caps(budget: Budget) -> None:
    # Pretend failed attempts burned most of the reserve.
    ledger = [{"job": "smoke_tau2", "status": "failed", "cost_usd": 10.0}]
    with pytest.raises(BudgetError, match="only \\$"):
        check_launch(budget, "train_grpo", ledger, signed_off=True)


def test_signoff_requires_ticked_approval(tmp_path: Path) -> None:
    path = tmp_path / "pre-gpu.md"
    assert not signoff_approved(path)
    path.write_text("- [ ] Approved: GPU phases may start.\n")
    assert not signoff_approved(path)
    path.write_text("- [x] Approved: GPU phases may start.\n")
    assert signoff_approved(path)


def test_modal_app_defines_every_job() -> None:
    pytest.importorskip("modal")
    from modal_app.launch import _jobs

    assert set(_jobs()) == set(load_budget().jobs)


def test_tau2_driver_has_no_external_model_defaults() -> None:
    text = Path("modal_app/tau2_driver.py").read_text()
    assert "EvaluationType.ENV" in text
    assert "gpt-" not in text and "api.openai.com" not in text
