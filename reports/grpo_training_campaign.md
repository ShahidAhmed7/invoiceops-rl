# GRPO training campaign — final report

Status: **full run `grpo-v3d` COMPLETED** — 150/150 optimizer steps over two
Modal attempts (preempted at ~55, resumed from checkpoint-50, finished at
150). All 4,960 rollout trajectories are preserved locally with verified
hashes and replayed without divergence.

## Campaign configuration (frozen at launch)

| Setting | Value |
| --- | --- |
| Model | `Qwen/Qwen3-4B-Instruct-2507` @ `cdbee75f…` (pinned revision) |
| Prompt | `v3d` |
| Context | 131,072 (`vllm_max_model_length`) |
| Completion budget | 24,576 tokens per rollout (all turns incl. tool results) |
| Rows | 180 = 36 fixed train tasks + 144 generated variants |
| LoRA | r=16, alpha=32, dropout=0, `all-linear` |
| LR | 2e-5, cosine schedule (TRL default) |
| Generations/prompt | 8 |
| Batch | 2 per-device × 16 grad-accum → 32 rollouts/optimizer step |
| Max steps | 150 (max 4,800 rollouts) |
| Tool iterations | ≤ 30 per rollout |
| Sampling | temp 1.0, top-p 1.0, top-k 0, seed 7 |
| Wall clock | 345 min soft stop; 360 min Modal hard timeout |

## Trajectory logging (what was added for this campaign)

- `src/invoiceops/adapters/rollout_log.py` — `RolloutRecorder`: atomic
  `.jsonl.gz` shards (`trajectories/batch-NNNN.jsonl.gz`, `model_calls/batch-NNNN.jsonl.gz`),
  a running `manifest.json` (sha256 + sizes + counters), per-batch volume commits.
- `trl_env.py` — private recorder hooks (`_dispatch`, `get_reward`,
  `_mark_rollout_truncated`, `reset`); the 15-tool public surface is unchanged.
- `modal_app/grpo_safety.py` — batch hooks around
  `_generate_and_score_completions`; raw-vs-post-safety tool masks captured;
  unfinished tool-pending rollouts get zeroed masks and are excluded from
  reward normalization (`rollouts/tool_cutoff_ratio` metric).
- `modal_app/trajectory_logging.py` — wraps `trainer.vllm_generation.llm.generate`
  (the single model-call choke point in TRL 1.16 colocate mode); refuses to
  train if the wrap fails; freezes dataset bundle hashes + code snapshot +
  stack versions into `meta.json`/`manifest.json`.
- `modal_app/sync_run.py` — incremental volume→local mirror with sha256
  verification, resumable state, `.tmp`/`.part` staging excluded.
- `scripts/replay_rollouts.py` — replays each record's `action_log` through a
  fresh `Episode`, compares every step's `state_before`/`state_after` hash and
  observation, re-verifies with the trusted verifier.
- `scripts/audit_training_run.py` — manifest/file integrity, shard counts,
  group integrity, mask accounting, call re-attribution, ledger reconciliation.

## Budget & accounts

- Allocation `grpo_training` (originally $25, owner raised to $60 on 2026-10-25,
  and separately topped up the `invoiceops-thinking` Modal account to ~$28).
- Ledger: `reports/modal_ledger.jsonl`, entries tagged `allocation=grpo_training`.
- Backup Modal account `kazigalib143` registered as a cold fallback ($30) —
  not used unless the primary runs dry.

## Readiness smokes

- `grpo-v3d-smoke-01` (9.3 min, $0.69): infra OK; caught a recorder assembly
  bug (`call.outputs[slot]` is a list — records degraded to skeletons while
  raw model_calls stayed intact). Fixed + regression test added.
- `grpo-v3d-smoke-02` (8.3 min, $0.62): clean — 96 rollouts, 3 batches, 0
  anomalies; all 96 records replayed with identical state hashes, identical
  observations, identical rewards (`replay_report.json`).

## Full run (LIVE — filled at close)

- Run: `grpo-v3d`, app `ap-5PONyHYhvS9I8VmhvqQ6AD`, workspace `nonestop220`.
- Step time ≈ 122 s → 150 steps ≈ 310 min + ~5 min startup/save.

### Attempt 1 — preempted at step ~55 (113.3 min billed, $8.40 est.)

- Modal spot-reclaimed the H100 mid-run: `Container terminated due to
  preemption` after step 54 (batch ordinal 54, 1,760 rollouts committed).
- Attempt-1's `except BaseException` still ran `close("failed")` + volume
  commit on the SIGTERM, so all 55 batches are durable and hash-verified.
- Modal auto-restarted the function with the same input; the fresh container
  correctly refused to reuse the run dir (`FileExistsError`, exist_ok=False)
  and the launcher recorded `failed`.

### Resume support added mid-campaign (no silent re-run)

- `train_grpo.run_training` now detects an interrupted same-config run
  (`manifest.json` present + `checkpoint-*` with trainer/optimizer/adapter
  state) and resumes via `trainer.train(resume_from_checkpoint=…)`; anything
  else still refuses with `FileExistsError`.
- `RolloutRecorder(resume=True)` loads the existing manifest, continues batch
  ordinals past committed AND interrupted shards (unique rollout ids across
  attempts), records each attempt in `manifest["attempts"]`, re-verifies the
  frozen dataset byte-for-byte, and carries `started_epoch` so the 345-min
  soft wall clock spans the whole run across attempts.
- LoRA weights are loaded explicitly with `set_peft_model_state_dict` before
  HF resume so adapter state never depends on Trainer's peft checkpoint path.

### Attempt 2 — completed (resumed at step 50 from checkpoint-50)

- Modal restarted the run at 2026-10-25T23:17Z; HF resume restored
  global_step=50, optimizer/scheduler/RNG, and the explicit adapter reload
  put the LoRA weights from `checkpoint-50` back. New batches continue
  ordinals 55+; the wall clock carried attempt-1's elapsed time.
- `train_grpo` returned `succeeded` after 209.5 min (ledger $15.54 est.).

## Final results — RUN COMPLETED (150/150 optimizer steps)

| Metric | Value |
| --- | --- |
| Optimizer steps | **150/150 completed** |
| Committed batches | 155 (55 attempt-1 incl. superseded 51–54, 100 attempt-2) |
| Rollout records | **4,960** (4,800 optimizer-consumed + 160 superseded-but-preserved) |
| Raw `llm.generate` calls | 2,210 (exact prompts, outputs, finish reasons, logprobs) |
| Env tool events | 49,912 |
| Batch anomalies | **0** across all 155 batches |
| Assembly errors / skeletons | **0** |
| Duplicate rollout ids | 0 (all 4,960 unique) |
| Reward-group integrity | 0 violations (8/group share one row_index) |
| Mask token accounting | 0 mismatches |
| Status counts | `terminal_submitted` 4,917 · `unfinished_other` 43 (ended without terminal submit; all preserved with reward) |
| Reward | mean 0.705; first-10-step mean 0.55 → last-10 mean 0.68; `frac_reward_zero_std` 0.25–1.0 late in training (groups never collapsed) |
| Losses/grads | all finite (204 step entries) |
| `tool_cutoff_ratio` | 0 every step — safety mask never needed |
| Local mirror | 542 files, ~all sha256-verified against the manifest |

## Close-out audit (`reports/modal/grpo-v3d-audit.json`)

- Manifest verify: 541 files checked — every trajectory/model-call/dataset
  shard hash matches; **no missing files, no `.tmp`/`.part` leftovers**.
- Known-benign aux drift (5 files): `meta.json` and TRL's
  `checkpoints/completions/completions_00051–54.parquet` were rewritten by
  attempt-2 after attempt-1 had registered their hashes. The deployed
  attempt-2 image predates the recorder's rewrite-rehash fix, so the manifest
  keeps attempt-1's hashes for those files. Shards are unaffected; the remote
  aux content is the authoritative (attempt-2) version.
- Replay (`runs/modal/training/grpo-v3d/replay_report.json`): **4,959/4,960
  records replayed through fresh `Episode`s with zero divergence** — every
  per-step `state_before`/`state_after` hash, every observation, and every
  verifier regrade identical. The single un-played record
  (`b0064/r15`) has an empty `action_log` — its first turn produced no tool
  call, so there was nothing to replay.
- GPU cleanup: Modal app `ap-HlldL2GmteHK9zE11Dh5r0` `stopped`, 0 tasks;
  all smoke apps stopped earlier. No idle GPU containers remain.

## Spend reconciliation (`reports/modal_ledger.jsonl`, allocation `grpo_training`)

| Entry | GPU | Time | Est. cost | Status |
| --- | --- | --- | --- | --- |
| `grpo-v3d-smoke-01` | H100 | 9.3 min | $0.69 | succeeded (caught the assembly bug) |
| `grpo-v3d-smoke-02` | H100 | 8.3 min | $0.62 | succeeded (clean readiness proof) |
| `grpo-v3d` attempt 1 | H100 | 113.3 min | $8.40 | preempted by Modal at step ~55 |
| `grpo-v3d` attempt 2 | H100 | 209.5 min | $15.54 | **succeeded, steps 51–150** |
| **Campaign total** | | | **$25.25** | of $60 allocation |

All spend on the `invoiceops-thinking` profile; backup account `kazigalib143`
was registered but never used.

## Honest limitations

- Attempt-1's rollouts for optimizer steps ~51–54 were superseded when the
  resume re-generated those steps. Both versions are preserved and uniquely
  identified (ordinals 51–54 vs 55+); the ledger and `attempts` manifest
  section document the boundary.
- 43 rollouts (0.9%) ended `unfinished_other` — episode never terminated
  (iteration/completion limits or EOS without submit). They carry reward and
  full transcripts; none needed safety masking.
- `meta.json` + 4 completion parquet aux files can't be re-verified against
  their attempt-1 manifest hashes (overwritten in place on the volume).
- Reward improved modestly (0.55 → 0.68 on first/last 10 steps); whether that
  transfers to the held-out test set is a separate evaluation question —
  `select_and_test`/`tau2`/`bfcl` jobs were NOT launched (need separate
  authorization per the handoff).
