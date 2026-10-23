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
    assert caps == pytest.approx(40.40)
    assert b.total_usd - caps == pytest.approx(9.60)


def test_unconfirmed_rates_refuse_everything() -> None:
    unconfirmed = replace(load_budget(), rates_confirmed=False)
    with pytest.raises(BudgetError, match="rates_confirmed"):
        check_launch(unconfirmed, "inspect_models", [], signed_off=True)


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


def test_spend_limit_refuses_jobs_beyond_released_credit(budget: Budget) -> None:
    limited = replace(budget, spend_limit_usd=2.0)
    check_launch(limited, "smoke_serve_candidate", [], signed_off=True)  # worst case $0.65
    with pytest.raises(BudgetError, match="released"):
        check_launch(limited, "tau2_before", [], signed_off=True)  # worst case $3.95
    spent = [{"job": "smoke_serve_candidate", "status": "succeeded", "cost_usd": 1.5}]
    with pytest.raises(BudgetError, match="released"):
        check_launch(limited, "bfcl_before", spent, signed_off=True)


def test_multi_call_jobs_fit_their_priced_timeout() -> None:
    from modal_app.launch import CALL_MINUTES

    jobs = load_budget().jobs
    for name, minutes in CALL_MINUTES.items():
        assert sum(minutes) <= jobs[name].timeout_min, name


# The first credit release (docs/MODAL_HANDOFF.md). The core jobs must fit even if Modal's
# CPU and memory charges add $0.50/h to every GPU rate; the optional ones run only if the
# guard still allows them.
FIRST_RELEASE_CORE = (
    "inspect_models",
    "smoke_serve_candidate",
    "probe_and_dev",
    "smoke_train",
    "test_candidate",
)
FIRST_RELEASE_OPTIONAL = ("smoke_tau2", "bfcl_before")


# GPU prices used for planning, before the CPU and memory allowance is added.
PLANNING_RATES = {"H100": 3.95, "L40S": 1.95, "CPU": 0.0}


def test_first_release_fits_the_spend_limit(budget: Budget) -> None:
    assert budget.spend_limit_usd == pytest.approx(9.50)
    budget = replace(budget, rates=PLANNING_RATES)
    padded = replace(budget, rates={k: v + 0.5 if v else v for k, v in budget.rates.items()})
    ledger: list[dict[str, object]] = []
    for job in FIRST_RELEASE_CORE:
        money = check_launch(padded, job, ledger, signed_off=True)
        ledger.append({"job": job, "status": "succeeded", "cost_usd": money["worst_case"]})
    # At the planning rates, the optional jobs fit as well.
    ledger = []
    for job in FIRST_RELEASE_CORE + FIRST_RELEASE_OPTIONAL:
        money = check_launch(budget, job, ledger, signed_off=True)
        ledger.append({"job": job, "status": "succeeded", "cost_usd": money["worst_case"]})
