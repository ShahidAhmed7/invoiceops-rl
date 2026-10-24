# Prompt trials before training

**Question:** can a better system prompt improve the untrained candidate before any training, and which prompt should GRPO train with?

**Model:** `Qwen/Qwen3-4B-Instruct-2507` @ `cdbee75f`, temperature 0.7, top-p 0.8.

## Protocol

- **Selection data:** candidate prompts were written and chosen on the **train and dev splits only**: 36 + 12 tasks, 4 attempts each.
- **Pre-set rule:** the highest task-mean success over train and dev combined wins, provided it does not raise the critical-violation rate.
- **One test run:** only the winner was run on the test split, once.
- **What the prompts may contain:** general AP working practice only, no task-family hints. v1 and v2 stay frozen.
- **Disclosure:** the transcript audit (`reports/transcript_audit.md`) had read test transcripts. Every failure the new prompts address was confirmed on train and dev before writing them (see "Evidence" below). The fix that made v3c work came from the v3a and v3b trial transcripts on train.

## Candidates

| Prompt | Change from v2 |
|---|---|
| v3a | Search for the policy instead of guessing document ids; before `submit_case`, check that the disposition is recorded and consistent with any payment proposal. |
| v3b | v3a, plus: open every invoice attachment as evidence; write the amount arithmetic out in cents; pick the reason code whose policy conditions match, not one whose name sounds right. |
| v3c | v3a, with step 1 rewritten: search for the policy, **then open it with `get_document` and read all of it**; a search result shows only the title. |

The prompt texts are in `src/invoiceops/agents/prompts/system_v3*.md`.

## Train and dev results

| Prompt | Train + dev | Train (95% CI) | Dev | Attempts with a critical violation | False completions | Train tasks mixed / always pass / never pass | Mean tool calls |
|---|---|---|---|---|---|---|---|
| v2 | **44.8%** | 43.8% (31.2%–56.2%) | 47.9% | 20.3% | 63 | 19 / 8 / 9 | 12.2 |
| v3a | **34.4%** | 36.8% (22.9%–50.7%) | 27.1% | 41.1% | 17 | 8 / 10 / 18 | 10.0 |
| v3b | **28.6%** | 26.4% (15.3%–39.6%) | 35.4% | 44.8% | 17 | 9 / 6 / 21 | 9.7 |
| v3c | **69.3%** | 70.1% (58.3%–80.6%) | 66.7% | 10.4% | 11 | 14 / 18 / 4 | 10.4 |

### What happened

**v3a and v3b fixed one failure and caused a worse one.**
- The disposition check worked: false completions fell from 63 to 17.
- But told to search for the policy instead of guessing its id, the model treated the search hit (a title) as the policy and **never opened it**. Policy reads on train fell from 143/144 attempts (v2) to 89 (v3a) and 55 (v3b).
- Without the rules, it paid invoices it should have held: payment proposed on 36 of 60 hold or reject training attempts, against 13 for v2. Critical violations doubled.
- Under v2, the failed id guess had forced a search followed by a `get_document`. That "wasted" call was what made the model read the policy.

**v3c restores the policy read and keeps the disposition check.**
- It scores 69.3% on train and dev, against 44.8% for v2.
- Critical violations are halved, and false completions fall from 63 to 11.

### Evidence on train and dev, prompt v2

These failures were confirmed on train and dev before the variants were written:

| Failure | Train (144 attempts) | Dev (48) |
|---|---|---|
| proposed payment but never recorded a disposition | 41 | 13 |
| guessed a policy document id | 143 | 47 |
| wrong hold reason code | 10 | 4 |
| paid without required approval | 6 | 0 |
| wrong amount | 9 | 0 |
| invoice attachment left unopened | 12 of 20 | 8 of 8 |

## Test split: the single run of the winner

| Agent | Task-mean success | 95% CI | pass@4 | pass^4 | Critical violations | False completions |
|---|---|---|---|---|---|---|
| Untrained 4B, prompt v2 | **41.7%** | 28.1%–55.2% | 70.8% | 12.5% | 17 / 96 | 27 / 96 |
| **Untrained 4B, prompt v3c** | **72.9%** | 56.2%–87.5% | 79.2% | 54.2% | 3 / 96 | 2 / 96 |
| Reference 30B-A3B FP8, prompt v2 | **61.5%** | 43.8%–78.1% | 70.8% | 50.0% | 23 / 96 | 0 / 96 |

With v3c, the untrained 4B also scores above the 30B reference model under v2.

| Family | v2 | v3c |
|---|---|---|
| F01 Clean match | 50.0% | 87.5% |
| F02 Price discrepancy | 75.0% | 87.5% |
| F03 Short receipt | 12.5% | 87.5% |
| F04 Duplicate invoice | 100.0% | 100.0% |
| F05 Credit note | 25.0% | 100.0% |
| F06 Approval routing | 0.0% | 87.5% |
| F07 Vendor-detail conflict | 87.5% | 87.5% |
| F08 Missing receipt and clarification | 25.0% | 0.0% |
| F09 Shared PO capacity | 25.0% | 50.0% |
| F10 Untrusted document instructions | 37.5% | 50.0% |
| F11 Transient tool failure | 37.5% | 87.5% |
| F12 Stale policy and amended records | 25.0% | 50.0% |

**New weakness: missing receipt (F08) at 0%.**
- In 6 of 8 attempts the model asks receiving for the receipt, puts the invoice on hold, and submits **without checking the inbox** for the reply.
- The policy says to finish the case once the receipt arrives.
- Under v3c this family is also lower on train (42%, against 50% for v2).
- This was found on the test split, so it was **not** used to tune another prompt. A further prompt round would have to be designed and selected on train and dev only, and its test number would be a second look at the test split.

## Recommendation for training

- **The bar to beat is now 72.9% on test**, from prompt engineering alone. The trained model has to beat this, not v2's 41.7%.
- **Training with v3c starts from the strongest behaviour.** On train it leaves 14 tasks with mixed outcomes, 18 that always pass, and 4 that never pass. That is fewer learnable tasks than v2's 19, but the 144 generated training variants add more, and the remaining failures are where GRPO's signal will go: F03, F08, F09.
- **If training uses v3c,** `select_checkpoint` and `select_and_test` must evaluate with v3c too. They currently use v1.

## Cost

| Job | Ledger cost |
|---|---|
| prompt_trial v3a | $0.38 |
| prompt_trial v3b | $0.39 |
| prompt_trial v3c | $0.49 |
| test_prompt v3c | $0.25 |
