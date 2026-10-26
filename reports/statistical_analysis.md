# Statistical analysis of the completed experiment

This analysis reports observed effects, uncertainty and sensitivity checks for the
dev-selected step-125 adapter. Every successful and unsuccessful attempt remains in the
data. Primary inference compares the selected-prompt untrained model with the trained
model using identical task data, prompt, decoding and evaluation-source fingerprints.

## Initial prompt, selected prompt, and RL

| Configuration | Prompt | Passes | Strict success |
|---|---|---:|---:|
| Initial prompt | v1 | 7/96 | 7.292% |
| Selected prompt | v3d | 76/96 | 79.167% |
| Selected prompt + RL | v3d | 84/96 | 87.500% |

The initial-to-selected prompt comparison is +71.875 percentage points. The additional
matched RL comparison is +8.333 points. Prompt source texts and the complete sequence of
selection experiments are retained in `reports/prompt_trials.md`; the three stage counts
and their source files are recorded in `reports/statistics/analysis.json`.

## Effect sizes and paired inference

| Outcome | Untrained | Trained | Δ (pp) | 95% paired-task interval (pp) | Exact two-sided p |
|---|---:|---:|---:|---:|---:|
| InvoiceOps strict success | 79.167% | 87.500% | +8.333 | [+0.000, +17.708] | 0.140625 |
| InvoiceOps all four attempts | 58.333% | 75.000% | +16.667 | [+0.000, +37.500] | 0.218750 |
| τ² mean reward | 36.875% | 38.750% | +1.875 | [-6.250, +10.000] | 0.766815 |
| τ² all four trials | 20.000% | 22.500% | +2.500 | [-7.500, +12.500] | 1.000000 |

These are exploratory, post hoc analyses of completed runs. The InvoiceOps primary
endpoint was strict verifier success; secondary p-values are unadjusted and not
confirmatory. No reported RL or external effect is statistically significant at 0.05.

### What the positive domain effect means

- Success: **76/96 → 84/96**, eight additional successful attempts, +8.333 percentage points.
- Failures: **20 → 12**, a **40% relative reduction in the observed failure count**.
  This is a descriptive relative effect, not a 40-point accuracy gain.
- Repeat reliability: **14/24 → 18/24** tasks pass every attempt. Five tasks gain that
  consistency and one loses it; exact McNemar p = 0.218750.
- At-least-one success: **23/24 → 23/24**, unchanged. Training improved repeat execution
  on the sampled tasks, not the count of tasks solved at least once.
- Six task-level success rates improve, sixteen stay equal and two worsen. Every outcome
  is included rather than reporting only the improved tasks.

## Resampling and test definitions

**Bootstrap.** For each endpoint, resample paired task indices with replacement, keeping
both models and all four attempts together. Compute each model mean and their difference
in every resample. Use 100,000 draws from NumPy `default_rng(0)` and the 2.5th/97.5th
empirical percentiles (`method='inverted_cdf'`). InvoiceOps uses 24 task clusters; tau2
uses 40. These higher-resample intervals are generated directly for the figures; older
run summaries retain their original smaller-bootstrap intervals and unchanged point estimates.

**Exact paired sign-flip test.** Let d_i be the trained minus untrained number of successes
on task i. Under the exchangeable/symmetric paired null, enumerate the distribution of
sum(s_i d_i), for independent signs s_i in {-1,+1}. The two-sided p-value includes all
assignments with absolute sum at least the observed absolute sum. Zero differences do
not add information. A dynamic program enumerates the exact distribution: the primary
effect has 8 nonzero pairs, 256 assignments, and 36 extreme assignments (p = 0.140625).
The tau2 mean has 18 nonzero pairs and 262,144 assignments (p = 0.766815).

**Reliability.** Convert each task to a binary indicator for all four attempts succeeding.
Use the exact conditional binomial/McNemar test on gained and lost indicators. We do not
pair individual stochastic attempt indices or treat repeated attempts as independent tasks.

Task-level inference assumes tasks are suitable exchangeable units. Because InvoiceOps
tasks share companies, the company sensitivity below is essential; 24 tasks are not 24
independent companies. Neither the bootstrap nor a small p-value would repair prior test
inspection or establish a randomized causal experiment.

## Company sensitivity

Each of the four test companies contributes six tasks and 24 attempts.

| Company | Untrained passes | Trained passes | Company Δ (pp) | Δ omitting company (pp) |
|---|---:|---:|---:|---:|
| Glimmerdale Labware | 18/24 | 18/24 | +0.000 | +11.111 |
| Juniper Fold Logistics | 15/24 | 19/24 | +16.667 | +5.556 |
| Marrowind Energy Services | 22/24 | 23/24 | +4.167 | +9.722 |
| Pellucid Print Works | 21/24 | 24/24 | +12.500 | +6.944 |

Three company means improve and one is unchanged. All four leave-one-company-out effects
are positive, from +5.556 to +11.111 points. This shows that the observed gain is not
entirely dependent on one company. It does not supply four independent confirmations:
the company-level exact sign-flip test has only three nonzero company differences and
eight assignments, giving **p = 0.250**. Four companies are too few for a precise
population-level generalization claim. We do not promote a small-cluster percentile
interval into a significance claim.

## Family-level description

| Family | Untrained | Trained | Change (pp) |
|---|---:|---:|---:|
| F01 · Clean match | 100.0% | 100.0% | +0.0 |
| F02 · Price discrepancy | 87.5% | 87.5% | +0.0 |
| F03 · Short receipt | 62.5% | 75.0% | +12.5 |
| F04 · Duplicate invoice | 100.0% | 87.5% | -12.5 |
| F05 · Credit note | 100.0% | 100.0% | +0.0 |
| F06 · Approval routing | 100.0% | 100.0% | +0.0 |
| F07 · Vendor-detail conflict | 87.5% | 100.0% | +12.5 |
| F08 · Missing receipt and clarification | 50.0% | 62.5% | +12.5 |
| F09 · Shared purchase-order capacity | 50.0% | 50.0% | +0.0 |
| F10 · Untrusted document instructions | 62.5% | 100.0% | +37.5 |
| F11 · Transient tool failure | 87.5% | 100.0% | +12.5 |
| F12 · Stale policy and amended records | 62.5% | 87.5% | +25.0 |

Six families improve, five are unchanged and one declines. Each row has only two tasks
and eight attempts, so no family-level significance tests are reported. F10 attachments
were opened in **0/8 attempts under either model**. Its gain is scenario completion,
not demonstrated resistance to prompt injection.

## External results

The RL dataset contained InvoiceOps tasks only. Tau2 uses the same retail tasks, customer
model, seed, trial count and ENV-only grading before and after training. Its mean reward
rises by 1.875 points and all-four reliability by 2.500 points. The mean-reward interval
is -6.25 to +10.00 points and exact p is 0.766815: positive point estimates, not established
general transfer. The all-four outcome has three gained and two lost tasks (p = 1.0).

BFCL's eight executed categories contain **2,751 cases**. Summing correct cases gives
**2,214 → 2,211**, or **80.480% → 80.371%** (-0.109 points). This is a custom
executed-case micro-average, not BFCL's official Overall score. Its weights are the
numbers of cases in the executed categories; it is not a category-balanced average.
Baseline integer counts are uniquely reconstructed from published rounded category
accuracies at the known denominators, with round-trip checks in the analysis script.

Two BFCL categories improve, five decline and one is unchanged. All category effects
appear in the external figure and `reports/bfcl_selected.md`. Baseline per-case outcomes
are not available locally, so no paired case-level test or formal noninferiority claim is
made. “Largely retained” describes the observed scores, not a proven statistical margin.

## Behavior and cost checks

- False completions: **3 → 0**. Critical-violation attempts: **3 → 4**. The results do
  not establish a safety improvement; sparse events cannot support strong rate claims.
- Mean tool calls: **10.656 → 10.823**. Mean seconds per attempt: **24.06 → 27.90**.
  Completion tokens: **106,450 → 123,178**. No speed or token-efficiency improvement is claimed.
- No InvoiceOps infrastructure errors, missing attempts, context-limit stops or truncated
  turns. All 96 trained and 96 control traces replay exactly.
- Tau2 has all 160 rewarded trials, including one max-step trajectory retained as a zero.
  Its standard ENV-only grading is narrower than full conversational correctness.

## Reproduction and source integrity

```bash
uv run --frozen --group analysis python scripts/analyze_results.py
```

The included `reports/statistics/paired_observations.json` holds the 24 task IDs,
company/family labels, all four binary outcomes per model, source episode hashes, matching
task/evaluation fingerprints and selected adapter provenance. It was extracted from the
previously audited raw records, not reconstructed from the headline success rate. Tau2
uses its per-task means; BFCL uses its category CSVs and audited denominators.

To re-extract the compact observations from the full local trajectories:

```bash
uv run --frozen --group analysis python scripts/analyze_results.py --refresh-observations
```

The standard command works without raw trajectories or model APIs. JSON statistics and
all SVG/PNG figures are regenerated deterministically from the included data and locked
analysis dependencies. Figures retain zero reference lines and show uncertainty or all
evaluated categories where applicable. The complete evaluated model is checkpoint 125,
with the same adapter SHA-256 across InvoiceOps, BFCL and tau2.
