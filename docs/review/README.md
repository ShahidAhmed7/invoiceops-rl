# Review Guide

This guide is for the people who review InvoiceOps RL tasks. The tasks, tools, and verifiers are written by the builder. Reviews are how we check that they are correct, solvable, and fair. A task is not published until it has passed review.

You do not need to read code. Every review uses either plain-language task documents or the same command-line tools the agent uses.

## Who reviews what

| Role | What they bring | Reviews they can do |
|---|---|---|
| **Independent solver** | Careful reading; no accounting background required | R2 blind solves, R4 trace labels |
| **Domain reviewer** | Experience in accounts payable, procurement, or bookkeeping | R1 spec reviews, R3 family reviews, plus everything above |

If no domain reviewer has signed off, the project is labelled a **fictional policy simulator**. In that case it must not claim to reflect professional AP practice (README §10.3). Record in each form which role you reviewed in.

## When reviews happen

All of these reviews happen at the **pre-GPU gate** (BUILD_PLAN.md, Phase 10), except R4, which follows the baseline runs. The step-by-step checklist for that gate is in [`PRE_GPU_REVIEW.md`](PRE_GPU_REVIEW.md).

| Gate | When | What you review | Blocks |
|---|---|---|---|
| **R1: Scenario spec review** | Before the first five tasks are implemented, and again for each new task | The written scenario: facts, policy, expected outcome | Implementing that task |
| **R2: Blind solve** | After the tools work (M2). Repeat for a sample of each new family | Solve the task yourself using only the agent tools | Publishing the task |
| **R3: Family review** | During suite expansion (M4), once per task family | The family's variants, edge cases, and failing examples | Adding the family to the release |
| **R4: Trace adjudication** | After baseline runs (M5) | Agent run transcripts: did it actually succeed? | The baseline report |

Expected volume for the full plan: 5 R1 reviews, then about 12 R3 family reviews; 5 or more R2 solves plus a sample from each family; about 40–60 traces for R4. Each R1 or R2 typically takes 20–45 minutes.

## The one rule: solve before you see the answer

A blind solve (R2) is only valid if you have **not** seen that task's expected outcome. Spec documents and verifier notes contain the expected outcome.

If one person does both reviews for the same task, the order is:

1. **R2 first.** Solve the task using only the task prompt and the tools. Submit the form.
2. **R1 afterwards** (or R3). Now open the spec and compare it with what you did.

If you see a task's answer by accident, write that down on the form, and do not do a blind solve for that task. Someone else can solve it, or the task is published with only R1 review and labelled as such.

Task folders separate the two kinds of material:

```text
tasks/<split>/<task-id>/
├── public.json          # agent-visible; safe for blind solvers
└── private.json         # expected outcome; R1/R3 reviewers only
```

You never need to read the JSON directly. `invoiceops show-task <task-id>` prints the agent-visible part as readable text, and `invoiceops show-task <task-id> --private` adds the expected outcome, the accepted alternatives, and the failing examples. Only use `--private` after any blind solve of that task.

## How to do each review

### R1: Scenario spec review

Use [`templates/r1-spec-review.md`](templates/r1-spec-review.md).

1. Run `invoiceops show-task <task-id>` and read it the way the agent would.
2. Run `invoiceops show-task <task-id> --private`: the company facts, the policy, the expected end state, and the listed failing examples.
3. Answer the checklist. The questions that matter most:
   - Can the expected outcome be reached using **only** information the agent can access?
   - Is it the **only** correct outcome? If another response is also reasonable, describe it. The verifier must accept it or the policy must be clarified.
   - Would a real AP team do this? (Domain reviewers only.)
   - Is the arithmetic correct?
4. Choose a decision: **Approve**, **Approve with changes**, or **Reject**.

### R2: Blind solve

Use [`templates/r2-blind-solve.md`](templates/r2-blind-solve.md).

1. Start a session with `invoiceops play --task <task-id>`.
2. Use only the tools listed in the prompt. Do not open `private.json`, run `show-task --private`, or read the `src/invoiceops/families/` or `src/invoiceops/verification/` code for that task.
3. Write down each step you take and why, in a few words.
4. Submit the case with `submit_case`. The session saves its log and prints the run ID; record it on your form.
5. Afterwards, run `invoiceops grade <run-id>` to see whether the verifier passed it, and why. If you believe your solution was correct but it failed (or the reverse), that disagreement is exactly what we are looking for. Note it in the form.

### R3: Family review

Use [`templates/r3-family-review.md`](templates/r3-family-review.md). Read the family description, then two or three of its task specs, and the list of failing examples. The main question is whether the variants test the same skill fairly, without tricks such as unclear IDs, hidden requirements, or padding.

### R4: Trace adjudication

Use [`templates/r4-trace-labels.md`](templates/r4-trace-labels.md). You receive run transcripts **without** the verifier's verdict. For each one, label it pass, fail, or ambiguous, and give a reason. The builder then compares your labels with the verifier's grades. Every disagreement is investigated and published.

## Submitting a review

- Copy the template into `docs/review/completed/<task-id or family-id>/`. Name the copy `<gate>-<your-initials>-<YYYY-MM-DD>.md`, for example `r1-sa-2026-11-03.md`.
- Commit it, or send it to the builder to commit. Reviews are kept in the repository as the audit trail.
- `docs/review/status.md` lists every task's review status and the task revision (content hash) that was reviewed. If a reviewed task changes later, its hash changes and it needs review again.

## What reviewers are not asked to do

- Certify professional or legal correctness. Reviews are design checks, not an accounting opinion.
- Fix tasks yourself. Describe the problem; the builder makes the change and requests re-review.
- Judge the agent's writing style. Grading is based on system state, not prose.
