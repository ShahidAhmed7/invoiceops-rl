# Handoff prompt: run full Instruct GRPO training and archive every raw trajectory locally

Copy the prompt below into the chat that will execute the training.

---

You are taking over the InvoiceOps RL project. Your job is to implement complete trajectory
logging, validate the updated training stack, execute one full GRPO training run within the
owner's **$25 training allocation**, and deliver all raw trajectories and training artifacts
to the owner's local disk. Work through completion, rather than returning after launch.

Working directory: `/Users/shahidahmed/Documents/invoiceops-rl`.

## 1. Owner instructions and scope

- Use **Qwen/Qwen3-4B-Instruct-2507**, prompt **v3d**. The thinking model is deferred.
- Training context must be **131,072 tokens**, matching the test server, which the owner
  described as approximately 132k. It is not 13,200 tokens.
- The training completion budget is **24,576 tokens across the entire multi-turn rollout**,
  including assistant outputs and tool responses. It is not a fresh 24,576-token allowance
  for each turn. Preserve this distinction in code, logging and reports.
- **$25 covers the new training work in total**, including readiness smokes, failed attempts,
  retries and relevant ancillary charges. It is not $25 per attempt. Historical work is
  separate. Post-training evaluations have a separate allocation; this prompt does not
  release an unspecified additional evaluation budget.
- Log **every raw trajectory locally**, including failures, truncated/masked trajectories,
  zero-reward trajectories, successful trajectories and partially completed attempts when
  recovery is possible. Do not sample, filter or keep only successful examples.
- Implement necessary reversible fixes and conduct the bounded training run without asking
  for routine reconfirmation. This is the owner's instruction to perform that work within
  the stated scope and budget. Record the authorization accurately. Do not fabricate an
  independent reviewer's approval or overwrite reviewer-owned sign-off records.
- Preserve the existing dirty workspace. Several recent audit and thinking-smoke changes
  are uncommitted. Do not reset, discard or silently replace them.
- Do not launch duplicate training jobs, switch models, raise the $25 allocation, or run
  unrelated prompt sweeps. If a material blocker cannot be resolved within the authorized
  settings and budget, save the evidence and explain it clearly.

## 2. Read the current state before editing

Read these files under `/Users/shahidahmed/Documents/invoiceops-rl/`:

1. `docs/PROJECT_HANDOFF.md`
2. `reports/training_audit.md` and `reports/training_audit_checks.json`
3. `reports/evaluation_audit.md` and `reports/evaluation_audit_checks.json`
4. `modal_app/train_grpo.py`, `modal_app/train_config.json`, `modal_app/grpo_safety.py`
5. `src/invoiceops/adapters/trl_env.py`, `src/invoiceops/tasks/build.py`
6. `modal_app/app.py`, `modal_app/launch.py`, `modal_app/checkpoints.py`
7. `modal_app/budget.py`, `modal_app/budget.yaml`, `reports/modal_ledger.jsonl`
8. `src/invoiceops/runs.py`, `src/invoiceops/episode.py`, `src/invoiceops/verification/verifier.py`
9. `docs/review/signoff/pre-gpu.md` and `docs/review/builder-response.md`

The generic `docs/MODAL_RUNBOOK.md` contains historical instructions and stale statements
that no GPU work has run. Prefer the current handoff, audit reports and executable settings
for current state. Understand existing review requirements and owner authorization; do not
invent another approval step based solely on stale prose.

Current status:

- Full GRPO training has **not** run.
- A historical three-step GPU smoke and the selection/merge/serving chain passed. That smoke
  used 8 rollouts per step, 16,384 completion tokens and 20,480 context tokens.
- The **updated** 131k context, larger completion budget, safety wrapper and full batch have
  not been tested together on GPU. Do not treat the historical smoke as that validation.
- The local suite last passed **275 tests**, plus Ruff and mypy.
- The 180 training rows now contain **60/60/60** scenario variants. The generator contributes
  48/48/48 extra variants. Every family has 15 rows and every training company 30. All 180
  reconstructed rows pass the oracle through the training environment.
- The project trainer wrapper masks unfinished EOS-terminated tool calls and excludes their
  rewards from the group baseline. Preserve this fix and its terminal-success behavior.

## 3. Freeze and record the effective training settings

Merge `train_config.json` with `train_grpo.py:DEFAULTS` and verify these effective values:

| Setting | Value |
|---|---|
| Model | `Qwen/Qwen3-4B-Instruct-2507` |
| Revision | `cdbee75f17c01a7cc42f958dc650907174af0554` |
| Prompt / seed | `v3d` / 7 |
| Dataset | 36 original train tasks + 144 generated train instances = 180 rows |
| LoRA | rank 16, alpha 32, dropout 0, `all-linear`, causal LM |
| Learning rate / scheduler | `2e-5` / inherited linear decay, zero warmup |
| Generations per prompt | 8 |
| Per-device batch / accumulation | 2 / 16, one GPU |
| Effective generation batch | 32 rollouts, four groups of eight per optimizer step |
| Maximum optimizer steps | 150 |
| Whole-rollout completion budget | 24,576 |
| vLLM context | 131,072 |
| Tool-loop iteration cap | 30; a turn can contain multiple tool calls |
| Training sampling | temperature 1.0; inherited top_p 1.0, top_k 0, min_p unset |
| Reward / loss | strict binary verifier reward / inherited DAPO, group reward scaling |
| KL / iterations | inherited beta 0.0 / one update iteration per generated batch |
| Precision / memory | bf16, gradient checkpointing, colocated vLLM, utilization initially 0.35 |
| Truncation handling | TRL token masking plus `trainer_with_rollout_safety` |
| Checkpoint interval / retention | every 25 steps / up to 8, plus final adapter |
| Soft / hard time limits | 225 / 250 minutes |

Pinned GPU stack: TRL 1.16.0, Transformers 5.17.0, PEFT 0.21.2, vLLM 0.31.0,
PyTorch 2.13.0, Accelerate 1.15.0, Datasets 5.1.0. Use the image lockfiles; do not casually
upgrade the stack. Do not install the large CUDA stack on the owner's Mac.

Use a fresh, timestamped run name such as `grpo-v3d-full-<UTC_TIMESTAMP>` and a different
name for every smoke. Record the actual names and full effective configuration. The training
entry point refuses existing run directories and does not automatically resume. `--rerun`
only bypasses the launcher's succeeded-job guard; it does not resume training or make an
existing output directory safe. Add a small explicit smoke/run-name override if needed.

## 4. Account and budget checks before any paid call

Credentials already exist in private local configuration and the gitignored project `.env`.
Use `uv run --frozen --group modal --env-file .env ...` for the intended account. The private
profile is named `invoiceops-thinking`; that name identifies an account, not the model to
train. Verify the actual workspace and balance privately. Never print tokens, dump the
environment, copy `.env` into artifacts, or log authentication headers.

The current configured rates are H100 $4.45/hour and L40S $2.45/hour, including a planning
allowance. Confirm current applicable charges before relying on them. At the configured
H100 rate:

- A 250-minute full-training hard timeout estimates **$18.5417**.
- A 20-minute H100 smoke timeout estimates **$1.4833**, regardless of its lower nominal
  job cap in the YAML. Use timeout-based exposure, not the plan cap, for budget admission.
- One such smoke plus a worst-case full run estimates **$20.025**, leaving about $4.98
  within $25 for contingency and other training-related charges. Recalculate after each job.

The current global guard still has an old **$11 cumulative release** and about **$10.0722**
of historical estimated spend across accounts. It will refuse a full training launch.
Implement/document the owner's new training allocation in the guard correctly before launch:

- Keep historical ledger entries intact and distinguish accounts and this training allocation.
- Enforce **$25 maximum for this new training campaign**, reserving the full main-run worst
  case before spending on readiness jobs. Include failed jobs and all new smoke costs.
- Do not simply set the old cumulative release to $25 and call that $25 available for training.
  Do not charge all old-account expenditure against the new allocation either.
- Keep unrelated evaluation reserves separate; do not disable the budget guard or bypass the
  launcher with direct `.remote()` calls to get around a refusal.
- Update dollar calculations from the actual ledger and account state, rather than copying
  a stale cumulative-release number. Record every allocation/config adjustment transparently.
- Reconcile conservative ledger estimates with actual dashboard charges when available.

Do not raise timeouts or start another attempt unless its worst case fits the **remaining**
training allocation. Keep GPUs stopped between calls when idle.

## 5. Implement durable raw-trajectory logging before full training

This is required implementation work. The current `log_completions=True`, `report_to=none`,
and saved `log_history.json` do **not** constitute a complete persistent rollout archive.
Do not launch the full run until logging passes tests and a GPU smoke.

Use the existing trainer wrapper and environment integration, with narrow hooks compatible
with the exact pinned TRL version. Keep environment logging helpers private: TRL discovers
public methods as tools. The agent must still see exactly the intended 15 tools. Logging
must not add tool access, expose private answers, mutate trajectories, or alter rewards.
If a small upstream method must be vendored, retain its license/provenance, record the exact
release/source hash, keep modifications narrow and test parity against the pinned method.

### Identity and coverage

- Give each campaign, job, generation batch, prompt group, rollout and model turn a stable ID.
  Include process rank and both generation-batch ordinal and rollout index. Repeated visits
  to the same task must have different rollout IDs.
- Preserve explicit per-environment identity when TRL subsets a batch for another tool turn.
  Do not infer identity solely from prompt text: the eight generations in a group can have
  identical prompts, outputs and tool observations. Test that ambiguous case explicitly.
- Count each generated rollout once, not once per gradient-accumulation microbatch. Keep
  smoke and main-run counts separate. The planned 150-step main run has 32 rollouts per
  optimizer step, approximately 4,800 rollouts if every planned step completes; reconcile
  actual counts for early stops or partial batches instead of manufacturing expected records.
- Capture failures, all-equal reward groups, excluded rewards and incomplete attempts. Record
  a started-but-interrupted status when a batch fails; do not present missing data as success.

### Minimum raw content

For every rollout retain, in losslessly recoverable form:

- Task ID, original/generated flag, generated world/family/variant/salt, frozen task/bundle
  reference, dataset row index, prompt-group ID, seed where applicable, model/revision and
  effective run configuration reference.
- The exact initial model-visible messages and tool schemas, each model input's token IDs,
  and every raw sampled output's token IDs and decoded text before parsing or truncation.
- Every assistant turn and tool call, with raw arguments, parsed arguments, call ordering,
  tool results/errors and timestamps/durations. Store sampling logprobs and finish reasons
  when the backend exposes them; explicitly mark unavailable fields instead of inventing them.
- The complete actual environment event log, including observations later removed from the
  model-visible conversation by TRL's budget rollback. Keep the model-visible transcript and
  executed environment history distinguishable.
- Raw outputs discarded by the completion-budget slice. Retained completion IDs alone are
  insufficient to reconstruct how much generation occurred or where truncation happened.
- Initial and final state snapshots, per-event state hashes, actual terminal/end reason,
  token/context/iteration-budget exits and any infrastructure/verifier exception.
- Raw verifier verdict/checks/critical violations, the reward actually supplied to training,
  cutoff/exclusion reason, actual tool/loss masks, group identity and advantages when available.
  Distinguish a valid zero reward from `None`, a masked sample, and a verifier error. Preserve
  which samples entered the reward baseline even when their token loss was masked.
- Optimizer step before generation and the associated update, epoch/batch ordering, token
  counts and model-turn timing. Preserve special tokens and formatting needed for replay.

Save the frozen dataset manifest and full bundles once per run, with hashes, so generated
tasks can be replayed without relying on a subsequently modified generator. Private verifier
expectations belong only in trusted run artifacts; never feed them into model messages.

### Durable storage and local mirroring

Use these locations, or equivalent explicit paths documented in the run manifest:

- Remote durable volume: `invoiceops-runs:/train/<RUN_NAME>/`
- Local run root:
  `/Users/shahidahmed/Documents/invoiceops-rl/runs/modal/training/<RUN_NAME>/`
- Raw rollout shards: `trajectories/`; raw model-call shards: `model_calls/`
- Shared frozen data: `dataset/`; integrity manifest: `manifest.json`
- Console/launcher logs: `logs/`; periodic checkpoints: `checkpoints/`
- Final adapter: `final_adapter/`; configuration and step logs alongside them.

Use bounded-memory, append-safe lossless formats, such as immutable JSONL gzip shards.
Write temporary shards and atomically finalize them; flush completed records and commit the
Modal volume periodically, after generation batches, at checkpoints and on graceful stop.
Do not depend exclusively on the final `runs.commit()` after training returns. Preserve
recoverable partial artifacts on exceptions and timeout paths. Test the pinned SDK's volume
semantics rather than assuming files in container RAM are durable.

Run a local incremental downloader throughout training, roughly every 30–60 seconds when
new committed shards exist. Keep it independent of GPU computation and download finalized
files by manifest/checksum. Avoid repeatedly transferring all earlier shards. A remote volume,
dashboard log or cloud URL is **not** the requested local archive.

Estimate local storage from the smoke's bytes per rollout × planned rollouts, with headroom
for checkpoints and failure artifacts. Check free disk before the long job. Use compression
and immutable shared references where exact reconstruction is preserved; do not downsample
trajectories to save space. Keep raw artifacts under the already gitignored `runs/` directory.

The installed CLI supports a recursive final backup:

```bash
uv run --frozen --group modal --env-file .env modal volume get \
  invoiceops-runs /train/<RUN_NAME> \
  /Users/shahidahmed/Documents/invoiceops-rl/runs/modal/training/<RUN_NAME> --force
```

Replace placeholders with verified actual identifiers. This command downloads directory
contents recursively; verify the resulting layout. Do not treat it as an incremental sync
algorithm. At completion, compare remote and local manifests, checksums, counts and bytes.

## 6. Local validation and bounded GPU readiness smoke

First run the local checks, including new logging tests:

```bash
uv run --frozen --group dev --group modal pytest
uv run --frozen --group dev ruff check .
uv run --frozen --group dev ruff format --check .
uv run --frozen --group dev mypy
uv run --frozen --group dev --group modal python scripts/audit_evaluation.py
```

Add meaningful tests for repeated identical samples, multi-turn batch subsetting, generated
tasks, EOS-ended budget/iteration cutoffs, terminal success, exceptions, final-batch flushing,
environment reuse, identity uniqueness, atomic shards and local-download verification. Preserve
the existing training safety and evaluation regressions.

Then perform one bounded readiness smoke through the budgeted launcher with a fresh name:

- Use the actual Instruct revision, v3d, **131,072 context / 24,576 completion**, safety wrapper,
  logger and local mirroring. Run a small number of optimizer steps, ideally two or three,
  at the full **2 × 16** accumulation configuration and eight generations per prompt.
- Keep the corrected generated curriculum available. The old `SMOKE_TRAIN` override uses
  8 rollouts and zero generated rows; adapt it deliberately rather than assuming it tests the
  full batch and generated-row logging. Maintain a bounded hard timeout and ledger entry.
- Verify the H100 startup and memory profile. This model's bf16 KV cache for a 131,072-token
  maximum sequence alone needs about **18 GiB**, before cache-block overhead. vLLM validates
  capacity for that maximum even though actual prompt-plus-rollout length is about 27.7k.
  The current colocated utilization 0.35 may be tight. If needed, use measured memory data to
  make a modest allocation adjustment, preserve the owner's context/completion settings,
  document it and re-smoke only if the remaining $25 allocation allows it. Do not silently
  reduce the context or substitute a different model to make the smoke pass.
- Check finite losses/gradients on mixed-reward groups, tool execution, safety masking,
  checkpoint creation, durable records and local mirroring. A single all-equal reward group
  and zero gradient are normal; sustained absence of learning signal needs investigation.
- Verify logging against every smoke rollout. Replay actions from the frozen bundle and
  compare observations, final state/hash and verifier verdict. Generated tasks require their
  frozen bundles, not an on-disk `load_bundle(task_id)` lookup that cannot resolve them.
- Force local cutoff/failure cases to check archival coverage even if ordinary GPU samples
  do not hit those paths. Confirm the logger retained outputs removed by TRL's truncation.
- End the smoke, download all artifacts, inspect them and confirm there is no idle GPU.
  Do not proceed if logging is incomplete, IDs are ambiguous, the guard is wrong, or GPU
  memory at the requested settings has not been validated.

## 7. Execute and monitor the full run

Record the frozen settings, dataset/code hashes, relevant dirty diff or source snapshot,
dependency locks, account identity, Modal app ID, GPU type and budget admission decision.
Exclude credentials from source snapshots. Update the training configuration to the fresh
full-run name, then use the guarded launcher:

```bash
uv run --frozen --group modal --env-file .env python -m modal_app.launch train_grpo --dry-run
uv run --frozen --group modal --env-file .env python -m modal_app.launch train_grpo
```

Capture launcher output locally with a method that preserves its exit status, such as a
subprocess wrapper or a `pipefail`-protected tee. Keep the parent launcher alive through the
run. If detachment is necessary, use and validate the supported Modal lifecycle semantics;
do not accidentally cancel a paid run by abandoning its controlling process. Check the
installed CLI help for log retrieval; `modal app logs <APP_ID>` fetches recent logs, while
`--follow` streams them. Preserve timestamped logs locally.

Monitor step progress, elapsed time/cost, loss, grad norm, reward/group variance, completion
lengths, tool failures, importance-sampling corrections, TRL `clipped_ratio`, the added
`rollouts/tool_cutoff_ratio`, disk use and the remote/local trajectory counts. The EOS-only
clipped ratio does not replace the project cutoff metric. Give concise progress updates.

Stop at 150 optimizer steps or the 225-minute soft limit. The soft callback runs at step
boundaries and can overshoot; preserve the 250-minute hard ceiling. Allow time to save and
sync. If there are nonfinite losses, repeated protocol errors, broken logging, sustained
zero learning signal or a budget breach risk, stop gracefully where possible, persist all
available data, and diagnose before spending on another attempt. Never auto-retry a timed-out
run or reuse its output directory. Count the first attempt's cost before considering any retry.

## 8. Finish with a complete local archive and factual report

After training ends:

1. Commit/flush durable artifacts, retrieve every finalized shard and checkpoint, and recover
   any explicitly marked partial data. Confirm the final local mirror matches remote hashes.
2. Reconcile started/generated/finished/failed/masked rollouts per batch/group/step. Check
   duplicate IDs, gaps, missing model calls, missing tool events and unparseable shards.
   Compare counts to actual generation, not just `global_step × 32` when a job stopped mid-step.
3. Regrade/replay every completed trajectory against its frozen task bundle where technically
   possible. At minimum verify all action/observation/state/verdict integrity checks and
   explicitly list interrupted cases that cannot be fully replayed. Do not report full audit
   coverage if any records are missing. Make any resource limitation explicit.
4. Verify the final adapter and retained checkpoints exist locally, preserve optimizer/scheduler/
   RNG state files that were saved, and record hashes. The current final adapter alone is not
   a complete resumable optimizer checkpoint. Do not claim resume support without testing it.
5. Confirm no training GPU containers remain running. Reconcile actual or estimated campaign
   spend, split out smoke/failure/full-run costs, and state the remaining portion of $25.
6. Write a concise tracked report under `reports/` with step reached, normal/early/error stop,
   effective settings, app/run identifiers, reward/loss/gradient trends, cutoff counts, budget,
   exact local artifact path, dataset coverage and integrity results. Update the project handoff.
7. End with direct local links to the run report, local archive/manifest, final adapter and
   checkpoints. State plainly whether the full intended run completed and what remains.

Do not automatically call `select_and_test`, `tau2_after` or `bfcl_after` from this training
allocation. `select_and_test` also launches a test run; it is not merely a dev-selection command.
Prepare the next-step commands and cost estimates if separate evaluation funding is not yet
authorized. If evaluation is subsequently authorized, archive every evaluation trajectory too,
choose checkpoints on dev only, keep v3d and decoding fixed, and apply the evaluation audit's
coverage requirements. The existing test set has only four companies and prior prompt-work
exposure, so report gains as exploratory. Training reward alone is not evidence of improvement.

Your completion criteria are: logging implemented and validated, requested GPU settings
smoked, full training completed or a well-evidenced bounded failure reported, spend within
$25, every recoverable raw trajectory on the owner's local disk, and all counts/integrity
limitations documented. Do not declare success from console output or cloud-only files.
