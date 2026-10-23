# Modal Handoff: First Credit Release (USD 9.50)

This is the brief for the session that runs the first GPU jobs. Read it in full before spending anything. The general instructions are in [`MODAL_RUNBOOK.md`](MODAL_RUNBOOK.md), and the plan is in [`../BUILD_PLAN.md`](../BUILD_PLAN.md) (Phases 11A–12).

## The deal

- The project budget is still **USD 50** in total, but the owner has released only **USD 9.50** for now.
- `modal_app/budget.yaml` sets `spend_limit_usd: 9.50`. The launcher refuses any job whose worst case (hard timeout × rate) would take total spend above it. **Never raise it yourself**: only the owner releases more credit.
- Spend is counted from `reports/modal_ledger.jsonl`, which uses wall-clock time and is therefore an overestimate. The Modal dashboard is the real figure.

## Where things stand

| Item | State |
|---|---|
| Pre-GPU review | **Approved**, including the re-check (`docs/review/signoff/pre-gpu.md`). Jobs on InvoiceOps tasks may run. |
| Post-approval change | A verifier-only fix (a requested receipt must arrive before the decision); see the end of `docs/review/builder-response.md`. Tasks are unchanged. |
| Prompt v2 | Approved and frozen: `src/invoiceops/agents/prompts/system_v2.md`, sha256 `da1dd707ab199f8b55877cda332d6121dd7844d2f2d3031ebab20c7485c98ae0`. Do not edit it. |
| Model revisions | Not pinned yet (`modal_app/settings.py` → `REVISIONS` are `None`). Evaluation jobs refuse to run until step 2 below. |
| GPU rates | Not confirmed (`rates_confirmed: false`). Every launch is refused until step 1 below. |
| Modal access | The owner added `MODAL_TOKEN_ID` and `MODAL_TOKEN_SECRET` as environment variables, and allowed `api.modal.com` and `api.modal2.com`. Verify this; don't assume it. |

## What runs in this release

The jobs are chosen to remove the risks that could waste the big training spend later, and to produce the first real baseline number. Run them **in this order** and **stop at the first failure**.

Worst cases use the planning rates (H100 $3.95/h, L40S $1.95/h).

| # | Job | GPU, hard limit | Worst case | Why now |
|---|---|---|---|---|
| 1 | `inspect_models` | CPU, 10 min | ≈ $0 | Pins model revisions and checks licences and tool templates. Also builds all the images, so later GPU jobs don't pay for builds. |
| 2 | `smoke_serve_candidate` | L40S, 20 min | $0.65 | vLLM serves the 4B candidate, a tool call parses, and BFCL runs against it. Nearly every later job depends on this. |
| 3 | `probe_and_dev` | L40S, 30 + 20 min | $1.63 | Learnability probe on the training split, plus a dev run. **Decides whether training is worth paying for.** |
| 4 | `smoke_train` | H100, 20 min | $1.32 | Three GRPO steps through `environment_factory`. Proves the training stack before the $15.80 run. |
| 5 | `test_candidate` | L40S, 32 + 32 min | $2.11 | **First real result:** the untrained 4B model on our 24 held-out test tasks, prompts v1 and v2, 4 attempts each. |
| 6 | `smoke_tau2` (optional) | H100, 25 min | $1.65 | τ²-bench pipeline check and timing. The next release's τ²-bench budget depends on it. |
| 7 | `bfcl_before` (optional) | L40S, 35 min | $1.14 | BFCL baseline of the untrained model. Cheap, and frozen for the before/after comparison. |

Jobs 1–5 add up to $5.70 worst case. All seven add up to $8.49, leaving $1.01 for Modal's CPU and memory charges and at most one cheap re-run. `tests/test_modal_budget.py` checks that jobs 1–5 still fit if those charges add $0.50/h to every GPU rate.

**Not in this release:** `smoke_serve_reference`, `tau2_before`, `tau2_reference`, `test_reference`, `train_grpo`, and all of Phase 14. They wait for the owner's next release.

## Step by step

### 0. Check access (free)

```bash
uv sync --frozen --extra openenv --group modal
test -n "$MODAL_TOKEN_ID" && test -n "$MODAL_TOKEN_SECRET" && echo "token variables present"
uv run --group modal modal app list        # an API call that costs nothing
```

Never print the token values. If the variables are missing or `api.modal.com` is denied, stop and tell the owner what is missing. A session only picks up environment changes when it starts.

### 1. Confirm the rates (free)

1. Get the current **H100** and **L40S** per-hour prices from Modal's pricing page, or ask the owner to read them from the dashboard. If `modal.com` is blocked here, ask the owner; don't guess.
2. Modal also bills CPU and memory on GPU containers. Enter **all-in** rates: the GPU price plus **$0.50/h**. For example, if H100 is $3.95/h, write 4.45. Keep `CPU: 0.0`.
3. Set `rates_confirmed: true`.
4. Run `uv run --group modal python -m modal_app.launch <job> --dry-run` for each job in the table, in order. Every dry run must print a worst case.
5. If the higher rates mean jobs 6 and 7 no longer fit, they are the ones to drop. The guard refuses them on its own.
6. Commit the rates.

### 2. `inspect_models`, then pin revisions

```bash
uv run --group modal python -m modal_app.launch inspect_models
```

Check `reports/model_verification.json`:
- every primary model exists, has a licence, and its chat template supports tools;
- the FP8 reference model exists. If it doesn't, set `REFERENCE_FP8` in `modal_app/settings.py` to the bf16 model.

Then copy each `revision` into `REVISIONS` in `modal_app/settings.py`. Run `uv run pytest -q` and commit.

### 3–7. GPU jobs

Run each job with `uv run --group modal python -m modal_app.launch <job>`. After each one:

1. Read its result in `reports/modal/<job>.json` and its line in `reports/modal_ledger.jsonl`.
2. Check the success condition below.
3. Commit the reports.

| Job | Success means | If it fails |
|---|---|---|
| `smoke_serve_candidate` | `roundtrip.ok` is true and the BFCL smoke score files exist | Read the error. If the fix is clear (parser flag, memory setting), fix it, run the tests, and re-run once with `--rerun`. If not, stop. |
| `probe_and_dev` | Both summaries exist. On the training split, some tasks pass in some attempts and fail in others. | If nearly every training task always fails or always passes, **record it** in `reports/compatibility.md` and still continue to `smoke_train`. The owner decides about the curriculum before training. |
| `smoke_train` | Three steps finished, rewards appear in `log_history.json`, and a checkpoint was saved | Stop. Do not try training fixes with the remaining credit; write up the error. |
| `test_candidate` | Summaries for v1 and v2 exist, with task-mean success and confidence intervals | Re-run only if it died before any episode ran. |
| `smoke_tau2` | `simulations` is 2, `simulations_without_reward` is 0, and `seconds_per_simulation` is recorded | Stop. Record the error for the next release. |
| `bfcl_before` | Score files exist for every category in `settings.BFCL_CATEGORIES` | Stop. Record the error. |

**Re-run rules:**
- Never re-run a job that hit its hard timeout. A hang will just hang again.
- Re-run a failed job at most once, after fixing the cause and running `uv run pytest -q`.
- Re-runs come out of the same $9.50.

## What to write and commit

- `reports/modal_ledger.jsonl`, `reports/modal/*.json`, `reports/model_verification.json`, and the pinned `modal_app/settings.py`.
- `reports/compatibility.md`:
  - what worked;
  - versions and revisions;
  - tool-call parsing;
  - the learnability probe result, per family;
  - training-stack status;
  - the τ²-bench timing and the trials rule from `MODAL_RUNBOOK.md` §1 step 4.
- `reports/baseline.md`, partial:
  - the untrained candidate on the test split, prompts v1 and v2, with confidence intervals, a per-family breakdown, and critical violations;
  - mark the reference-model row as "not run yet".
- If `bfcl_before` ran: start `reports/external_baseline.md` with the BFCL numbers and the exact settings, and mark τ²-bench "not run yet".
- The README's "Measured so far" table gets a row for the untrained candidate, with the real numbers only.
- A spend summary: ledger total versus the Modal dashboard figure. Ask the owner for the dashboard figure if you can't see it.

**Rules:**
- Commit as the repository's configured author (`ShahidAhmed7`) and push to `main`. No co-author lines or AI attribution in commits.
- No pull request unless the owner asks.
- Never put tokens in files, commits, or chat.
- Report real numbers only, including bad ones. If something didn't run, say so.

## For the next release (owner's decision)

After this release, $40.50 of the $50 remains. The remaining jobs, with their caps from `budget.yaml`:
- **External baselines:** `smoke_serve_reference` $1.00, `tau2_before` $3.30, `tau2_reference` $3.30.
- **Reference model on our tasks:** `test_reference` $3.00.
- **Training:** `train_grpo` $15.80.
- **Final evaluation:** `select_and_test` $2.45, `tau2_after` $3.30, `bfcl_after` $0.80.

`tau2_before` must run before training (or at least on the untrained weights) so that the before/after comparison uses the same configuration. The reference-model jobs only add context and can be dropped if money is short.
