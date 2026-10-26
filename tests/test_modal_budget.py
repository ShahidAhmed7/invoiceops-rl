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
    assert caps == pytest.approx(57.60)
    assert b.total_usd - caps == pytest.approx(2.40)


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
    assert money["reserved"] == pytest.approx(
        57.60 - 3.30 - 0.85 - 26.70 - 0.80 - 1.35 - 2.45 - 3.30 - 0.80
    )


def test_remaining_evaluations_fit_funded_account_allocation(budget: Budget) -> None:
    for job in ("select_and_test", "tau2_after"):
        with pytest.raises(BudgetError, match="profile"):
            check_launch(budget, job, [], signed_off=True, account_profile=CAMPAIGN)
    money = check_launch(
        budget, "select_and_test", [], signed_off=True, account_profile="kazigalib143"
    )
    assert money["allocation_limit"] == 10.0
    assert money["worst_case"] == pytest.approx(80 / 60 * 2.45, abs=0.0001)
    ledger = [
        {
            "job": "select_and_test",
            "status": "succeeded",
            "cost_usd": 3.27,
            "allocation": "post_training",
        }
    ]
    money = check_launch(
        budget, "tau2_after", ledger, signed_off=True, account_profile="kazigalib143"
    )
    assert money["worst_case"] == pytest.approx(4.45)


@pytest.mark.parametrize(
    ("job", "profile", "allocation"),
    [
        ("bfcl_after", "invoiceops-thinking", "bfcl_final"),
        ("fresh_untrained_control", "kazigalib143", "fresh_control"),
    ],
)
def test_post_training_jobs_have_separate_account_bound_two_dollar_limits(
    budget: Budget, job: str, profile: str, allocation: str
) -> None:
    with pytest.raises(BudgetError, match="profile"):
        check_launch(budget, job, [], signed_off=True, account_profile="wrong-account")
    money = check_launch(budget, job, [], signed_off=True, account_profile=profile)
    assert money["allocation_limit"] == 2.0
    assert money["worst_case"] < 1.5
    with pytest.raises(BudgetError, match="allocation"):
        check_launch(
            budget,
            job,
            [{"job": job, "status": "failed", "cost_usd": 0.8, "allocation": allocation}],
            signed_off=True,
            account_profile=profile,
        )


def test_bfcl_uses_final_adapter_and_prices_merge_inside_its_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pytest.importorskip("modal")
    from modal_app import app
    from modal_app.launch import _jobs

    calls: list[tuple[str, int, tuple[object, ...], dict[str, object]]] = []

    class FakeFunction:
        def __init__(self, name: str) -> None:
            self.name, self.timeout = name, 0

        def with_options(self, *, timeout: int) -> FakeFunction:
            self.timeout = timeout
            return self

        def remote(self, *args: object, **kwargs: object) -> object:
            calls.append((self.name, self.timeout, args, kwargs))
            return "/runs/train/grpo-v3d/final_merged" if self.name == "merge" else {"ok": True}

    monkeypatch.setattr(app, "merge_checkpoint", FakeFunction("merge"))
    monkeypatch.setattr(app, "bfcl_eval", FakeFunction("eval"))
    result = _jobs()["bfcl_after"]()
    assert result["checkpoint"] == "final_adapter" and result["step"] == 150
    assert calls[0][1] + calls[1][1] == 35 * 60
    assert calls[0][2:] == (("grpo-v3d", "final_adapter"), {"target_dir": "final_merged"})
    assert calls[1][3] == {"model_path": "/runs/train/grpo-v3d/final_merged"}


def test_selected_bfcl_uses_dev_winner_and_verifies_hash(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import json

    pytest.importorskip("modal")
    from modal_app import app, launch

    config = tmp_path / "modal_app" / "train_config.json"
    config.parent.mkdir()
    config.write_text('{"run_name": "grpo-v3d"}')
    local = tmp_path / "runs/modal/training/grpo-v3d"
    dev = local / "selection/checkpoint-125"
    dev.mkdir(parents=True)
    (local / "selection.json").write_text(
        json.dumps(
            {
                "selected": "checkpoint-125",
                "dev_scores": {"final_adapter": 0.95, "checkpoint-125": 1.0},
            }
        )
    )
    (dev / "summary.json").write_text(
        json.dumps(
            {
                "tasks": 12,
                "attempts_per_task": 2,
                "scored_attempts": 24,
                "unscorable_attempts": 0,
                "task_mean_success": 1.0,
            }
        )
    )
    (dev / "config.json").write_text('{"adapter_sha256": "selected-hash"}')
    monkeypatch.setattr(launch, "ROOT", tmp_path)
    calls = []

    class FakeFunction:
        def __init__(self, name: str) -> None:
            self.name, self.timeout = name, 0

        def with_options(self, *, timeout: int) -> FakeFunction:
            self.timeout = timeout
            return self

        def remote(self, *args: object, **kwargs: object) -> object:
            calls.append((self.name, self.timeout, args, kwargs))
            return "/runs/train/grpo-v3d/selected_merged" if self.name == "merge" else {}

    monkeypatch.setattr(app, "merge_checkpoint", FakeFunction("merge"))
    monkeypatch.setattr(app, "bfcl_eval", FakeFunction("eval"))
    result = launch._jobs()["bfcl_selected"]()
    assert result["checkpoint"] == "checkpoint-125"
    assert sum(c[1] for c in calls) == 35 * 60
    assert calls[0][2:] == (
        ("grpo-v3d", "checkpoint-125"),
        {"expected_adapter_sha256": "selected-hash"},
    )
    assert calls[1][2][0] == "after-selected-checkpoint-125"
    # Preserve the recorded winner when equally scoring non-final checkpoints tie;
    # JSON key ordering must not silently change the selection decision.
    decision = json.loads((local / "selection.json").read_text())
    decision["dev_scores"]["checkpoint-100"] = 1.0
    (local / "selection.json").write_text(json.dumps(decision, sort_keys=True))
    assert launch._jobs()["bfcl_selected"]()["checkpoint"] == "checkpoint-125"
    b = load_budget()
    with pytest.raises(BudgetError, match="profile"):
        check_launch(b, "bfcl_selected", [], signed_off=True, account_profile="kazigalib143")
    money = check_launch(b, "bfcl_selected", [], signed_off=True, account_profile=CAMPAIGN)
    assert money["allocation_limit"] == 2.5


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
