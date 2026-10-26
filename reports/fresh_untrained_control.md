# Fresh untrained control with current evaluation code

Completed 2026-10-26. This reruns the original pinned base model, with no adapter, on the
24 existing test tasks × 4 attempts using prompt v3d and the current evaluation code.
It provides a current baseline for the trained model's eventual InvoiceOps test. It does
not itself evaluate the trained model.

| Metric | Original v3d baseline | Fresh untrained control |
|---|---:|---:|
| Strict passes | 69/96 | **76/96** |
| Task-mean success | 71.875% | **79.167%** |
| 95% task-bootstrap CI | 56.25%–85.42% | 66.67%–90.63% |
| pass@4 (at least one success) | 83.333% (20/24) | 95.833% (23/24) |
| pass^4 (all four successes) | 50.000% (12/24) | 58.333% (14/24) |
| Attempts with a critical violation | 1/96 | 3/96 |
| False completions | 3/96 | 3/96 |
| Infrastructure errors / missing attempts | 0 / 0 | 0 / 0 |

The new point estimate is 7.292 percentage points higher. Both runs use an untrained
model, so this difference must not be described as a training gain. Sampling and the
intervening evaluation fixes can affect comparisons; this experiment does not isolate
their contributions. The intervals overlap substantially. Keep the original result frozen
and use this fresh control as the current comparison when the trained InvoiceOps test runs.

The test split contains only four companies and has already been inspected during prompt
work. These are exploratory results on the existing test set, not an untouched new holdout.
The confidence interval resamples tasks, not companies. Per-family estimates below each
use only two tasks and eight attempts.

| Family | Original | Fresh |
|---|---:|---:|
| F01 | 100.0% | 100.0% |
| F02 | 100.0% | 87.5% |
| F03 | 75.0% | 62.5% |
| F04 | 100.0% | 100.0% |
| F05 | 87.5% | 100.0% |
| F06 | 62.5% | 100.0% |
| F07 | 100.0% | 87.5% |
| F08 | 25.0% | 50.0% |
| F09 | 50.0% | 50.0% |
| F10 | 50.0% | 62.5% |
| F11 | 75.0% | 87.5% |
| F12 | 37.5% | 62.5% |

## Effective configuration

- Model: `Qwen/Qwen3-4B-Instruct-2507`, revision
  `cdbee75f17c01a7cc42f958dc650907174af0554`, no trained adapter (`model_path` empty).
- vLLM 0.31.0 on L40S, Hermes tool parser; prompt v3d.
- Temperature 0.7, top-p 0.8; model generation defaults retain top-k 20.
- Context 131,072 tokens, at most 16,384 new tokens per turn, 40 tool calls,
  at most two continuation nudges; 16 concurrent attempts.
- Current metric, runner and verifier source hashes plus the task-data hash are saved
  in `runs/modal/test-untrained-current-v3d/config.json` and copied into the audit JSON.
- Actual maximum context: 7,985 tokens; zero truncated turns, context-limit stops,
  tool-call-limit stops, missing attempts or unscorable attempts.
- Total generated tokens: 106,450; prompt tokens across requests: 5,660,961.
- Mean tool calls: 10.656; mean attempt time: 24.06 seconds.
- Three critical violations: two overpayment proposals and one payment proposal for an
  unpayable invoice. These are scored model failures, not infrastructure errors.

## Local verification and raw outputs

All 96 unique task/attempt records were downloaded and parsed, covering exactly 24 tasks
and attempts 0–3. All 99 downloaded files matched the download manifest's recorded sizes
and SHA-256 hashes. Recomputing the summary reproduced it exactly. Replaying every saved
action against a fresh environment produced zero state-hash, observation, final-snapshot
or verifier mismatches. Regrading the saved final snapshots independently also matched.

- Result: `reports/modal/fresh_untrained_control.json`.
- Audit and per-file hashes: `reports/modal/fresh_untrained_control_audit.json`.
- All raw messages, tool events, usage, final snapshots and verifier outcomes:
  `runs/modal/test-untrained-current-v3d/episodes/` (96 files).
- Local config, summary and generated report: `runs/modal/test-untrained-current-v3d/`.
- Launcher/server log: `runs/local-logs/fresh-control.log`.
- Remote backup: funded account's `invoiceops-runs` volume,
  `/invoiceops/test-untrained-current-v3d`.

Raw directories are gitignored and retained locally. The original baseline was not overwritten.

## Account and cost

Profile `kazigalib143` (the funded account). [Modal run](https://modal.com/apps/kazigalib143/main/ap-yxXhlw9AFIKXmPgbJfkYrR).
Ledger estimate **$0.4246**, including 10.4 minutes of launcher wall time at the configured
$2.45/hour GPU rate; first-use CPU image-build time makes this an estimate, not an account
invoice. The GPU function had a 32-minute hard timeout, priced at $1.31 before launch,
within its separate $2 control allocation. Both accounts had no running containers after
completion.

The two completed evaluations together have a ledger estimate of $0.8225: $0.3979 for
trained BFCL on `invoiceops-thinking`, plus $0.4246 for this untrained control. No remaining
training, selection or external benchmark jobs were launched.

Next: select the trained checkpoint on dev, run its InvoiceOps test once under these
settings, then run τ²-bench with the original customer model and grading setup. The funded
account does not yet have the training adapters; copy the required artifacts into its
account-scoped volume and bind the evaluation budget to that profile before launching.
