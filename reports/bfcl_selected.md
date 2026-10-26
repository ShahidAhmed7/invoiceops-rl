# BFCL: dev-selected checkpoint 125 versus untrained

Completed 2026-10-26 on the first/low-credit account (`invoiceops-thinking`, workspace
`nonestop220`). This is the full planned BFCL subset: **2,751 cases across all eight
baseline categories**, with no case limit. It evaluates the same dev-selected checkpoint
125 used for the trained InvoiceOps test and tau2. No checkpoint was selected or changed
using BFCL scores.

| Category | Untrained | Selected step 125 | Selected change (pp) | Earlier final step 150 |
|---|---:|---:|---:|---:|
| `simple_python` | 95.25% | **95.00%** | -0.25 | 95.50% |
| `multiple` | 94.50% | **93.50%** | -1.00 | 94.00% |
| `parallel` | 93.00% | **92.50%** | -0.50 | 92.50% |
| `parallel_multiple` | 90.00% | **89.50%** | -0.50 | 89.50% |
| `irrelevance` | 88.75% | **88.75%** | +0.00 | 88.75% |
| `live_simple` | 78.29% | **78.68%** | +0.39 | 79.07% |
| `live_multiple` | 76.83% | **77.21%** | +0.38 | 77.11% |
| `multi_turn_base` | 27.00% | **25.50%** | -1.50 | 27.50% |

Selected-checkpoint changes are small and mostly negative: five categories declined,
two improved, one stayed unchanged. Multi-turn declined from 54/200 to 51/200 passes
(−1.5 percentage points). This run does not show a general BFCL improvement from training,
and does not establish a statistically reliable regression either. The earlier step-150
run remains a separately labelled diagnostic, not the selected model's result.

Do not quote BFCL's printed Overall or Multi Turn Overall: they include unexecuted categories
as zeros. This run covers every case in our planned eight categories, not every category
in the entire BFCL benchmark.

## Matched settings and verified provenance

- Pinned base: `Qwen/Qwen3-4B-Instruct-2507` at
  `cdbee75f17c01a7cc42f958dc650907174af0554`.
- Adapter: `grpo-v3d/checkpoints/checkpoint-125`, SHA-256
  `451f24b51081dbe1e2779a07f30bbb2fee884291a4e948b1951f9a454aaa18f7`.
- The launcher checked the local selection decision and fully scored dev summary, then
  required the first account's adapter hash to match before merging. Merge provenance on
  both accounts is identical (same adapter, checkpoint and pinned base).
- First-account weights: `/runs/train/grpo-v3d/selected_merged`, served under the base
  model's standard BFCL handler name. Local provenance is
  `reports/modal/bfcl-selected-merge-provenance.json`.
- BFCL 2026.3.23, handler `Qwen/Qwen3-4B-Instruct-2507-FC`, vLLM 0.31.0,
  L40S, Hermes parser, 16 threads, 131,072 context, BFCL's 4,096-token output limit.
- Requested temperature 0.001; vLLM clamps it to 0.01. The original baseline used the
  same requested value and vLLM version. Benchmark prompts and decoding were not retuned.

## Raw outputs and audit

All 82 remote files were saved locally, including every generated result, multi-turn
inference log, category error analysis, score CSV and evaluation config. File sizes and
SHA-256 hashes match the download manifest. The audit verified **2,751 unique case IDs**,
all eight category denominators, correct-count/accuracy arithmetic and selected provenance.

- Result: `reports/modal/bfcl_selected.json`.
- Audit and raw artifact hashes: `reports/modal/bfcl_selected_audit.json`.
- Full local raw directory: `runs/modal/bfcl-selected-checkpoint-125/`.
- Remote backup: first account's `invoiceops-runs`, `/bfcl/after-selected-checkpoint-125`.
- Log: `runs/local-logs/bfcl-selected-checkpoint-125.log`.
- [Modal run](https://modal.com/apps/nonestop220/main/ap-kUmTaE2VbE3buoPiVarehc).
- Ledger estimate: **$0.4420**, 10.8 minutes at the configured $2.45/hour rate. The
  dedicated account allocation is $2.50; the shared merge/eval hard timeout is 35 minutes
  (7 + 28), priced at $1.43 before launch. This is an estimate, not an account invoice.

Raw directories are gitignored and retained locally. The original untrained and step-150
result files were not overwritten.
