# Modal Runbook

Step-by-step instructions for the GPU phases (BUILD_PLAN.md Phases 11A–14). Everything here is written and tested locally, but **none of it has run on Modal yet**, so the first steps are cheap smoke tests that check the setup before any long job.

Every job goes through one command:

```bash
uv run python -m modal_app.launch <job>            # add --dry-run to check without spending
```

The launcher refuses a job if:

- the GPU rates in `modal_app/budget.yaml` are not confirmed,
- the job uses InvoiceOps tasks and the pre-GPU review is not signed off,
- the job already succeeded (pass `--rerun` to repeat it on purpose), or
- its worst case (timeout × rate) does not fit in the budget left after reserving every other job's cap, or
- its worst case would take total spend above `spend_limit_usd`, the credit the owner has released so far. The first release is USD 9.50; see [`MODAL_HANDOFF.md`](MODAL_HANDOFF.md) for what it covers.

Each launch appends its measured cost to `reports/modal_ledger.jsonl` and saves its result under `reports/modal/`. The ledger counts wall-clock time including container start-up, so it slightly overestimates. Compare it with the Modal dashboard after each job.

## 0. One-time setup

1. **Account and spending limit.** In the Modal dashboard, set a workspace spending limit if your plan offers one.
2. **Token.** Create an API token (Settings → API Tokens). If you work in a Claude Code cloud session, add it as `MODAL_TOKEN_ID` and `MODAL_TOKEN_SECRET` in the environment settings, and never in chat. On your own machine, run `uv run --group modal modal token set --token-id ... --token-secret ...`.
3. **Network.** If you run from a Claude Code cloud environment, add `api.modal.com` and `api.modal2.com` under Allowed domains.
4. **Dependencies.** Run `uv sync --frozen --extra openenv --group modal`.
5. **Rates.** Copy the current H100 and L40S per-hour prices from Modal's pricing page into `modal_app/budget.yaml`, set `rates_confirmed: true`, and commit.
6. **Check.** Run `uv run python -m modal_app.launch inspect_models --dry-run`. It should print the job's worst-case cost.

## 1. Phase 11A: external baselines (no review needed, about $10)

Run these in order and stop at the first failure.

| Step | Command | What to check afterwards |
|---|---|---|
| 1 | `launch inspect_models` | `reports/model_verification.json`: every primary model `exists`, has a license, and `chat_template_mentions_tools` is true. **Copy each `revision` into `modal_app/settings.py` → `REVISIONS` and commit.** If the FP8 reference model does not exist, set `REFERENCE_FP8` to the bf16 model in `settings.py`. |
| 2 | `launch smoke_serve_candidate` | `reports/modal/smoke_serve_candidate.json`: `roundtrip.ok` is true and the BFCL smoke score files exist. |
| 3 | `launch smoke_serve_reference` | `roundtrip.ok` is true. |
| 4 | `launch smoke_tau2` | `simulations` is 2, `simulations_without_reward` is 0, and note `seconds_per_simulation`. **Budget rule:** if `seconds_per_simulation × 160 / concurrency 16` plus about 10 minutes of start-up is over 50 minutes, set `TAU2_TRIALS = 2` in `settings.py` before step 5. |
| 5 | `launch tau2_before` | `reports/modal/tau2_before.json`: `pass_1` and `pass^4` for the untrained model. |
| 6 | `launch tau2_reference` | The same numbers with the reference model as the agent. |
| 7 | `launch bfcl_before` | BFCL score CSVs per category. |

Then write `reports/external_baseline.md` from those files. Each run's numbers are frozen: Phase 14 re-runs the identical configuration on the trained model.

If a job fails, its ledger line has the error. Fix the cause, then re-run with `--rerun`; a failure never triggers an automatic retry.

## 2. Phase 10: pre-GPU review

Follow [`review/PRE_GPU_REVIEW.md`](review/PRE_GPU_REVIEW.md) and commit an approved `docs/review/signoff/pre-gpu.md`. The remaining jobs refuse to start until then.

## 3. Phase 11B–12: our tasks (about $7.35)

| Step | Command | What to check |
|---|---|---|
| 1 | `launch smoke_train` | Three GRPO steps finished, rewards appear in `log_history.json`, and a checkpoint was saved. |
| 2 | `launch probe_and_dev` | Learnability: on the training split, some tasks must pass sometimes and fail sometimes. If nearly every task always fails (or always passes), stop and adjust the curriculum before training. |
| 3 | Freeze `src/invoiceops/agents/prompts/system_v2.md` (reviewer approves; no test transcripts may be read first). | |
| 4 | `launch test_candidate` | Test split, prompts v1 and v2, 4 attempts each. |
| 5 | `launch test_reference` | Reference model on the test split. |

Write `reports/baseline.md`.

## 4. Phase 13: training (about $15.80)

1. Review `modal_app/train_config.json` (the defaults are in `modal_app/train_grpo.py`). Get the reviewer's approval of the config and the cap.
2. Run `launch train_grpo`. Training stops at `max_steps` or after `wall_clock_limit_min` (225 minutes), whichever comes first, and saves the final adapter.

## 5. Phase 14: final evaluation (about $6.55)

| Step | Command | What it does |
|---|---|---|
| 1 | `launch select_and_test` | Picks the checkpoint by **development** success only, merges it, then runs the test split once. |
| 2 | `launch tau2_after` | τ²-bench retail with the merged trained model; same customer model, seed, and trials as before. |
| 3 | `launch bfcl_after` | BFCL with the merged trained model. |

Write `reports/final.md`: before vs. after on our test split, on τ²-bench, and per BFCL category, with confidence intervals, critical violations, and any regressions stated plainly.

## What each result can and cannot claim

- **Our test split:** held-out *companies*, same 12 task families. Not evidence of generalisation to new kinds of task.
- **τ²-bench:** graded on database state only, with an open simulated customer. Valid for before/after comparison, but **not comparable with the public leaderboard**.
- **BFCL:** our own runs with our serving setup. Compared only with each other, not presented as leaderboard entries.
- **One training run** is preliminary evidence; say so.
