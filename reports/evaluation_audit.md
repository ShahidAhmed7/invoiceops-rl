# Evaluation audit — 2026-10-26

**The primary metric is appropriate:** strict success under the trusted verifier. It checks
the final AP state and action history, including payment amounts, approvals, receipts,
evidence, forbidden actions and a consistent submission. Passing prose is insufficient.
No LLM judge determines InvoiceOps correctness. The binary reward used in training and
the success predicate used in evaluation come from the same verifier.

The audit found and fixed accounting and evaluation-control bugs. It also identified limits
on statistical and held-out claims. No model requests or GPU jobs were needed.

## What the metrics mean

Let r(t,a) be 1 for a strict pass and 0 for a graded failure. Unscorable infrastructure or
verifier failures are reported separately.

| Metric | Calculation / interpretation |
|---|---|
| `task_mean_success` — primary | Compute each task's mean over its scored attempts, then average the task means. Each task receives equal weight. |
| `strict_success` | Total strict passes / total scored attempts. Equals task-mean success when each task has the same number of scored attempts. |
| `pass@k` | Fraction of complete k-attempt tasks with at least one pass. Measures success with multiple chances, rather than single-attempt accuracy. |
| `pass^k` | Fraction of complete k-attempt tasks with all k attempts passing. Measures observed repeated reliability; it is not the overall success rate raised to k. |
| 95% task-bootstrap interval | Resample tasks, retaining each task's observed attempt mean, and take the central bootstrap percentiles. Repeated attempts on one task are not treated as separate tasks. |
| Critical violations | Counts of unsafe histories, including attempts that later repair their final state. Report alongside success. |

For example, two tasks with outcomes [pass, fail] and [pass, pass] have task-mean success
75%, pass@2 100%, and pass^2 50%. A regression test checks this example and input-order
invariance. The existing bootstrap calculation is consistent with its stated task-level scope.

## Fixed bugs

1. **Incomplete repeated-attempt metrics.** The old implementation removed unscorable
   attempts, then used the remaining outcomes under the original k label. A success plus
   an infrastructure error could appear as pass@2 success despite only one scored attempt.
   Now only tasks with every scheduled attempt scored enter pass@k/pass^k, with explicit
   complete/incomplete-task denominators. With no eligible tasks, the metric is null.
   Task-mean success remains conditional on scored attempts; coverage must accompany it.
2. **Blocked attempts counted calls.** Three rejected environment calls in one episode were
   counted as three blocked attempts. Now `blocked_attempts` counts episodes with at least
   one rejected environment call, and `blocked_tool_calls` retains the call count. Malformed
   JSON rejected by the client before environment dispatch is outside these environment-log
   counters. The old October 22 random-agent run changes from 41 blocked attempts to 36.
3. **Tool-call budget overshoot.** A model response containing multiple calls could execute
   beyond `max_tool_calls`. The runner now checks the cap before every call, and records
   `tool_call_limit` as the stop reason. Budget exhaustion remains a graded outcome.
4. **Invalid empty confidence intervals.** All-unscorable runs emitted NaN endpoints, which
   are not standard JSON numbers. They now emit null endpoints and render as n/a.
5. **Unsafe checkpoint selection.** Development summaries with missing/unscorable attempts
   could win on their remaining scored subset; even a null score could be selected when
   every candidate failed evaluation. Selection now requires a complete, fully scored run.
   It also deduplicates identical adapter configuration/weight files before evaluation.

Evaluation rejects duplicate task IDs, duplicate task/attempt records and invalid trial counts.
Missing scheduled attempts/tasks are exposed in coverage. Future run configurations record
hashes of the metric, verifier, runner and task data, plus context and nudge settings, so
historical code/schema versions can be distinguished.

## Saved-result verification

`uv run --frozen --group dev --group modal python scripts/audit_evaluation.py` reproduces
the audit without model calls. Details are in [`evaluation_audit_checks.json`](evaluation_audit_checks.json).

- **372 locally available episodes across 11 runs:** recalculated headline success,
  task-bootstrap intervals, pass@k and pass^k all match their saved summaries.
- **192 current-schema snapshots regraded.** Pass/fail decisions match. Four older scripted
  episodes gain `payment_before_receipt` critical labels under the current verifier; all four
  already failed. Historical safety labels are therefore version-specific.
- **180 pre-review snapshots** use the older task/schema and were recounted from their stored
  outcomes rather than regraded against the current suite. Their old verifier is not silently
  treated as the current verifier.
- **21 committed complete summaries**, including the v3d model baselines: task-mean success
  equals attempt success, implied success counts are integral, reliability bounds hold, and
  confidence bounds contain the point estimate. The v3d test point is still 69/96 = **71.875%**.
  Its raw Instruct episodes are not available locally, so this is an arithmetic check of its
  summary, not a new transcript-level regrade of that run.
- **275 tests pass**, including the new metric, runner, checkpoint and training regressions.
  Ruff and mypy pass.

## Process limits and how to interpret results

- **Small company sample:** the test split has 24 tasks from only four companies. Its current
  intervals resample tasks, not companies, and do not establish generalization to a broad
  population of unseen companies. Do not present 24 × 4 attempts as 96 independent tasks.
- **Previous test exposure:** the test split has been inspected during earlier prompt work.
  Freeze v3d and the evaluation settings now, select checkpoints only on dev, and label the
  resulting test comparison exploratory. A stronger final claim needs a fresh, unused test set.
- **Before/after comparison:** use the same tasks, verifier, prompt, decoding settings and
  attempt count. Report the paired per-task change and its uncertainty when both raw runs
  are available; overlapping or non-overlapping marginal intervals alone are not that test.
- **Coverage:** inference/context/tool-budget failures caused by the policy remain graded
  failures. Infrastructure and verifier failures remain unscorable. Do not publish a gain
  from a partially scored run; checkpoint selection now refuses such results.
- **Benchmark scope:** τ² uses ENV-only grading and a local customer model, so it is a
  controlled before/after comparison, not a public-leaderboard score. The saved mean rewards
  and all-four-trial rates recalculate to 36.875% / 20% for the candidate and 43.75% / 27.5%
  for the reference. The all-k reliability definition agrees with the
  [pinned upstream implementation](https://github.com/sierra-research/tau2-bench/blob/318fa35b1431a42e3ffdad05197378f506fac9d4/src/tau2/metrics/agent_metrics.py).
  BFCL uses the pinned upstream evaluator; compare only the eight executed categories.
  Its printed overall 21.68% includes unexecuted categories and is not this model's selected-
  category accuracy; this restriction was already recorded in [`external_baseline.md`](external_baseline.md).

The evaluation code is now better guarded, but these local checks do not establish that
the updated training run will improve the model or fit GPU memory at the new limits.
