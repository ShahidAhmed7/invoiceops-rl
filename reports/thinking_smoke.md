# Thinking-2507 inference smoke — 2026-10-26 (Asia/Dhaka)

The inference pipeline passed. Strict task success was **8/12 (66.7%)**, with zero critical
violations, zero infrastructure errors, zero truncated turns, and zero context-limit stops.
This is a development-only pipeline and token-budget check, not a held-out benchmark or a
training experiment. The active candidate remains Instruct-2507.

## Configuration and scope

- Model: `Qwen/Qwen3-4B-Thinking-2507`, revision `768f209d9ea81521153ed38c47d515654e938aea`.
- Prompt: `v3d`; all 12 dev tasks, one attempt each (one task per family).
- Temperature 0.6, top-p 0.95, top-k 20; no separate thinking-token budget.
- Maximum output 32,768 tokens per turn; context 131,072; concurrency 4.
- vLLM 0.31.0, bf16, L40S, Hermes tool parser plus `qwen3` reasoning parser.
- GPU function hard timeout: 20 minutes. It completed before that timeout.
- [Modal run](https://modal.com/apps/nonestop220/main/ap-hPAYMdFmg3zFRDS3k26qDM).
- The two-tool round trip passed in 4.47 s, with correct names and
  arguments, 316 reasoning tokens and
  365 total generated tokens.

## Length and latency measurements

These distributions cover all 121 model turns in the 12 dev episodes; they exclude
the preliminary two-tool round trip. Reasoning text was counted using the pinned model's
tokenizer. Parsed reasoning is not re-sent in message history.

| Per-turn metric | Mean | Median | P95 | Maximum |
|---|---:|---:|---:|---:|
| Reasoning tokens | 1,399.9 | 830 | 4,163 | 5,894 |
| Total generated tokens, including reasoning | 1,458.1 | 934 | 4,265 | 5,922 |
| Request latency, seconds | 23.1 | 13.8 | 67.2 | 93.4 |

- Largest prompt plus current completion: **12,299 tokens**.
- Total generation: **176,429 tokens**, including **169,382 reasoning tokens**
  (96.0% of generation).
- Mean generation per episode: **14,702.4 tokens**.
- Mean episode latency: **233.3 s**; maximum
  343.6 s. Episodes run concurrently, so their times must not be
  added to estimate elapsed wall clock.
- Model-server startup: 250.1 s. Function work before final teardown:
  18.95 min. Launcher wall clock including image builds:
  23.60 min.

The 16,384-token per-turn cap would have been above every observed turn. The larger
32,768 allowance was not approached. The 131,072 context was also comfortably above the
observed maximum. This does not guarantee that a larger sample cannot produce a longer tail.

**Training has a different limit.** Four episodes generated more than 16,384 tokens across
all turns even before tool results. Adding tokenized tool-response text puts
**5/12** above that length, excluding template overhead.
The current 16,384-token whole-rollout GRPO budget therefore needs a fresh review before
training this thinking checkpoint. These are inference-derived lower bounds, not measured
TRL rollouts; see `modal/smoke_thinking_rollout_lengths.json`.

## Accuracy and comparison

| Model | Dev attempts | Strict success | Mean generated tokens per episode |
|---|---:|---:|---:|
| Instruct-2507, v3d (existing baseline) | 12 × 4 | 87.5% | 1,172.7 |
| Thinking-2507, v3d (this smoke) | 12 × 1 | 66.7% | 14,702.4 |

The thinking smoke used **12.54×** as many generated tokens per episode. Its
observed accuracy did not improve on the existing baseline. Attempts, decoding settings,
and concurrency differ (instruct used 16 concurrent episodes; thinking used 4), and this
small smoke is not sufficient to establish a statistically reliable ranking or a matched
latency comparison. Thinking's task-bootstrap 95% interval is 41.7–91.7%.

Failures were workflow and evidence omissions, not output-budget failures:
- F01 and F10: submitted a payable case without creating the payment proposal and completing
  the approval follow-up.
- F09: omitted the required corrected-invoice request to the supplier.
- F06: omitted the target invoice from the disposition evidence.

| Family | Task | Result | Generated tokens | Seconds | Failed checks |
|---|---|---|---:|---:|---|
| F03 | T-0222C3 | pass | 12,462 | 201.6 | — |
| F08 | T-71E1D2 | pass | 8,931 | 143.6 | — |
| F04 | T-84D47B | pass | 21,235 | 343.6 | — |
| F01 | T-8F0E1E | fail | 12,681 | 205.2 | submission_consistent, payment_amount, approval_before_payment |
| F05 | T-9362E5 | pass | 13,159 | 212.5 | — |
| F07 | T-A680BE | pass | 13,760 | 221.1 | — |
| F11 | T-C45901 | pass | 14,642 | 235.2 | — |
| F09 | T-CC052D | fail | 17,333 | 279.8 | clarification_to_supplier |
| F02 | T-D30567 | pass | 11,920 | 190.4 | — |
| F06 | T-DC7A6B | fail | 10,190 | 166.7 | disposition_evidence |
| F10 | T-E72409 | fail | 18,353 | 282.0 | submission_consistent, payment_amount, approval_before_payment |
| F12 | T-F88990 | pass | 21,763 | 317.8 | — |

## Reproduction and accounting

Credentials are held only in the ignored local `.env` and private Modal configuration, using
profile `invoiceops-thinking`. The owner reported USD 26 credit on this second account; its
live billing balance was not read. The launcher records the account profile on new ledger
entries. No historical ledger entries were changed.

```bash
uv run --frozen --group modal --env-file .env python -m modal_app.launch smoke_thinking --rerun --dry-run
```

The completed job cannot be launched again without `--rerun`. No additional runs were made.
The overall USD 50 budget and USD 11 released-spend limit remain unchanged. The new USD 0.85
job allocation reduces the unallocated reserve; runtime job caps sum to USD 44.55.

Ledger estimate: **USD 0.9636** for this job; cumulative project ledger
**USD 10.0722**. The estimate includes image builds and startup at the GPU rate and is
not the Modal bill. The GPU function's 20-minute timeout is distinct from launcher elapsed
time while images are built.

Artifacts:
- `reports/modal/smoke_thinking.json`: measured summary, per-episode and per-turn diagnostics.
- `reports/modal/smoke_thinking_replay.json`: all 12 episodes and 127 tool calls replayed
  exactly, including observations, state hashes, final states, and verdicts.
- `runs/modal/smoke-thinking-v3d/`: downloaded episode records, config, and summary (ignored).
- Local validation before launch: Ruff lint and format, strict mypy, **255 tests passed**.

The smoke supports keeping the existing instruct candidate for now. A model-selection
comparison would need repeated train/dev evaluation and an explicit quality-versus-cost
criterion before any switch or full thinking-model training.
