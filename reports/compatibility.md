# Compatibility report (Phase 11A)

Results of the first credit release (`docs/MODAL_HANDOFF.md`, USD 9.50). Every figure comes from `reports/modal/*.json` and `reports/modal_ledger.jsonl`.

## What ran

| # | Job | Result | Ledger cost |
|---|---|---|---|
| 1 | `inspect_models` | Passed on the third attempt. The first was blocked by the network policy (`input-plane.us-east.modal.com`); the second could not find the prompt files in the image. | $0.00 |
| 2 | `smoke_serve_candidate` | Passed on the re-run. The first attempt failed because the BFCL environment was missing `soundfile`. | $0.40 |
| 3 | `probe_and_dev` | Passed. | $0.31 |
| 4 | `smoke_train` | Passed on the re-run. The first attempt hit a `KeyError: 'model'` in the job wrapper before loading any weights. | $0.36 |
| 5 | `test_candidate` | Passed. See `reports/baseline.md`. | $0.35 |
| 6 | `smoke_tau2` | Passed on the third attempt, with the owner's go-ahead. The first failed on DeepGEMM, the second on missing τ² data; details below. | $1.26 |
| 7 | `bfcl_before` | Passed. See `reports/external_baseline.md`. | $0.42 |
| + | `probe_v2` (added) | Passed: train split, prompt v2, 43.8%; 19 of 36 tasks have mixed outcomes. | $0.30 |
| + | `tau2_before` | Passed: pass^1 36.9%, pass^4 20.0%. | $1.16 |
| + | `test_reference` (prompt v2) | Passed: 61.5%. See `reports/baseline.md`. | $0.35 |
| + | `tau2_reference` | Passed: pass^1 43.8%, pass^4 27.5%. | $0.85 |
| + | `dev_v2` (added) | Passed: dev split, prompt v2, 47.9% (CI 27.1%–70.8%). | $0.20 |
| + | `prompt_trial` v3a, v3b, v3c (added) | Passed. Train+dev 34.4%, 28.6%, **69.3%** (v2: 44.8%). See `reports/prompt_trials.md`. | $1.26 |
| + | `test_prompt` v3c (added) | Passed: **72.9%** on test, the single test run of the chosen prompt. | $0.25 |
| + | `prompt_trial` v3d, `test_prompt` v3d (added) | Passed. Train+dev 78.1%; test 71.9% (v3c 72.9%). | $0.73 |
| | **Total** | | **$8.21** |

Jobs marked + ran after the owner released the rest of the $9.50 for the remaining jobs.
- `smoke_serve_reference` was not run: the reference model was already served twice successfully.
- `train_grpo` does not fit the release.

## Versions and revisions

| Component | Version |
|---|---|
| Candidate | `Qwen/Qwen3-4B-Instruct-2507` @ `cdbee75f17c01a7cc42f958dc650907174af0554` (Apache-2.0, 262,144-token context, tool-calling template) |
| Reference (FP8) | `Qwen/Qwen3-30B-A3B-Instruct-2507-FP8` @ `5a5a776300a41aaa681dd7ff0106608ef2bc90db` |
| Reference (bf16) | `Qwen/Qwen3-30B-A3B-Instruct-2507` @ `0d7cf23991f47feeb3a57ecb4c9cee8ea4a17bfe` |
| Fallbacks | `Qwen/Qwen3.5-4B` @ `851bf6e8…` (an image-text model, `Qwen3_5ForConditionalGeneration`); `Qwen/Qwen3-8B` @ `b968826d…` (**40,960-token context**: it needs its own `max_model_len` if it is ever used) |
| Serving | vLLM 0.31.0; Hermes tool-call parser; `VLLM_USE_DEEP_GEMM=0` (see τ²-bench) |
| Training | TRL 1.16.0, PEFT 0.21.2, transformers 5.17.0, torch 2.13.0 |
| Benchmarks | BFCL `bfcl-eval` 2026.3.23; τ²-bench @ `318fa35b1431a42e3ffdad05197378f506fac9d4` |
| Client | `modal[api-proxy-support]` 1.6.2 (the proxy extra lets the client connect through an HTTPS proxy) |

## Serving (smoke_serve_candidate)

- **Stack:** vLLM 0.31.0 on an L40S serves `Qwen/Qwen3-4B-Instruct-2507` at revision `cdbee75f17c01a7cc42f958dc650907174af0554`, with `--max-model-len 131072` and `--gpu-memory-utilization 0.85`.
- **Memory:** vLLM reported 28.66 GiB of KV cache, room for 208,672 tokens. That is 1.59 full-length requests at once; typical episodes are far shorter.
- **Tool-call parsing:** the Hermes parser (`--tool-call-parser hermes`) parsed both calls of the two-tool round trip, with the right names and arguments (`roundtrip.ok`).
- **BFCL smoke (5 cases per category; a pipeline check, not a score):** `simple_python` 5/5, `multi_turn_base` 0/5. `bfcl_before` measures the full categories.
- **Fixes on the way:**
  - Images now ship the system prompts. Modal's default copies only `.py` files.
  - `soundfile` is added to the BFCL environment. `qwen_agent` imports it without declaring it.
- **BFCL request length:** BFCL asks for at most `min(4096, context − prompt)` new tokens per request, using the model's 262,144 `max_position_embeddings` as the context. Requests therefore stay under 4,096 output tokens and fit the 131,072 server. BFCL's own output cap is left as it is, so scores stay comparable.

## Learnability probe (train split, prompt v1, 4 attempts)

- **Overall:** task-mean success 13.9% (95% CI 5.6%–24.3%), pass@4 25.0%, pass^4 5.6%.
- **Per task:**
  - 7 of the 36 tasks pass in some attempts and fail in others. Only these give GRPO a learning signal.
  - 2 always pass.
  - **27 always fail.**
- **Per family:** 6 of 12 families never passed on the training split: F02 Price discrepancy, F03 Short receipt, F06 Approval routing, F10 Untrusted document instructions, F11 Transient tool failure, F12 Stale policy and amended records.
- **Dev split, 2 attempts:** 8.3% (CI 0.0%–25.0%).

| Family | Train (3 tasks × 4) | Dev (1 task × 2) |
|---|---|---|
| F01 Clean match | 16.7% | 0.0% |
| F02 Price discrepancy | 0.0% | 0.0% |
| F03 Short receipt | 0.0% | 0.0% |
| F04 Duplicate invoice | 16.7% | 0.0% |
| F05 Credit note | 41.7% | 0.0% |
| F06 Approval routing | 0.0% | 0.0% |
| F07 Vendor-detail conflict | 16.7% | 0.0% |
| F08 Missing receipt and clarification | 58.3% | 100.0% |
| F09 Shared PO capacity | 16.7% | 0.0% |
| F10 Untrusted document instructions | 0.0% | 0.0% |
| F11 Transient tool failure | 0.0% | 0.0% |
| F12 Stale policy and amended records | 0.0% | 0.0% |

**For the owner's curriculum decision:**
- With prompt v1, three quarters of the training tasks give zero reward in all four attempts, so GRPO gets no gradient from them.
- `modal_app/train_config.json` currently trains with prompt v1.
- On the test split, prompt v2 scores 41.7% against v1's 7.3% (`reports/baseline.md`), so training with v2 is likely to give far more tasks a mixed outcome. This probe did not measure v2 on the training split.

## Training stack (smoke_train)

The smoke run was three GRPO steps through `environment_factory`:
- LoRA r=16, 8 rollouts per step (2 per device × 4 accumulation steps), on the 36 training tasks.
- The model is loaded at the pinned revision in bf16.
- `max_completion_length` is 16,384 and `vllm_max_model_length` is 20,480.

| Step | Reward | Reward std | Groups with zero std | Completion mean / max | Clipped | Tool calls per rollout | Tool failures | IS ratio mean | Step seconds |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.125 | 0.354 | 0.00 | 830 / 1093 | 0.00 | 11.1 | 0.00 | 0.79 | 27.1 |
| 2 | 0.000 | 0.000 | 1.00 | 685 / 825 | 0.00 | 11.0 | 0.00 | 0.45 | 23.5 |
| 3 | 0.750 | 0.463 | 0.00 | 726 / 805 | 0.00 | 11.5 | 0.00 | 0.51 | 22.8 |

What this shows:
- **Rewards flow** from the verifier through `get_reward`.
- **Tool calls execute,** with no tool failures.
- **No completion came near the budget:** none was clipped.
- **A checkpoint (`checkpoint-3`) and the final LoRA adapter were saved:** README.md, adapter_config.json, adapter_model.safetensors, chat_template.jinja, tokenizer.json, tokenizer_config.json, training_args.bin.

To watch in the real run:
- **Importance-sampling ratio:** the mean ratio between vLLM's sampling and the trainer's log-probabilities was 0.45–0.79. TRL corrects for it, but `sampling/importance_sampling_ratio` is worth watching.
- **Wall clock:** about 23–27 s per step of 8 rollouts. The full run uses 32 rollouts per step for 150 steps; if time scaled linearly, that would pass the 225-minute wall-clock stop. vLLM batches the 32 rollouts together, so the real time per step should be lower. Watch `step_time` in the first steps of `train_grpo`.

## τ²-bench (smoke_tau2)

The job failed twice, and the third attempt passed after both fixes, with the owner's go-ahead:

1. **First attempt: the FP8 user simulator failed to start.** vLLM's DeepGEMM FP8 kernels compile at start-up and need nvcc 12.9 or newer, while the CUDA base image has 12.8. Fix: `VLLM_USE_DEEP_GEMM=0`. vLLM then uses its CUTLASS, FlashInfer or Triton FP8 kernels.
2. **Re-run: both servers started, then the driver failed.**
   - KV cache: the agent got 156,192 tokens at 40% memory, the user simulator 38,176 at 45%.
   - The driver stopped because a pip install from git leaves out tau2's `data/` directory, so `retail/tasks.json` was missing.
   - Fix: the image installs tau2 from a checkout at the pinned commit and sets `TAU2_DATA_DIR`.
   - Checked first on Modal by an image build, and locally by running the driver end to end against a stub server.
3. **Third attempt: passed.** 2 simulations, none without a reward, **16.3 s per simulation**.

**Trials rule (`MODAL_RUNBOOK.md` §1 step 4):** 16.3 s × 160 / 16 + 10 minutes of start-up is about 12.7 minutes, well under 50, so `TAU2_TRIALS` stays at 4. `tau2_before` then took 15.6 minutes, of which 9.5 minutes were simulations.

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

### Measured in the runs

Across all 360 evaluation attempts (probe, dev, test v1 and v2), the context limit was never a constraint:
- **Turns truncated:** 0.
- **Episodes stopped by the context guard:** 0.
- **Largest context:** 8,411 tokens (test, prompt v2).

The figures come from `tokens` in each summary. `inspect_models` recounted the tokenizer figures with the candidate's own `tokenizer.json`: schemas 2,675, system prompts 110 and 260, largest document 1,683. They match the estimates below to the token.

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
