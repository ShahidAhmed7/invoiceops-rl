"""Launch one budgeted Modal job.

    uv run --group modal python -m modal_app.launch <job> [--dry-run] [--rerun]

Each job name matches ``budget.yaml``. The launcher refuses jobs the budget or the review
sign-off does not allow, runs the job on Modal, saves its result under ``reports/modal/``, and
appends the measured wall-clock cost to ``reports/modal_ledger.jsonl``. The ledger estimate
includes container start-up and is therefore conservative; reconcile it with the Modal
dashboard after each job.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from modal_app import settings
from modal_app.budget import (
    ROOT,
    BudgetError,
    append_ledger,
    check_launch,
    load_budget,
    read_ledger,
    signoff_approved,
)

REPORTS = ROOT / "reports" / "modal"
SMOKE_TRAIN = {
    "run_name": "smoke",
    "generated_variants": 0,
    "wall_clock_limit_min": 12,
    # 2 x 4 = 8 rollouts per step: one group of num_generations.
    "grpo": {"max_steps": 3, "save_steps": 3, "gradient_accumulation_steps": 4},
}
# Hard timeouts (minutes) for each Modal call a job makes, in order. A job that makes several
# calls, or reuses a long-running function for a short check, gets a per-call timeout so that
# the calls together never run longer than the job's ``timeout_min`` in budget.yaml, which is
# what the budget guard prices. Jobs not listed make one call with the function's own timeout.
CALL_MINUTES: dict[str, tuple[int, ...]] = {
    "smoke_train": (20,),
    "probe_and_dev": (30, 20),
    "probe_v2": (25,),
    "dev_v2": (20,),
    "test_candidate": (32, 32),
    "select_and_test": (40, 10, 30),
}


def _limit(fn: Any, minutes: int) -> Any:
    return fn.with_options(timeout=minutes * 60)


def _jobs() -> dict[str, Callable[[], Any]]:
    from modal_app import app as m

    train_config = json.loads((ROOT / "modal_app" / "train_config.json").read_text())
    run_name = train_config["run_name"]
    merged = f"/runs/train/{run_name}/selected_merged"

    def probe_and_dev() -> Any:
        probe, dev = CALL_MINUTES["probe_and_dev"]
        return {
            "probe": _limit(m.invoiceops_eval_l40s, probe).remote(
                "probe-train", settings.CANDIDATE_MODEL, splits=["train"], attempts=4
            ),
            "dev": _limit(m.invoiceops_eval_l40s, dev).remote(
                "dev-v1", settings.CANDIDATE_MODEL, splits=["dev"], attempts=2
            ),
        }

    def test_candidate() -> Any:
        minutes = dict(zip(("v1", "v2"), CALL_MINUTES["test_candidate"], strict=True))
        return {
            p: _limit(m.invoiceops_eval_l40s, minutes[p]).remote(
                f"test-candidate-{p}",
                settings.CANDIDATE_MODEL,
                splits=["test"],
                attempts=4,
                prompt=p,
            )
            for p in ("v1", "v2")
        }

    def select_and_test() -> Any:
        select, merge, test_min = CALL_MINUTES["select_and_test"]
        selection = _limit(m.select_checkpoint, select).remote(run_name)
        path = _limit(m.merge_checkpoint, merge).remote(run_name, selection["selected"])
        test = _limit(m.invoiceops_eval_l40s, test_min).remote(
            "test-trained-v1",
            settings.CANDIDATE_MODEL,
            model_path=path,
            splits=["test"],
            attempts=4,
        )
        return {"selection": selection, "merged": path, "test": test}

    return {
        "inspect_models": lambda: m.inspect_models.remote(),
        "smoke_serve_candidate": lambda: m.smoke_serve_candidate.remote(),
        "smoke_serve_reference": lambda: m.smoke_serve_reference.remote(),
        "smoke_tau2": lambda: m.smoke_tau2.remote(),
        "tau2_before": lambda: m.tau2_eval.remote("before", settings.CANDIDATE_MODEL),
        "tau2_reference": lambda: m.tau2_eval.remote("reference", settings.REFERENCE_FP8),
        "bfcl_before": lambda: m.bfcl_eval.remote("before"),
        "smoke_train": lambda: _limit(m.train_grpo, CALL_MINUTES["smoke_train"][0]).remote(
            json.dumps(SMOKE_TRAIN)
        ),
        "probe_and_dev": probe_and_dev,
        "probe_v2": lambda: _limit(m.invoiceops_eval_l40s, CALL_MINUTES["probe_v2"][0]).remote(
            "probe-train-v2", settings.CANDIDATE_MODEL, splits=["train"], attempts=4, prompt="v2"
        ),
        "dev_v2": lambda: _limit(m.invoiceops_eval_l40s, CALL_MINUTES["dev_v2"][0]).remote(
            "dev-v2", settings.CANDIDATE_MODEL, splits=["dev"], attempts=4, prompt="v2"
        ),
        "test_candidate": test_candidate,
        # Prompt v2: the transcript audit shows v1 mostly measures whether a model guesses that a
        # payment proposal is required (reports/transcript_audit.md).
        "test_reference": lambda: m.invoiceops_eval_h100.remote(
            "test-reference-v2", settings.REFERENCE_FP8, splits=["test"], attempts=4, prompt="v2"
        ),
        "train_grpo": lambda: m.train_grpo.remote(json.dumps(train_config)),
        "select_and_test": select_and_test,
        "tau2_after": lambda: m.tau2_eval.remote(
            "after", settings.CANDIDATE_MODEL, agent_path=merged
        ),
        "bfcl_after": lambda: m.bfcl_eval.remote("after", model_path=merged),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("job")
    parser.add_argument("--dry-run", action="store_true", help="check the guard and stop")
    parser.add_argument("--rerun", action="store_true", help="allow re-running a succeeded job")
    args = parser.parse_args(argv)

    budget = load_budget()
    ledger = read_ledger()
    try:
        money = check_launch(budget, args.job, ledger, signoff_approved(), rerun=args.rerun)
    except BudgetError as exc:
        print(f"refused: {exc}")
        return 2
    job = budget.jobs[args.job]
    print(
        f"{args.job}: up to ${money['worst_case']:.2f} on {job.gpu} "
        f"(cap ${job.cap_usd:.2f}); spent so far ${money['spent']:.2f}"
    )
    if args.dry_run:
        return 0

    import modal

    from modal_app import app as modal_app_module

    started = time.time()
    status, result, error = "failed", None, None
    try:
        with modal.enable_output(), modal_app_module.app.run():
            result = _jobs()[args.job]()
        status = "succeeded"
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
    finally:
        seconds = time.time() - started
        cost = round(budget.rate(job) * seconds / 3600, 4)
        append_ledger(
            {
                "job": args.job,
                "phase": job.phase,
                "gpu": job.gpu,
                "status": status,
                "started": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(started)),
                "seconds": round(seconds, 1),
                "rate_usd_per_hour": budget.rate(job),
                "cost_usd": cost,
                "error": error,
            }
        )
    REPORTS.mkdir(parents=True, exist_ok=True)
    if result is not None:
        Path(REPORTS / f"{args.job}.json").write_text(
            json.dumps(result, indent=2, sort_keys=True, default=str)
        )
        if args.job == "inspect_models":
            (ROOT / "reports" / "model_verification.json").write_text(
                json.dumps(result, indent=2, sort_keys=True)
            )
    print(
        f"{args.job}: {status} in {seconds / 60:.1f} min, estimated ${cost:.2f}"
        + (f" ({error})" if error else "")
    )
    return 0 if status == "succeeded" else 1


if __name__ == "__main__":
    sys.exit(main())
