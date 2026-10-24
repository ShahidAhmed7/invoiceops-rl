# Baseline

The untrained candidate on the 24 held-out test tasks: two tasks per family, 4 attempts each, temperature 0.7, top-p 0.8, at most 40 tool calls per attempt.
- **Model:** `Qwen/Qwen3-4B-Instruct-2507` at revision `cdbee75f17c01a7cc42f958dc650907174af0554`, served by vLLM 0.31.0 on an L40S.
- **Lengths:** 131,072-token context and up to 16,384 new tokens per turn (see `reports/compatibility.md`).
- **Source:** `reports/modal/test_candidate.json`, job `test_candidate`.

Success is strict: an attempt passes only if every verifier check passes. Task-mean success averages each task's pass rate over the 24 tasks. The 95% confidence interval is a bootstrap over tasks.

## Test split

| Agent | Prompt | Task-mean success | 95% CI | pass@4 | pass^4 |
|---|---|---|---|---|---|
| Untrained candidate (4B) | v1 | 7.3% | 1.0%–15.6% | 16.7% | 0.0% |
| Untrained candidate (4B) | v2 | 41.7% | 28.1%–55.2% | 70.8% | 12.5% |
| Untrained candidate (4B) | v3c | 72.9% | 56.2%–87.5% | 79.2% | 54.2% |
| Reference model (30B-A3B FP8) | v1 | not run | | | |
| Reference model (30B-A3B FP8) | v2 | 61.5% | 43.8%–78.1% | 70.8% | 50.0% |

| | v1 | v2 |
|---|---|---|
| Attempts with a critical violation | 30 / 96 | 17 / 96 |
| False completions (submitted a status or amount the system does not show, and failed) | 43 / 96 | 27 / 96 |
| Exception cases not paid | 9/36 | 31/36 |
| Clean cases paid correctly | 7/60 | 19/60 |
| Mean tool calls per attempt | 10.4 | 12.5 |
| Mean seconds per attempt | 12.2 | 21.9 |
| Largest context reached (tokens) | 7,133 | 8,411 |
| Turns truncated / context-limit stops | 0 / 0 | 0 / 0 |
| Unscorable attempts | 0 | 0 |

### Per family (task-mean success; 2 tasks × 4 attempts each)

| Family | v1 | v2 |
|---|---|---|
| F01 Clean match | 62.5% | 50.0% |
| F02 Price discrepancy | 0.0% | 75.0% |
| F03 Short receipt | 0.0% | 12.5% |
| F04 Duplicate invoice | 0.0% | 100.0% |
| F05 Credit note | 0.0% | 25.0% |
| F06 Approval routing | 0.0% | 0.0% |
| F07 Vendor-detail conflict | 0.0% | 87.5% |
| F08 Missing receipt and clarification | 0.0% | 25.0% |
| F09 Shared PO capacity | 12.5% | 25.0% |
| F10 Untrusted document instructions | 12.5% | 37.5% |
| F11 Transient tool failure | 0.0% | 37.5% |
| F12 Stale policy and amended records | 0.0% | 25.0% |

### Critical violations (count over 96 attempts)

| Violation | v1 | v2 |
|---|---|---|
| `overpayment_proposed` | 14 | 9 |
| `payment_proposed_for_unpayable_invoice` | 12 | 5 |
| `payment_without_required_approval` | 4 | 3 |

## Reading

- **Prompt v3c is the prompt-engineered baseline: 72.9% on test.** It was chosen on train and dev before its single test run; see `reports/prompt_trials.md`.

- **v2 is the stronger baseline: 41.7% against 7.3% for v1.** The confidence intervals do not overlap. v2 is the frozen prompt that adds general AP working practice, with no task-family hints.
- **v1 rarely completes a case correctly.** It has 43 false completions (a submission whose status or amount the system does not show), and pays only 7/60 clean cases correctly. Overpayment is its most frequent critical violation.
- **Scripted agents on the same test split:** always-pay scores 29.2%, always-hold 8.3%, and doing nothing 0% (`README.md`). Untrained v1 scores below always-pay; v2 is above it.
- **The reference model (`Qwen/Qwen3-30B-A3B-Instruct-2507-FP8` @ `5a5a776`, H100, prompt v2) scores 61.5%.** It has 0 false completions and 23 / 96 attempts with a critical violation (overpayment_proposed 4, payment_proposed_for_unpayable_invoice 11, payment_without_required_approval 8). It never asks for approval, and scores 0% on approval routing (F06) and short receipts (F03); see `reports/transcript_audit.md` §8. Source: `reports/modal/test_reference.json`.
- **With 2 tasks per family, the per-family figures are indicative only.**
- **This audit does not yet cover transcripts.** The audit so far rests on the committed summaries: counts, consistency between metrics, and lengths. Transcript-level review waits on downloads from the Modal volume, which this session's network policy blocks (`*.modal-storage.com`).
