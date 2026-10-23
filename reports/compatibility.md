# Compatibility report (Phase 11A)

Sections on serving, tool-call parsing, the learnability probe, the training stack and τ²-bench are added as the jobs in `docs/MODAL_HANDOFF.md` run.

## Serving (smoke_serve_candidate)

- **Stack:** vLLM 0.31.0 on an L40S serves `Qwen/Qwen3-4B-Instruct-2507` at revision `cdbee75f17c01a7cc42f958dc650907174af0554`, with `--max-model-len 131072` and `--gpu-memory-utilization 0.85`.
- **Memory:** vLLM reported 28.66 GiB of KV cache, room for 208,672 tokens. That is 1.59 full-length requests at once; typical episodes are far shorter.
- **Tool-call parsing:** the Hermes parser (`--tool-call-parser hermes`) parsed both calls of the two-tool round trip, with the right names and arguments (`roundtrip.ok`).
- **BFCL smoke (5 cases per category; a pipeline check, not a score):** `simple_python` 5/5, `multi_turn_base` 0/5. `bfcl_before` measures the full categories.
- **Fixes on the way:**
  - Images now ship the system prompts. Modal's default copies only `.py` files.
  - `soundfile` is added to the BFCL environment. `qwen_agent` imports it without declaring it.
- **BFCL request length:** BFCL asks for at most `min(4096, context − prompt)` new tokens per request, using the model's 262,144 `max_position_embeddings` as the context. Requests therefore stay under 4,096 output tokens and fit the 131,072 server. BFCL's own output cap is left as it is, so scores stay comparable.

## Context and generation lengths

Measured before any GPU run, over all 72 tasks, with a Qwen2/Qwen3 BPE tokenizer rebuilt from llama.cpp's `ggml-vocab-qwen2.gguf`. Qwen3 uses the same vocabulary. `huggingface.co` was not reachable from the build session. `inspect_models` recounts the main figures with the candidate's own `tokenizer.json` (`token_counts` in `reports/model_verification.json`).

Chat-format overhead (role markers, `<tool_call>` and `<tool_response>` wrappers) is included in the episode figures below.

| Part of the conversation | Tokens |
|---|---|
| Tool schemas (15 tools) | 2,675 |
| System prompt v1 / v2, without schemas | 110 / 260 |
| System block with schemas and tool instructions, v1 / v2 | 2,876 / 3,026 |
| Task prompt, max | 118 |
| **Fixed part of every request** | **≈ 3,150** |
| Oracle episode (calls and tool results), max / median | 2,426 / 1,871 (≤ 15 tool calls) |
| Reading every record once plus the oracle's actions, max / median | 8,728 / 6,805 |
| One tool call, max / median | 112 / 36 |
| Largest tool result (`get_document`) | 1,696 |
| Other tool results, max | `get_history` 560, `search_records` 435, `get_invoice` 305, the rest < 300 |

The densest tool output (digit-heavy JSON) measures 1.93 characters per token. The runner estimates at 1.8, so its context guard errs toward stopping early.

### What an episode can need

| Episode | Context needed |
|---|---|
| Oracle-like | ≈ 5.6k |
| Reads everything once, ~150 tokens of text per turn | ≈ 14k (the old 16k limit, minus 2k reserved for output, left 14.3k) |
| Worst case within the 40-tool-call limit (40 × largest result) | ≈ 80k |

### Settings chosen

**Evaluation (vLLM serving the agent):**
- **Context: 131,072.** The Qwen3-2507 models support 262,144 natively, so no RoPE scaling is needed.
- **Output: up to 16,384 new tokens per turn.** This is the output length Qwen uses in its own examples for the 2507 models.
- **No request can fail on length.** Each request asks for at most the context left, and the HTTP timeout is 900 s, enough for a full 16k-token turn under load.
- **Running out of context counts as a graded failure.** If fewer than 1,024 tokens remain, the episode ends unsolved, counted as `context_limit_stops` in the summary. Before this change it would have been an HTTP 400, dropped as unscorable.
- **Truncated turns are counted.** Turns cut off by the cap appear as `truncated_turns`, and the largest context reached as `max_context`.

**Memory check (bf16 KV cache):**
- Qwen3-4B has 36 layers, 8 KV heads and head dimension 128, so about 144 KiB per token.
- On the L40S at 85% memory, about 28 GiB remains for KV cache after weights, which is room for about 200k tokens. A single 131k sequence fits, and 16 typical episodes run side by side.
- vLLM allocates KV cache only for tokens in use.
- `inspect_models` records `kv_cache_bytes_per_token` from each model's config, to confirm these figures.

**τ² user simulator: 32,768.** It shares the H100 with the agent at 45% memory, which leaves about 40k tokens of KV cache for the FP8 30B model. Its dialogue carries no tool output. When the reference model is both agent and user, it gets the full 131,072.

**Training (TRL 1.16 `environment_factory`):**
- **Completion budget covers the whole rollout.** In TRL's tool loop the completion is every assistant turn plus every tool result (`_tool_call_loop`, `grpo_trainer.py`). Each turn may generate up to the remaining budget, and only the tail beyond `max_completion_length` is cut.
- **`max_completion_length` 16,384.** That is nearly twice the read-everything rollout.
- **`vllm_max_model_length` 20,480.** That is the 3.2k prompt plus 16,384, with margin, so the completion budget is always the limit reached first.
- **Truncated rollouts are left out of the loss** (`mask_truncated_completions`).
- **Batch: 2 per device × 16 accumulation steps.** That keeps 32 rollouts per step (4 groups of 8), but each forward pass holds logits for 2 sequences of up to 20k tokens (about 12 GB in bf16), not 8.
- **The smoke run uses 2 × 4**, which is one group of 8.
