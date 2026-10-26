# Training audit — 2026-10-26

The active Instruct configuration is compatible with the pinned APIs, and its prompt and
completion budgets fit its training context. The audit found two issues, now corrected:
the generated curriculum underrepresented variant 2, and TRL's truncation detection missed
some tool-loop exits. These are separate from the successful three-step GPU smoke;
that smoke does not establish that a full run is bug-free.

This audit launched no Modal jobs. After reviewing the initial audit, the owner requested
larger training limits: context is now **131,072**, matching the test server, and the completion
budget is **24,576**. Budget limits were not changed. The owner's allocation is **$25 for
training alone**, with evaluations separate. The fixes were validated locally without GPU jobs.

## Effective parameters

Sources: `modal_app/train_config.json`, `modal_app/train_grpo.py`, `modal_app/settings.py`,
and the exact TRL 1.16.0 / Transformers 5.17.0 release sources. Values inherited from libraries
are distinguished below because they do not appear in the project's JSON configuration.

| Parameter | Effective training value |
|---|---|
| Model | `Qwen/Qwen3-4B-Instruct-2507`, non-thinking |
| Pinned revision | `cdbee75f17c01a7cc42f958dc650907174af0554` |
| Prompt / run / seed | `v3d` / `grpo-v3d` / 7 |
| Adapter | LoRA rank 16, alpha 32, dropout 0, all linear layers |
| Learning rate | Starts at `2e-5`; inherited linear decay, zero warmup |
| Maximum optimizer steps | 150, subject to the wall-clock stop |
| Generations per prompt | 8 |
| Batch | 2 per forward pass × 16 accumulation × 1 GPU = 32 rollouts per optimizer step |
| Distinct prompt groups per step | 4 groups of 8 rollouts |
| Maximum rollouts over 150 steps | 4,800; not 4,800 unique tasks |
| Training sampling | Temperature 1.0; inherited top_p 1.0, top_k 0 (disabled), min_p unset |
| Completion budget | 24,576 tokens **across the rollout**, including assistant turns and tool responses |
| vLLM training context | 131,072 tokens, including the initial prompt |
| Tool-loop iteration cap | 30; an iteration can contain multiple tool calls |
| Precision / memory | bf16; gradient checkpointing; colocated vLLM memory utilization 0.35 |
| Reward | Trusted verifier's binary success reward |
| Loss / reward normalization | Inherited `dapo` / `group` |
| KL coefficient | Inherited beta 0.0: no reference-policy KL penalty |
| Updates per generated batch | Inherited `num_iterations=1` |
| Gradient clipping / weight decay | Inherited max norm 1.0 / weight decay 0.0 |
| vLLM importance correction | Inherited enabled, `sequence_mask` |
| Checkpoints | Every 25 steps; retain up to 8; save a final adapter on normal completion |
| Time limits | 225-minute soft stop; 250-minute Modal hard timeout |

Training sampling differs deliberately from evaluation: evaluation uses temperature 0.7,
top_p 0.8 and the model's top_k 20. Its 16,384-token limit is **per turn**, with a 131,072-token
serving context. Neither those evaluation limits nor the model's native 262,144-token window
are the training window. Temperature 1.0 and beta 0 are valid choices, not API bugs; they
increase exploration and leave drift control to the clipped objective and the run's duration.

## Findings

### Fixed: the 144 generated instances omitted scenario variant 2

Location: `src/invoiceops/tasks/build.py:102`, especially the variant index at line 109;
activated by `generated_variants: 144` in the training configuration.

The original generator exhausted all 6 companies × 12 families before advancing the variant
index. Its first 72 outputs were variant 0, the next 72 variant 1, and variant 2 started at
output 145. The original 180-row dataset contained:

| Scenario variant | Original rows | Generated rows | Total |
|---|---:|---:|---:|
| 0 | 12 | 72 | 84 |
| 1 | 12 | 72 | 84 |
| 2 | 12 | 0 | 12 |

Families and companies remain balanced, but variant 2 receives one seventh as many rows as
either other variant. Shuffling cannot repair this distribution. This is a curriculum coverage
issue, not an invalid-task or leakage problem.

The generator now interleaves variants within each company/family sweep and rotates them
between sweeps. The 144 generated rows contain **48/48/48** variants; including original
tasks the counts are **60/60/60**. Every family still has 15 rows and every training company
30. The oracle solves all 180 reconstructed rows through the training adapter. A complete
216-generated-row cycle visits each company/family/variant triple once; slicing remains
deterministic. These invariants are covered by `tests/test_training.py`.

### Fixed: EOS-terminated tool-loop cutoffs entered the loss

Project setting: `modal_app/train_grpo.py:39`. The behavior is in pinned TRL 1.16.0's
`GRPOTrainer._tool_call_loop` and `_generate_and_score_completions`.

TRL identifies truncation by whether the **last token** is EOS or padding. However:

1. If an executed tool's response would exceed the rollout budget, the loop removes that
   response from the conversation and exits with the preceding assistant tool call intact.
   That assistant message normally ends in EOS, so the truncation mask remains enabled.
2. If the tool-iteration limit is reached after another tool call was generated, the loop exits
   with that pending call unexecuted. Its EOS also passes the truncation check.

I reproduced both paths by executing the exact release's tool-loop method on the CPU,
substituting deterministic generation, parsing and token suffixes. These were synthetic edge
cases, not observed failures in the recorded GPU smoke. They demonstrate that the project's
comment promising to exclude budget-cut rollouts is stronger than the implementation.
Such incomplete rollouts can contribute learning signal when their group has mixed rewards;
the clipped-ratio metric can also undercount these exits.

`modal_app/grpo_safety.py` now wraps the pinned trainer's generation boundary. If a rollout
ends on a tool call while its environment is unfinished, it zeros that rollout's tool-loss
mask and marks its reward unscorable **before** TRL constructs tensors, normalizes reward
groups or counts DAPO loss tokens. Completed environments retain their rewards and masks.
The token IDs, logprobs, generated-length metrics and observations remain intact. The extra
`rollouts/tool_cutoff_ratio` metric reports these exits; TRL's original `clipped_ratio` remains
an EOS-based metric. The environment clears its cutoff marker on reset.

Regression tests cover unfinished EOS calls, terminal success, natural failure, environment
reuse and disabling masking. The CPU reproduction also runs the exact release's tool-loop
method through the project wrapper: both audited cutoff paths now have zero loss tokens
and excluded rewards. This does not replace an on-GPU smoke of the updated trainer.

The same loop requests a full per-turn generation allowance and slices it to the remaining
rollout budget afterward. A deterministic test generated 10 tokens when only 2 could be kept.
This is an additional efficiency concern for unusually long rollouts.

## Checks that passed

- **275 local tests pass**, including 20 new regression cases; Ruff and mypy pass.
- All 180 dataset rows resolve to unique train-only tasks, with no held-out task ID overlap.
- Generated specs reconstruct the exact public prompt stored in each row.
- All 180 tasks receive reward 1 through `InvoiceOpsToolEnv` when solved by the oracle.
- All configured GRPO keyword names exist in the pinned configuration classes.
- Generation batch 32 is divisible by 8 generations: four complete groups per optimizer step.
- Tokenizing all initial prompts with the pinned model tokenizer and all 15 discovered tool
  schemas gives **3,121–3,126 tokens**. Maximum prompt plus completion budget is
  **27,702**, below the new 131,072 context ceiling. Actual sequence length is still bounded
  by the initial prompt plus the whole-rollout completion cap.
- The model's pinned revision equals its Hub main revision at this audit. TRL loads the policy
  and tokenizer at the pin. Although its colocated vLLM loader omits the revision argument,
  it synchronizes all policy weights before first generation; this is not evidence that this
  run trains against different base weights.
- Pinned TRL handles all-None reward rows with a NaN-aware baseline and zero advantage;
  unscorable verifier results are not silently treated as ordinary failures.

Machine-readable measurements and synthetic-case outputs are in
[`training_audit_checks.json`](training_audit_checks.json). The checked TRL trainer source
SHA-256 is recorded there. Primary release source:
[TRL GRPO trainer](https://github.com/huggingface/trl/blob/v1.16.0/trl/trainer/grpo_trainer.py),
[TRL configuration](https://github.com/huggingface/trl/blob/v1.16.0/trl/trainer/grpo_config.py),
and [the pinned model configuration](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507/blob/cdbee75f17c01a7cc42f958dc650907174af0554/config.json).

## Operational limits and budget

The existing GPU smoke completed three optimizer steps with **8 rollouts per step**, saved an
adapter, and demonstrated nonzero gradients on mixed-reward groups. The later selection /
merge / serving smoke passed too. The proposed full run uses **32 rollouts per step** and has
not been executed. Its longest-rollout memory use and sustained training behavior remain
untested. That smoke used the previous 16,384 completion / 20,480 context settings. Passing
local tests does not establish training improvement or a GPU memory bound at the new limits.

The enlarged context also needs a GPU startup check: vLLM 0.31.0 requires its KV cache to
hold at least one sequence of the configured maximum length, even though actual rollouts
are capped much earlier. For this model, bf16 KV storage at 131,072 tokens is approximately
18 GiB before cache-block overhead. Whether that fits alongside weights and other allocations
under the current colocated memory utilization of 0.35 must be checked on the H100. See
[the pinned vLLM cache validation](https://github.com/vllm-project/vllm/blob/v0.31.0/vllm/v1/core/kv_cache_utils.py).

The soft stop checks time only at optimizer-step boundaries. A slow step may run beyond
225 minutes, and a hard timeout can prevent the final save. In addition, `trainer.train()` has
no resume argument and the output directory is reused without rejecting old contents.
The training entry point now refuses an existing run directory rather than silently mixing
old checkpoints with a fresh run. It still does not implement automatic resume; retries need
a fresh run name. A timeout can still prevent the final save.

Checkpoint selection now hashes adapter configuration and weights, evaluates identical saved
adapters only once, and fills the candidate list with the next distinct checkpoints. It also
rejects incomplete or unscorable development runs before selection, merge or final test.
The historical three-step smoke evaluated the same final weights twice; its different scores
reflect stochastic evaluation.

At the configured H100 rate of $4.45/hour, the 250-minute hard limit estimates **$18.5417**
for training, leaving **$6.4583** within the owner's **$25 training allocation**. This is a planning
estimate, not a dashboard bill. The separate evaluation jobs are outside that allocation.

The launch dry run currently refuses training: the project's cumulative released limit is
still $11, with $10.0722 in its estimated ledger. It requires at least $28.62 cumulatively to
admit this training job's current worst case. That cumulative figure includes earlier work on
both accounts; it is not the training job's price. A training allocation and account balance
must be represented correctly in the launch guard before launching. No limits were changed
and no GPU credits were spent during this audit.
