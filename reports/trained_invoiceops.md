# Trained InvoiceOps test: dev-selected checkpoint 125

Completed 2026-10-26. Checkpoint 125 was selected on dev before the trained test was run
once, with 24 test tasks × 4 attempts. The primary comparator is the fresh untrained
control run with the current evaluation code, not the older frozen 69/96 baseline.

| Metric | Fresh untrained | Trained step 125 | Change |
|---|---:|---:|---:|
| Strict passes | 76/96 | **84/96** | +8 passes |
| Task-mean success | 79.167% | **87.500%** | **+8.333 pp** |
| 95% task-bootstrap CI | 66.67%–90.63% | 77.08%–96.88% | |
| pass@4 (at least one success) | 23/24 (95.833%) | 23/24 (95.833%) | unchanged |
| pass^4 (all four successes) | 14/24 (58.333%) | **18/24 (75.000%)** | +16.667 pp |
| Attempts with critical violations | 3/96 | 4/96 | +1 |
| False completions | 3/96 | 0/96 | −3 |
| Clean cases paid correctly | 50/60 | 53/60 | +3 |
| Exception cases not paid | 35/36 | 35/36 | unchanged |
| Infrastructure errors / missing attempts | 0 / 0 | 0 / 0 | |

The trained model's point estimate improved by 8.333 percentage points. A paired task
bootstrap (10,000 samples, seed 0, resampling all four attempts of each task together)
gives a 95% interval for that difference of **0 to +17.708 percentage points**. Six task
rates improved, sixteen stayed unchanged and two worsened. This small experiment does
not establish a precise or robust training effect. The test set contains four companies
and has already been inspected during prompt work; these results are exploratory.

Reliability across repeated attempts improved, but the safety picture is mixed: false
completions fell to zero while critical-violation attempts rose from three to four.
The trained run made three overpayment proposals and one proposal for an unpayable invoice.

| Family | Fresh untrained | Trained | Change (pp) |
|---|---:|---:|---:|
| F01 | 100.0% | 100.0% | +0.0 |
| F02 | 87.5% | 87.5% | +0.0 |
| F03 | 62.5% | 75.0% | +12.5 |
| F04 | 100.0% | 87.5% | -12.5 |
| F05 | 100.0% | 100.0% | +0.0 |
| F06 | 100.0% | 100.0% | +0.0 |
| F07 | 87.5% | 100.0% | +12.5 |
| F08 | 50.0% | 62.5% | +12.5 |
| F09 | 50.0% | 50.0% | +0.0 |
| F10 | 62.5% | 100.0% | +37.5 |
| F11 | 87.5% | 100.0% | +12.5 |
| F12 | 62.5% | 87.5% | +25.0 |

Per-family estimates use only two tasks and eight attempts. Shared PO capacity (F09)
remains at 50%; missing receipt/clarification (F08) is 62.5%.

## Configuration and provenance

- Base: `Qwen/Qwen3-4B-Instruct-2507` at
  `cdbee75f17c01a7cc42f958dc650907174af0554`.
- Selected adapter: `grpo-v3d/checkpoints/checkpoint-125`; SHA-256
  `451f24b51081dbe1e2779a07f30bbb2fee884291a4e948b1951f9a454aaa18f7`.
- Merged weights: `/runs/train/grpo-v3d/selected_merged` on `kazigalib143`.
  Local provenance: `reports/modal/selected-merge-provenance.json`.
- Prompt v3d, temperature 0.7, top-p 0.8, inherited top-k 20, 131,072-token context,
  16,384 output tokens per turn, 40 tool calls, two continuation nudges, concurrency 16.
- Task data and metric/runner/verifier source fingerprints match the fresh control exactly.
  Configuration fields were compared directly; see the before/after comparison JSON.
- Actual maximum context: 8,306 tokens. Zero truncated turns, context-limit stops,
  tool-call-limit stops, missing attempts or unscorable attempts.
- Generated tokens: 123,178; prompt tokens across requests: 5,823,762.
  Mean tool calls: 10.823; mean episode time: 27.90 seconds.

## Raw evidence and verification

All 99 remote files were downloaded with sizes and SHA-256 hashes recorded in the local
download manifest. All 96 unique task/attempt pairs were replayed against fresh environments:
zero state-hash, observation, final-snapshot or verifier mismatches. Independent regrading
of saved snapshots matched, and the entire summary recomputed exactly.

- All raw messages, tool calls, snapshots and verifier outcomes:
  `runs/modal/test-trained-v3d/episodes/` (96 JSON files).
- Run config, summary, report and download manifest: `runs/modal/test-trained-v3d/`.
- Result: `reports/modal/select_and_test.json` (also contains selection and transfer checks).
- Raw replay audit: `reports/modal/trained_invoiceops_audit.json`.
- Matched settings, per-task differences and paired bootstrap:
  `reports/modal/invoiceops_before_after_comparison.json`.
- Dev selection and its 96 raw episodes: `reports/checkpoint_selection.md`.
- Log: `runs/local-logs/select-and-test-grpo-v3d.log`.
- Remote backup: funded account's `invoiceops-runs`, `/invoiceops/test-trained-v3d`.
- [Modal run](https://modal.com/apps/kazigalib143/main/ap-uFLIcxSGuZo7KSidY5sHLR).

The combined dev selection, merge and trained test cost an estimated **$0.7879**
(19.3 minutes of launcher wall time at the configured $2.45/hour rate), under the
funded account's $10 post-training allocation. This is a ledger estimate, not an account
invoice. Raw directories remain gitignored and preserved locally.
