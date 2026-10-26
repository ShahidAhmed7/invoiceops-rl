# BFCL after training: final step 150

Completed 2026-10-26. The final `grpo-v3d/final_adapter` was merged into the pinned
`Qwen/Qwen3-4B-Instruct-2507` base and evaluated on all 2,751 cases across the same eight
BFCL categories as the frozen untrained baseline. **This is the final checkpoint, not a
dev-selected checkpoint.** No development selection has run yet.

| Category | Untrained | Trained final | Change (percentage points) |
|---|---:|---:|---:|
| `simple_python` | 95.25% | 95.50% | +0.25 |
| `multiple` | 94.50% | 94.00% | -0.50 |
| `parallel` | 93.00% | 92.50% | -0.50 |
| `parallel_multiple` | 90.00% | 89.50% | -0.50 |
| `irrelevance` | 88.75% | 88.75% | +0.00 |
| `live_simple` | 78.29% | 79.07% | +0.78 |
| `live_multiple` | 76.83% | 77.11% | +0.28 |
| `multi_turn_base` | 27.00% | 27.50% | +0.50 |

The differences are small and mixed (−0.50 to +0.78 percentage points). This run shows no
large loss of general tool-calling accuracy on these categories. It does not establish a
statistically reliable improvement or measure the InvoiceOps training gain. Compare these
category scores; BFCL's printed Overall and Multi Turn Overall include unrun categories as
zeros and must not be reported as our aggregate scores.

## Reproducibility and provenance

- Base revision: `cdbee75f17c01a7cc42f958dc650907174af0554`.
- Adapter SHA-256: `9f5ef7e8e82447411d601a562e3c217343bfa905a346aac8b6b4529207f1baec`,
  matched against the local final adapter before interpreting scores.
- Served weights: `/runs/train/grpo-v3d/final_merged`; the served model name remains the
  base model's BFCL handler name. `merge_provenance.json` identifies the actual trained weights.
- BFCL `2026.3.23`, handler `Qwen/Qwen3-4B-Instruct-2507-FC`, vLLM `0.31.0`, L40S,
  Hermes parser, 16 threads, 131,072-token context, BFCL's 4,096-token output limit.
- Requested temperature 0.001, matching the baseline command. The current server log confirms
  vLLM clamps this to 0.01; the baseline used the same vLLM version and requested setting.
- Job: `bfcl_after`, account profile `invoiceops-thinking` (workspace `nonestop220`).
- [Modal run](https://modal.com/apps/nonestop220/main/ap-TFpvVidRDfsiqU8hfyhcGM).
- Ledger estimate: $0.3979 (9.7 minutes at the configured $2.45/hour rate). This includes
  launcher wall time; it is an estimate, not a reconciled account invoice.
- Shared hard timeout: 7 minutes for merge plus 28 minutes for BFCL, priced at $1.43
  before launch, within the separate $2 account allocation.

## Artifacts

- Committed result and score CSV contents: `reports/modal/bfcl_after.json`.
- Frozen before result: `reports/modal/bfcl_before.json` and `reports/external_baseline.md`.
- Full local raw outputs, score CSVs, error analyses and configuration:
  `runs/modal/bfcl-after-final-step150/`.
- Local merge provenance: `runs/modal/bfcl-final-merge-provenance.json`.
- Full launcher/server log: `runs/local-logs/bfcl-after-final.log`.
- Raw files remain on this account's `invoiceops-runs` volume under
  `/bfcl/after-final-step150`; merged weights under `/train/grpo-v3d/final_merged`.

The raw directories are gitignored. Keep them on disk; do not substitute CSV summaries
for the raw generated results when reproducing or auditing this evaluation.

Local audit (`reports/modal/bfcl_after_audit.json`) verified all 82 downloaded files
against the download manifest's sizes and SHA-256 hashes, 2,751 unique generated case IDs,
and the per-category score denominators and correct-count arithmetic. There are 400
simple-Python, 200 multiple, 200 parallel, 200 parallel-multiple, 240 irrelevance, 258
live-simple, 1,053 live-multiple and 200 multi-turn-base cases.
