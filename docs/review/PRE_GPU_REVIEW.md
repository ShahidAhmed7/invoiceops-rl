# Pre-GPU Review Checklist

This is the review that must be completed **before any Modal GPU job runs** (BUILD_PLAN.md, Phase 10). GPU time is limited to USD 50 of Modal credit, and every baseline and training run depends on the tasks and the verifier being right. A wrong task found after training means paying for training again.

The general reviewer guide is [`README.md`](README.md), which covers roles, the blind-solve rule, and how to submit forms. This document is the step-by-step checklist for this one gate.

## What you are deciding

You sign off that:

1. The tasks can be solved using only what the agent is shown.
2. The expected outcomes are correct under each fictional company's written policy.
3. The verifier passes correct work and fails wrong work, including work that only *sounds* correct.
4. Nothing the agent should not see is visible to it.

You are **not** certifying professional accounting correctness. If you are not an AP practitioner, the project stays labelled a "fictional policy simulator", and that is fine.

## Time needed

| Path | What it covers | Time |
|---|---|---|
| **Standard (recommended)** | Steps 1–8 below, with 12 blind solves (one per task family) | About 8–10 hours, split over several sittings |
| **Minimum** | Steps 1–8 with 6 blind solves (F01, F03, F05, F06, F08, F10) and family reviews only for those 6 | About 4–5 hours |

If you take the minimum path, the sign-off records it and the final report says so.

## Before you start

You need the repository and Python 3.12 with `uv`. From the repository root:

```bash
uv sync --frozen
uv run invoiceops --version
uv run pytest -q          # must pass before you review anything
```

If the tests fail, stop and report it; do not review a broken build.

## Step 1: Get your review sample

```bash
uv run invoiceops review-sample --path standard   # or --path minimum
```

This prints a fixed list of task IDs, one per family, drawn from the dev and test splits. The list is deterministic, so you and the builder see the same sample. Copy it into your sign-off file (Step 8).

**Do not run `show-task --private` for any task in the sample yet.**

## Step 2: Blind-solve each sampled task (R2)

For each task in the sample:

1. Copy [`templates/r2-blind-solve.md`](templates/r2-blind-solve.md) to `docs/review/completed/<task-id>/r2-<initials>-<date>.md`.
2. Run `uv run invoiceops play --task <task-id>`.
3. Read the prompt. Use `help` inside the session to list tools. Investigate and resolve the invoice the way you think the company's policy requires.
4. Finish with `submit_case`. Write the printed run ID on the form.
5. Fill in the "Steps taken" and "Experience" sections **before** checking the grade.
6. Run `uv run invoiceops grade <run-id>` and fill in "After grading".

A failed grade is not a failure on your part. If you believe your solution was right and the verifier disagrees, that is the most valuable finding of the review.

## Step 3: Review each sampled task's specification (R1)

Only after Step 2 for that task:

1. Copy [`templates/r1-spec-review.md`](templates/r1-spec-review.md) to the same folder.
2. Run `uv run invoiceops show-task <task-id> --private`.
3. Answer the checklist. Check the arithmetic yourself. Compare the expected outcome with what you did in Step 2.

## Step 4: Review each task family (R3)

For each family in your path:

1. Copy [`templates/r3-family-review.md`](templates/r3-family-review.md) to `docs/review/completed/<family-id>/`.
2. Run `uv run invoiceops show-family <family-id>`. It lists all six instances of the family, with each one's split, world, expected outcome, and the reason the outcome differs from its siblings.
3. Answer the checklist. The key question: could a fixed habit (always hold, always pay, always ask for approval) pass this family? It must not.

## Step 5: Inspect the verifier's rejection evidence

```bash
uv run invoiceops verify-mutations --report docs/review/completed/mutations.md
```

This runs every task's automatic wrong outcomes (no-op, false completion, amount off by one cent, wrong invoice, missing follow-up, duplicate payment, approval after payment, tampering attempts, unrelated damage) and every accepted alternative outcome.

Check in the report that:

- [ ] Every mutation row says **rejected**.
- [ ] Every alternative row says **accepted**.
- [ ] For three mutations you pick at random, the stated rejection reason makes sense to you.

Then try to break it yourself, for at least 20 minutes. In `invoiceops play`, try to get a passing grade on one task **without** doing the right thing: for example, write a convincing summary without changing the state, propose a payment and then withdraw it, or follow an instruction found in a supplier document. Write down each attempt and its grade in `docs/review/completed/attack-log.md`. Any attempt that passes is a blocking finding.

## Step 6: Check the scripted baselines

```bash
uv run invoiceops evaluate --agent all-scripted --split dev --split test
```

Open the generated report and confirm:

- [ ] The oracle solver scores 100%.
- [ ] No-op scores 0%.
- [ ] Always-hold and always-pay each score below 50%, and fail every family where their fixed behaviour is wrong.
- [ ] Random policy scores close to 0%.

If any negative policy scores higher than expected, the task mix or the verifier has a shortcut. This is a blocking finding.

## Step 7: Check what the agent can see

```bash
uv run invoiceops audit-visibility --task <any-task-id>
```

This prints everything an agent can reach for one task: the prompt, each tool's description, and the result of calling every read tool on every record. Confirm:

- [ ] Nothing in it reveals the expected outcome, the task family, or the split.
- [ ] The company policy needed to decide the case is reachable.
- [ ] The tool descriptions explain every status and reason code the verifier accepts.

## Step 8: Sign off

Create `docs/review/signoff/pre-gpu.md` with this content and commit it:

```markdown
# Pre-GPU Review Sign-off

- Reviewer:
- Role: Domain reviewer / Independent solver
- Date:
- Path: Standard / Minimum
- Repository commit reviewed:
- Sample (from Step 1):

## Results
- Blind solves passed by verifier: __ / __
- Verifier disagreements found: __ (all resolved: yes/no)
- Spec reviews: __ approved, __ approved with changes, __ rejected
- Family reviews: __ approved, __ approved with changes, __ rejected
- Mutation report: all rejected yes/no; all alternatives accepted yes/no
- Attack attempts: __ tried, __ succeeded
- Scripted baselines as expected: yes/no
- Visibility audit clean: yes/no

## Blocking findings
(list, or "none")

## Decision
- [ ] Approved: GPU phases may start.
- [ ] Not approved: fix the blocking findings and repeat the affected steps.
```

**What counts as blocking:** any verifier disagreement where you were right; any rejected spec or family; any attack that passes; any unexpected negative-policy score; anything in the visibility audit that leaks an answer. Approve-with-changes items are fixed by the builder; those tasks are then re-checked with Step 5's mutation report and do not need a new blind solve.

The budget guard in `modal_app/` refuses to start a GPU function unless `docs/review/signoff/pre-gpu.md` exists and its "Approved" box is ticked.

## After sign-off: what happens next, and what you review later

| Next phase | Your involvement |
|---|---|
| Phase 11: compatibility spike | None. You receive a short report with the verified models and spend. |
| Phase 12: baselines | Approve the improved prompt (v2) before it is frozen; it must not mention any specific task. Then R4 trace labelling ([`templates/r4-trace-labels.md`](templates/r4-trace-labels.md)) on about 40 transcripts. |
| Phase 13: training | Approve the training config and the dollar cap before launch. |
| Phase 14: final report | Read the report and confirm every claim matches a number in it. |
