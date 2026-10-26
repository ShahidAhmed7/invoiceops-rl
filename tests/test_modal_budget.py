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
    assert b.total_usd == 60.0
    assert caps == pytest.approx(55.45)
    assert b.total_usd - caps == pytest.approx(4.55)


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
    ledger = [{"job": "smoke_tau2", "status": "failed", "cost_usd": 40.0}]
    with pytest.raises(BudgetError, match="only \\$"):
        check_launch(budget, "test_reference", ledger, signed_off=True)


# The $25 GRPO training allocation (owner handoff 2026-10-26) is a separate pool bound
# to the second Modal account; entries are tagged allocation=grpo_training.
CAMPAIGN = "invoiceops-thinking"


def _campaign(job: str, status: str, cost: float) -> dict[str, object]:
    return {"job": job, "status": status, "cost_usd": cost, "allocation": "grpo_training"}


def test_allocation_jobs_need_their_own_account(budget: Budget) -> None:
    with pytest.raises(BudgetError, match="profile"):
        check_launch(budget, "smoke_train", [], signed_off=True, account_profile="default")
    money = check_launch(budget, "smoke_train", [], signed_off=True, account_profile=CAMPAIGN)
    # 20 min on H100; the main run's 360-minute worst case stays reserved inside the pool.
    assert money["worst_case"] == pytest.approx(1.4833)
    assert money["reserved"] == pytest.approx(26.7)
    assert money["allocation_limit"] == 60.0


def test_allocation_counts_only_its_own_ledger(budget: Budget) -> None:
    # A historical smoke success on the default pool does not block the campaign smoke.
    ledger: list[dict[str, object]] = [
        {"job": "smoke_train", "status": "succeeded", "cost_usd": 0.5}
    ]
    check_launch(budget, "smoke_train", ledger, signed_off=True, account_profile=CAMPAIGN)
    # Once the campaign smoke succeeds, another needs an explicit rerun.
    ledger.append(_campaign("smoke_train", "succeeded", 1.2))
    with pytest.raises(BudgetError, match="already succeeded"):
        check_launch(budget, "smoke_train", ledger, signed_off=True, account_profile=CAMPAIGN)
    check_launch(
        budget, "smoke_train", ledger, signed_off=True, rerun=True, account_profile=CAMPAIGN
    )


def test_allocation_guard_covers_the_full_campaign(budget: Budget) -> None:
    ledger = [_campaign("smoke_train", "succeeded", 1.4)]
    money = check_launch(budget, "train_grpo", ledger, signed_off=True, account_profile=CAMPAIGN)
    assert money["worst_case"] == pytest.approx(26.7)  # 360 min on H100
    assert money["spent"] == pytest.approx(1.4)
    # Even after the smoke, 1.4 + 26.70 stays under the 60 limit; a bigger burn refuses.
    ledger = [_campaign("smoke_train", "failed", 40.0)]
    with pytest.raises(BudgetError, match="allocation"):
        check_launch(budget, "train_grpo", ledger, signed_off=True, account_profile=CAMPAIGN)


def test_default_pool_ignores_allocation_entries_and_jobs(budget: Budget) -> None:
    ledger = [_campaign("train_grpo", "succeeded", 18.0)]
    money = check_launch(budget, "tau2_before", ledger, signed_off=False)
    assert money["spent"] == 0.0  # campaign spend never enters the default pool
    # Allocation jobs no longer reserve their caps from the default pool either.
    assert money["reserved"] == pytest.approx(55.45 - 3.30 - 0.85 - 26.70)


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


# The first credit release (USD 9.50). The core jobs must fit even if Modal's
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
    assert budget.spend_limit_usd >= 9.50  # the first release; the owner may release more
    budget = replace(budget, rates=PLANNING_RATES)
    padded = replace(budget, rates={k: v + 0.5 if v else v for k, v in budget.rates.items()})
    ledger: list[dict[str, object]] = []
    for job in FIRST_RELEASE_CORE:
        # smoke_train moved to the grpo_training allocation; it runs on that account.
        profile = CAMPAIGN if budget.allocation_for(job) else "default"
        money = check_launch(padded, job, ledger, signed_off=True, account_profile=profile)
        entry: dict[str, object] = {
            "job": job,
            "status": "succeeded",
            "cost_usd": money["worst_case"],
        }
        if budget.allocation_for(job):
            entry["allocation"] = budget.allocation_for(job).name
        ledger.append(entry)
    # At the planning rates, the optional jobs fit as well.
    ledger = []
    for job in FIRST_RELEASE_CORE + FIRST_RELEASE_OPTIONAL:
        profile = CAMPAIGN if budget.allocation_for(job) else "default"
        money = check_launch(budget, job, ledger, signed_off=True, account_profile=profile)
        entry = {"job": job, "status": "succeeded", "cost_usd": money["worst_case"]}
        if budget.allocation_for(job):
            entry["allocation"] = budget.allocation_for(job).name
        ledger.append(entry)
