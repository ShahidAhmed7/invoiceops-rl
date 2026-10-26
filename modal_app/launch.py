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
import os
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
# Jobs that take --prompt; their reports and ledger lines carry the prompt version.
PROMPT_JOBS = ("prompt_trial", "test_prompt")
# Training jobs write one report per run name so retries cannot overwrite evidence.
TRAIN_JOBS = ("smoke_train", "train_grpo")
SMOKE_TRAIN = {
    # Readiness smoke at full training settings: complete 144-row generated curriculum,
    # full 2x16 accumulation (32 rollouts/step = 4 groups of 8), trajectory logging.
    # run_name is set per launch (--run-name or a UTC timestamp); fresh dirs only.
    "generated_variants": 144,
    "wall_clock_limit_min": 14,
    "grpo": {"max_steps": 3, "save_steps": 1},
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
    "prompt_trial": (17, 11),
    "test_prompt": (32,),
    "test_candidate": (32, 32),
    "select_and_test": (40, 10, 30),
    "smoke_post_train": (20, 10, 12),
}


def _limit(fn: Any, minutes: int) -> Any:
    return fn.with_options(timeout=minutes * 60)


def _stamp(prefix: str) -> str:
    return f"{prefix}-{time.strftime('%Y%m%d-%H%M%S', time.gmtime())}"


def _jobs(prompt: str = "v2", run_name: str | None = None) -> dict[str, Callable[[], Any]]:
    from modal_app import app as m

    train_config = json.loads((ROOT / "modal_app" / "train_config.json").read_text())
    if run_name:
        train_config["run_name"] = run_name
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

    def prompt_trial() -> Any:
        # Prompt engineering on train and dev only; the test split is run once, for the winner.
        train, dev = CALL_MINUTES["prompt_trial"]
        return {
            "train": _limit(m.invoiceops_eval_l40s, train).remote(
                f"probe-train-{prompt}",
                settings.CANDIDATE_MODEL,
                splits=["train"],
                attempts=4,
                prompt=prompt,
            ),
            "dev": _limit(m.invoiceops_eval_l40s, dev).remote(
                f"dev-{prompt}",
                settings.CANDIDATE_MODEL,
                splits=["dev"],
                attempts=4,
                prompt=prompt,
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
            f"test-trained-{settings.AGENT_PROMPT}",
            settings.CANDIDATE_MODEL,
            model_path=path,
            splits=["test"],
            attempts=4,
            prompt=settings.AGENT_PROMPT,
        )
        return {"selection": selection, "merged": path, "test": test}

    def smoke_post_train() -> Any:
        # The post-training chain (LoRA serving, selection, merge, serving merged weights) on the
        # smoke_train adapter, at minimum size, before paying for train_grpo.
        select, merge, evaluate = CALL_MINUTES["smoke_post_train"]
        selection = _limit(m.select_checkpoint, select).remote(
            "smoke", attempts=1, max_candidates=2
        )
        path = _limit(m.merge_checkpoint, merge).remote("smoke", selection["selected"])
        merged = _limit(m.invoiceops_eval_l40s, evaluate).remote(
            "smoke-merged",
            settings.CANDIDATE_MODEL,
            model_path=path,
            splits=["dev"],
            attempts=1,
            prompt=settings.AGENT_PROMPT,
        )
        return {"selection": selection, "merged": path, "merged_dev": merged}

    return {
        "inspect_models": lambda: m.inspect_models.remote(),
        "smoke_serve_candidate": lambda: m.smoke_serve_candidate.remote(),
        "smoke_thinking": lambda: m.smoke_thinking.remote(),
        "smoke_serve_reference": lambda: m.smoke_serve_reference.remote(),
        "smoke_tau2": lambda: m.smoke_tau2.remote(),
        "tau2_before": lambda: m.tau2_eval.remote("before", settings.CANDIDATE_MODEL),
        "tau2_reference": lambda: m.tau2_eval.remote("reference", settings.REFERENCE_FP8),
        "bfcl_before": lambda: m.bfcl_eval.remote("before"),
        "smoke_train": lambda: _limit(m.train_grpo, CALL_MINUTES["smoke_train"][0]).remote(
            json.dumps({**SMOKE_TRAIN, "run_name": run_name if run_name else _stamp("smoke")})
        ),
        "probe_and_dev": probe_and_dev,
        "probe_v2": lambda: _limit(m.invoiceops_eval_l40s, CALL_MINUTES["probe_v2"][0]).remote(
            "probe-train-v2", settings.CANDIDATE_MODEL, splits=["train"], attempts=4, prompt="v2"
        ),
        "dev_v2": lambda: _limit(m.invoiceops_eval_l40s, CALL_MINUTES["dev_v2"][0]).remote(
            "dev-v2", settings.CANDIDATE_MODEL, splits=["dev"], attempts=4, prompt="v2"
        ),
        "prompt_trial": prompt_trial,
        "test_prompt": lambda: _limit(
            m.invoiceops_eval_l40s, CALL_MINUTES["test_prompt"][0]
        ).remote(
            f"test-candidate-{prompt}",
            settings.CANDIDATE_MODEL,
            splits=["test"],
            attempts=4,
            prompt=prompt,
        ),
        "test_candidate": test_candidate,
        # Prompt v2: the transcript audit shows v1 mostly measures whether a model guesses that a
        # payment proposal is required (reports/transcript_audit.md).
        "test_reference": lambda: m.invoiceops_eval_h100.remote(
            "test-reference-v2", settings.REFERENCE_FP8, splits=["test"], attempts=4, prompt="v2"
        ),
        "train_grpo": lambda: m.train_grpo.remote(json.dumps(train_config)),
        "select_and_test": select_and_test,
        "smoke_post_train": smoke_post_train,
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
    parser.add_argument("--prompt", default="v2", help="system prompt version for prompt_trial")
    parser.add_argument(
        "--run-name",
        help="training run directory name for smoke_train/train_grpo "
        "(default: train_config.json's run_name; smoke gets a UTC timestamp)",
    )
    args = parser.parse_args(argv)

    budget = load_budget()
    ledger = read_ledger()
    account_profile = os.environ.get("MODAL_PROFILE", "default")
    try:
        money = check_launch(
            budget,
            args.job,
            ledger,
            signoff_approved(),
            rerun=args.rerun,
            account_profile=account_profile,
        )
    except BudgetError as exc:
        print(f"refused: {exc}")
        return 2
    job = budget.jobs[args.job]
    alloc = budget.allocation_for(args.job)
    run_name = args.run_name
    if args.job == "smoke_train" and run_name is None:
        run_name = _stamp("smoke")
    elif args.job == "train_grpo" and run_name is None:
        run_name = json.loads((ROOT / "modal_app" / "train_config.json").read_text())["run_name"]
    print(
        f"{args.job}: up to ${money['worst_case']:.2f} on {job.gpu} "
        f"(cap ${job.cap_usd:.2f}); spent so far ${money['spent']:.2f}"
        + (f"; allocation {alloc.name} limit ${alloc.limit_usd:.2f}" if alloc else "")
        + (f"; run {run_name}" if run_name else "")
    )
    if args.dry_run:
        return 0

    import modal

    from modal_app import app as modal_app_module

    started = time.time()
    status, result, error = "failed", None, None
    try:
        with modal.enable_output(), modal_app_module.app.run():
            result = _jobs(args.prompt, run_name)[args.job]()
            if args.job == "smoke_thinking" and not result["pipeline_ok"]:
                raise RuntimeError("Thinking smoke acceptance checks failed; see its report.")
        status = "succeeded"
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
    finally:
        seconds = time.time() - started
        cost = round(budget.rate(job) * seconds / 3600, 4)
        append_ledger(
            {
                "job": args.job,
                "account_profile": account_profile,
                "phase": job.phase,
                "gpu": job.gpu,
                "status": status,
                "started": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(started)),
                "seconds": round(seconds, 1),
                "rate_usd_per_hour": budget.rate(job),
                "cost_usd": cost,
                "error": error,
                **({"allocation": alloc.name} if alloc else {}),
                **({"run_name": run_name} if run_name and args.job in TRAIN_JOBS else {}),
                **({"prompt": args.prompt} if args.job in PROMPT_JOBS else {}),
            }
        )
    REPORTS.mkdir(parents=True, exist_ok=True)
    if result is not None:
        if args.job in PROMPT_JOBS:
            name = f"{args.job}-{args.prompt}"
        elif args.job in TRAIN_JOBS and run_name:
            name = f"{args.job}-{run_name}"
        else:
            name = args.job
        Path(REPORTS / f"{name}.json").write_text(
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
