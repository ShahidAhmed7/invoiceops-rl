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

| v3d | v3c, plus: after any clarification or approval request, check the inbox and act on the reply before finishing; compare a payment with the policy's approval limits before proposing it; where the policy says what to do, do exactly that even when it differs from common practice. |

| v4 | A fresh prompt in company style, with no model patches: an AP practice guide (policy decides, three-way match, exact amounts, approval limits, follow up on replies, record decisions separately from payment requests) plus a short guide to the AP system. It has no numbered procedure, and none of the lines written to fix model mistakes. |

The prompt texts are in `src/invoiceops/agents/prompts/system_v3*.md` and `system_v4.md`.

## Train and dev results

| Prompt | Train + dev | Train (95% CI) | Dev | Attempts with a critical violation | False completions | Train tasks mixed / always pass / never pass | Mean tool calls |
|---|---|---|---|---|---|---|---|
| v2 | **44.8%** | 43.8% (31.2%–56.2%) | 47.9% | 20.3% | 63 | 19 / 8 / 9 | 12.2 |
| v3a | **34.4%** | 36.8% (22.9%–50.7%) | 27.1% | 41.1% | 17 | 8 / 10 / 18 | 10.0 |
| v3b | **28.6%** | 26.4% (15.3%–39.6%) | 35.4% | 44.8% | 17 | 9 / 6 / 21 | 9.7 |
| v3c | **69.3%** | 70.1% (58.3%–80.6%) | 66.7% | 10.4% | 11 | 14 / 18 / 4 | 10.4 |
| v3d | **78.1%** | 75.0% (64.6%–84.7%) | 87.5% | 6.8% | 6 | 16 / 18 / 2 | 10.7 |
| v4 | **40.6%** | 40.3% (25.0%–55.6%) | 41.7% | 55.7% | 8 | 4 / 13 / 19 | 11.9 |

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

## Second round: v3d (train and dev evidence only)

v3d targets v3c's train and dev failures:
- asked someone but never checked the inbox: 14 train, 3 dev attempts;
- applied a generic receipt rule instead of the company's: 16 and 3;
- paid without the required approval: 5 and 4.

The rule, set before the run, was to beat v3c on train and dev without raising the critical-violation rate.

**Result on train and dev:** 78.1% against 69.3%, critical violations 6.8% against 10.4%. Missing receipt on train rose from 42% to 75%, approval routing from 50% to 67%.

**Its test run, a second look at the test split:**

| Agent | Task-mean success | 95% CI | pass@4 | pass^4 | Critical violations | False completions |
|---|---|---|---|---|---|---|
| Untrained 4B, prompt v3c | 72.9% | 56.2%–87.5% | 79.2% | 54.2% | 3 / 96 | 2 / 96 |
| Untrained 4B, prompt v3d | 71.9% | 56.2%–85.4% | 83.3% | 50.0% | 1 / 96 | 3 / 96 |

**The 9-point gain on train and dev did not carry over to test.** v3d and v3c are within a point of each other there. After several rounds of choosing prompts on train and dev, part of that gain is selection noise.
- v3d is safer: 1 critical violation against 3.
- It does better on missing receipt (25% against 0%) but worse on stale policy (37.5% against 50%).

**Prompt engineering has plateaued at about 72–73% on test.** A further round is unlikely to show a real gain without many more tasks.

## Company-style prompt without model patches: v4 (train and dev only)

**Question:** how much of the gain comes from realistic company guidance, and how much from lines written to patch model mistakes? v4 was written as what a company would hand a new AP clerk, and was not given a test run.

**Result: 40.6% on train and dev, about the same as v2 (44.8%), and the most dangerous prompt tested.** 55.7% of attempts had a critical violation: 52 payments proposed on invoices that should not be paid, 11 overpayments, and 16 payments without required approval on train, against 13, 8 and 6 for v2.

The transcripts replay exactly (192 of 192). What they show:
- **The model reads the policy but does not check the records against it.** It opened the policy in 142 of 144 training attempts, yet paid 52 of the 60 attempts that should be held or rejected. It called no `request_approval` in 144 attempts, although v4 states that large payments need approval.
- **It acts without checking.** On `T-02FF9D` the invoice price is $118.72 per case against the PO's $112.00, a 6% variance. The model wrote "the quantities and prices align exactly", then paid.
- **The order of work changed.** Under v4 the model read the policy after gathering the records in all 144 attempts (v2: 12 of 144, v3c: 0), then decided at once. Within v2, though, reading order alone does not predict success, so it is not the whole explanation.

**Reading.** The patch lines are only part of the story. v4 also drops v2's **numbered procedure**: "apply the policy's checks in the order it gives", and "propose a payment only when the policy allows it". It describes good practice instead of prescribing an order of work, and the 4B model then gathers records and approves by default.

For this model, **a step-by-step procedure matters more than realistic wording.** The v3 prompts' gain over v2 comes from the procedure plus the patches, not from AP knowledge the model lacked. A one-line ablation (v4 plus "work through the policy's checks one by one, in the order it gives, before deciding") would test the procedure explanation directly.

## Selected prompt and completed RL experiment

**v3d was selected** for its train/dev score and lower critical-violation rate. It left
16 fixed training tasks with mixed outcomes and two that never passed; 144 generated
training variants supplemented the 36 fixed tasks. Training, checkpoint selection and
the final InvoiceOps evaluation all used v3d.

The current untrained v3d evaluation scored **76/96 (79.167%)**, compared with the
initial v1 result of **7/96 (7.292%)**. The dev-selected RL checkpoint then scored
**84/96 (87.500%)** with v3d, an additional **8.333 points** over the matched untrained
control. Source results above remain frozen; see the [statistical analysis](statistical_analysis.md)
for the three-stage comparison and paired RL inference.

## Cost

| Job | Ledger cost |
|---|---|
| prompt_trial v3a | $0.38 |
| prompt_trial v3b | $0.39 |
| prompt_trial v3c | $0.49 |
| test_prompt v3c | $0.25 |
| prompt_trial v3d | $0.48 |
| test_prompt v3d | $0.25 |
| prompt_trial v4 | $0.43 |
| **All prompt trials** | **$2.67** |
