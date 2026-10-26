# Project Handoff: InvoiceOps RL

This is the brief for whoever continues the project. It covers what the project is, everything that has run, what we learned, the decisions made and why, what is left, what it will cost, and the rules to follow.

Last updated: 2026-10-26 (Asia/Dhaka), after the local training audit.

**Execution prompt:** [`FULL_TRAINING_HANDOFF_PROMPT.md`](FULL_TRAINING_HANDOFF_PROMPT.md)
contains the full-training handoff, including the $25 allocation, required raw-trajectory
logging implementation, GPU readiness checks and verified local artifact delivery.

**Training audit:** [Findings and effective parameters](../reports/training_audit.md).
All 275 tests and oracle checks on all 180 training rows pass. The generated curriculum is
now balanced (60/60/60), and a project trainer wrapper masks unfinished EOS tool calls and
excludes them from the reward baseline. The owner clarified **$25 for training alone**, with evaluations separate. The current
250-minute training hard limit estimates $18.54 at the configured rate, so it fits that
allocation. After the audit the owner requested larger limits: training context is now 131,072
and completion budget 24,576. The new limits need GPU memory validation. Released-credit
limits were not changed and no GPU jobs were launched; the existing $11 release still blocks launch.

**Evaluation audit:** [Definitions, fixes and limits](../reports/evaluation_audit.md).
Strict verifier success is the primary metric. Fixed incomplete pass@k/pass^k accounting,
blocked-attempt counting and tool-call budget overshoot. Checkpoint selection rejects
incomplete dev runs and deduplicates saved adapters. Recounting 372 local episodes changes
no headline success rates; 21 committed summaries pass arithmetic checks. Test has only
four companies and has already been inspected during prompt work, so gains are exploratory.

**Latest check:** `Qwen/Qwen3-4B-Thinking-2507` passed the inference pipeline smoke, but scored
8/12 on dev with one attempt per task. No truncation or context stops occurred; maximum
per-turn output was 5,922 tokens and maximum prompt plus completion was 12,299. Generation
cost 12.54× as many tokens per episode as the existing instruct dev baseline, without an
observed accuracy improvement. The samples and concurrency differ. The active candidate and
training config remain Instruct-2507 with v3d. See [`../reports/thinking_smoke.md`](../reports/thinking_smoke.md).

**Read first:**
1. This file.
2. [`../BUILD_PLAN.md`](../BUILD_PLAN.md): the full plan, verified facts and phases.
3. [`MODAL_RUNBOOK.md`](MODAL_RUNBOOK.md): how to launch GPU jobs.

The reports under [`../reports/`](../reports/) hold every number quoted here.

---

## 1. The project in one paragraph

InvoiceOps is a verifiable accounts-payable environment for training and evaluating tool-using agents. An agent acts as the AP assistant of a fictional company. It investigates one supplier invoice through 15 typed tools (purchase orders, receipts, supplier records, history, policy documents) and records what the company's written policy requires: pay, hold or reject, with any clarification or approval the policy demands. A trusted verifier grades the **final system state and action history** with a strict 0/1 reward.

There are 72 tasks: 12 families across 12 fictional companies, split **by company** into 36 train, 12 dev and 24 test.

**The experiment:** baseline `Qwen/Qwen3-4B-Instruct-2507`, train it with GRPO and LoRA on the training companies, then compare before and after on the held-out test companies and on two external benchmarks (τ²-bench retail, BFCL). The whole project has a USD 50 Modal budget.

## 2. Where things stand

| Phase | What | Status |
|---|---|---|
| 0–9 | Environment, tasks, verifier, adapters, containers, local evaluation | **Done** (no GPU) |
| 10 | Pre-GPU human review | **Approved** at re-check ([`review/signoff/pre-gpu.md`](review/signoff/pre-gpu.md)) |
| 11A | Model checks, serving, external baselines | **Done**: models pinned, serving and tool parsing verified, BFCL and τ²-bench baselines for the 4B and the 30B reference |
| 11B | GRPO smoke test | **Done**: 3 steps, rewards flow, checkpoint saved |
| 12 | Baselines on our tasks | **Done**: probes, dev, test for prompts v1/v2/v3c/v3d, reference model on test |
| 12+ | Prompt engineering before training | **Done**: v3d chosen for training ([`../reports/prompt_trials.md`](../reports/prompt_trials.md)) |
| 14 (pipeline) | Post-training chain (LoRA serving, selection, merge, merged serving) | **Done** on the smoke adapter |
| 13 | GRPO training | **Done**: `grpo-v3d` completed 150/150 steps on 2026-10-26; 4,960 rollout trajectories preserved, verified and replayed ([`../reports/grpo_training_campaign.md`](../reports/grpo_training_campaign.md)) |
| 14 | Selection, final test, τ²-bench and BFCL after | **Next.** Uses `final_adapter`/`checkpoint-*` from `grpo-v3d`; needs a fresh credit release |
| 15 | Showcase release | After 14 |

## 3. Results so far

### 3.1 Our tasks: test split (24 held-out tasks × 4 attempts)

| Agent | Prompt | Task-mean success | 95% CI | pass@4 | pass^4 | Source |
|---|---|---|---|---|---|---|
| Always pay (script) | – | 29.2% | | | | `README.md` |
| Untrained 4B | v1 | 7.3% | 1.0–15.6% | 16.7% | 0.0% | `reports/modal/test_candidate.json` |
| Untrained 4B | v2 | 41.7% | 28.1–55.2% | 70.8% | 12.5% | same |
| Untrained 4B | v3c | **72.9%** | 56.2–87.5% | 79.2% | 54.2% | `reports/modal/test_prompt-v3c.json` |
| Untrained 4B | **v3d (training prompt)** | **71.9%** | 56.2–85.4% | 83.3% | 50.0% | `reports/modal/test_prompt-v3d.json` |
| Reference 30B-A3B FP8 | v2 | 61.5% | 43.8–78.1% | 70.8% | 50.0% | `reports/modal/test_reference.json` |

Train and dev results for every prompt are in [`../reports/prompt_trials.md`](../reports/prompt_trials.md).

**The test split has been looked at twice.** v3c and v3d each had one test run, and the transcript audit read test transcripts. The trained model should get **one** final test run.

### 3.2 External benchmarks (before training)

| Benchmark | Untrained 4B | Reference 30B-A3B | Source |
|---|---|---|---|
| τ²-bench retail, test split, 4 trials, ENV grading, local 30B customer | pass^1 36.9%, pass^4 20.0% | pass^1 43.8%, pass^4 27.5% | `reports/external_baseline.md` |
| BFCL `simple_python` / `multiple` / `parallel` / `parallel_multiple` | 95.25 / 94.50 / 93.00 / 90.00% | not run | same |
| BFCL `irrelevance` / `live_simple` / `live_multiple` / `multi_turn_base` | 88.75 / 78.29 / 76.83 / 27.00% | not run | same |

Neither benchmark is comparable with its public leaderboard (local models, ENV-only grading). Do not quote BFCL's printed "Overall"; it averages over categories we did not run.

### 3.3 GRPO training run `grpo-v3d` (2026-10-26)

- **150/150 optimizer steps completed** — 4,800 optimizer-consumed rollouts (4,960 records preserved including 160 superseded by the preemption resume), LoRA adapter in `final_adapter/`, checkpoints at 25/50/75/100/125/150.
- Training-signal metrics: reward mean 0.705 overall, 0.55 → 0.68 (first vs last 10 steps); `frac_reward_zero_std` 0.25–1.0 late (healthy group variance); all losses/grads finite; `tool_cutoff_ratio` 0 throughout.
- Trajectory archive: 155 committed batches, 2,210 raw vLLM calls, 49,912 env events; every shard sha256-verified in the manifest; **4,959/4,960 records replayed with zero state/observation/reward divergence** (`runs/modal/training/grpo-v3d/replay_report.json`).
- Whether it improved the model is **untested** — selection/test/τ²/BFCL are phase 14 and need their own credit release.
- Full detail: [`../reports/grpo_training_campaign.md`](../reports/grpo_training_campaign.md); integrity audit: `reports/modal/grpo-v3d-audit.json`.

## 4. What we learned (read before changing anything)

**Prompting:**
- **The prompt is the biggest lever measured so far.** v2 to v3c/v3d moved test success from 41.7% to about 72%, beating the 30B reference with v2.
- **The 4B model needs a numbered procedure.** A company-style prompt without one (v4) scored like v2 on train and dev, with 56% of attempts committing a critical violation: it read the policy and then paid by default.
- **Small wording changes can break the policy read.** "Search, don't guess IDs" (v3a, v3b) made the model treat a search hit, which is only a title, as the policy, so it never opened it. v3c fixed this by saying to open the policy with `get_document` and read all of it.
- **Prompting has plateaued.** v3d beat v3c by 9 points on train and dev but tied on test. Further prompt rounds on 48 tasks are mostly noise.

**Failure modes** ([`../reports/transcript_audit.md`](../reports/transcript_audit.md)):
- v1 skips the payment proposal; v2 skips the disposition.
- Credit notes are cited but not subtracted, or a tenth is subtracted (a cents slip).
- The model asks receiving, then submits without reading the reply.
- It picks plausible but wrong reason codes (`quantity_exceeds_receipt` where `short_receipt` is required).

**Things to know about the tasks and grading:**
- **Injection family F10 tests nothing at present.** The model never opened the planted attachment in any of 16 test attempts, so F10 measures receipt and amount logic, not injection resistance.
- **The 30B reference never requests approval** (0 of 96 attempts) and applies generic rules instead of company rules.
- **Grading reproduces exactly:** all 1,416 downloaded episodes (14 runs) replay to the same observations, final state and verdict. The v3d runs and the post-training smoke test were not downloaded.

**Context and lengths** ([`../reports/compatibility.md`](../reports/compatibility.md)):
- Episodes peak around 8–10k tokens; nothing was truncated in any run.
- Serving uses a 131,072-token context and 16,384 new tokens per turn. A runner guard keeps every request inside the context.
- Training now uses a 24,576-token whole-rollout completion budget and a 131,072-token vLLM context, at the owner's request. The recorded GPU smoke used the previous 16,384 / 20,480 limits.

## 5. Decisions made, and why

| Decision | Why | Where |
|---|---|---|
| Train, select checkpoints and run the final test with **prompt v3d** | Won the train/dev selection rule; ties v3c on test with fewer critical violations; leaves 16 learnable training tasks (2 never pass) | `modal_app/settings.py` `AGENT_PROMPT`, `modal_app/train_config.json` (`run_name: grpo-v3d`) |
| Context 131,072, 16,384 new tokens per turn, runner context guard | No context errors or mid-turn truncation; measured need is far smaller | `modal_app/settings.py`, `src/invoiceops/agents/openai_runner.py` |
| τ² user simulator context 32,768 | It shares the H100 at 45% memory (about 38k tokens of KV cache) | `settings.USER_SIM_MAX_MODEL_LEN` |
| Training: completion 24,576, vLLM context 131,072, batch 2 × 16, bf16, model at the pinned revision | Owner requested more room; new limits and trainer wrapper need GPU validation; audited tool cutoffs now excluded | `modal_app/train_grpo.py`, `reports/training_audit.md` |
| `VLLM_USE_DEEP_GEMM=0` | DeepGEMM's FP8 kernels need nvcc 12.9+, and the image has 12.8; the FP8 reference failed to start without this | `modal_app/app.py` `ENV` |
| τ²-bench installed from a pinned checkout with `TAU2_DATA_DIR` | A pip install from git leaves out tau2's data | `modal_app/app.py` `serve_image` |
| `soundfile` in the BFCL environment | `qwen_agent` imports it without declaring it | same |
| `modal[api-proxy-support]` | The Modal client needs `python-socks` to connect through an HTTPS proxy | `pyproject.toml` |
| Reference model on test with prompt v2 (not v1) | v1 mostly measures whether a model guesses that a proposal is needed | `modal_app/launch.py` `test_reference` |

**Not reviewed yet.** The pre-GPU review approved the tasks, the verifier and prompt v2. Everything since was decided by the owner and the builder: the length settings, the runner guard, prompts v3a–v4 and choosing v3d, and the training config changes. Each is logged in [`review/builder-response.md`](review/builder-response.md) and the reports. The runbook asks the reviewer to approve the training config before `train_grpo`.

## 6. Money

**Released credit and ledger:**
- The project budget is USD 50. The owner has released **USD 11.00** (`spend_limit_usd` in `modal_app/budget.yaml`).
- The ledger (`reports/modal_ledger.jsonl`, 27 runs) shows **USD 10.0722 spent** (USD 10.07 rounded).

**The ledger overestimates.** It charges wall-clock time, including image builds and start-up, at the GPU rate. The owner read about $3.68 left on the Modal account before the last three prompt runs. Always compare against the Modal dashboard; the per-job table is in [`../reports/modal_spend.md`](../reports/modal_spend.md).

**Rates** (Modal pricing page, 2026-10-23): H100 $3.95/h and L40S $1.95/h. Plus $0.50/h for CPU and memory, the guard uses **H100 $4.45/h, L40S $2.45/h**.

**The second Modal account** was configured privately on 2026-10-26, with USD 26 credit
reported by the owner, for the authorized thinking smoke. Use `uv run --env-file .env --group modal`
for that account (private profile `invoiceops-thinking`). Credentials are not committed. New
ledger entries record `account_profile`; prior entries are unchanged. Account balance was not
read from the dashboard. This configuration and the smoke authorization do not release
additional credit or authorize a full training run.

**What the remaining jobs need.** The guard refuses a job unless *ledger spend + the job's worst case* (hard timeout × rate) fits under `spend_limit_usd`:

| Job | GPU, hard limit | Worst case | Plan cap | Typical actual (ledger) |
|---|---|---|---|---|
| `train_grpo` | H100, 360 min | **$26.70** | $26.70 | **done** — $23.94 over two attempts (preempted once, resumed); soft stop 345 min never fired |
| `select_and_test` | L40S, 40 + 10 + 30 min | $3.27 | $2.45 | about $1 (smoke chain: $0.48) |
| `tau2_after` | H100, 60 min | $4.45 | $3.30 | about $1.20 (`tau2_before`: $1.16) |
| `bfcl_after` | L40S, 35 min | $1.43 | $0.80 | about $0.45 (`bfcl_before`: $0.42) |

- **`train_grpo` is spent** — the campaign billed $25.25 under the
  `grpo_training` allocation (USD 60, owner-authorized 2026-10-25), so the old
  released-credit math no longer applies.
- **For the remaining phase-14 programme** (`select_and_test`, `tau2_after`,
  `bfcl_after`), the worst cases sum to ~$8 under the same allocation's
  remaining headroom, but each still needs its own launch authorization.
- **Only the owner raises `spend_limit_usd`.**

## 7. Next steps, in order

### 7.1 Before training — superseded (owner authorized the campaign directly)
1. ~~**Reviewer approval of the training config.**~~ The owner authorized the full run
   directly on 2026-10-25 ("complete it... no human in the loop") and raised the
   `grpo_training` allocation to USD 60; the config ran as reviewed below:
   - prompt v3d, run `grpo-v3d`;
   - prompt v3d, run `grpo-v3d`;
   - LoRA r=16, alpha 32, learning rate 2e-5;
   - 8 generations per prompt; 2 per device × 16 accumulation steps (32 rollouts per step);
   - 150 steps, training temperature 1.0, at most 30 tool-calling iterations;
   - completion 24,576, vLLM context 131,072; validate GPU startup and memory at these new limits;
   - 144 generated training variants plus the 36 training tasks;
   - 345-minute wall-clock stop (owner raised it; 360-min Modal hard timeout).

2. **Credit:** covered by the `grpo_training` allocation (USD 60 authorized);
   campaign spent $25.25 by ledger.
3. **Account:** profile `invoiceops-thinking`; backup `kazigalib143` registered
   but unused.

### 7.2 Training — **DONE (2026-10-26)**

`grpo-v3d` completed **all 150 optimizer steps** in two attempts: the first was
preempted by Modal at ~step 55 ($8.40), the second resumed from `checkpoint-50`
and finished ($15.54). Step time ≈124 s; the soft wall clock (345 min, carried
across attempts) never fired. Every rollout is durably archived and sha256
verified; **4,959/4,960 records replayed with zero divergence** (one record had
an empty action log — nothing to replay). Reward mean 0.705, trending 0.55 →
0.68 (first vs last 10 steps); `frac_reward_zero_std` stayed 0.25–1.0 late in
training; `tool_cutoff_ratio` was 0 every step. Artifacts: remote
`invoiceops-runs:/train/grpo-v3d`, mirrored to `runs/modal/training/grpo-v3d`
(542 files). Reports: `reports/grpo_training_campaign.md` (full detail),
`reports/modal/grpo-v3d-audit.json` (integrity audit). The same
`launch train_grpo` entry point now resumes an interrupted same-config run
from its latest checkpoint instead of failing — rerun only with a **new**
`--run-name` for a fresh lineage.
- **Never re-run a job that hit its hard timeout.**

### 7.3 Final evaluation
1. `launch select_and_test`. This picks the checkpoint on **dev** with v3d (2 attempts, the last 3 checkpoints plus the final adapter), merges it, and runs the test split **once** with v3d (`test-trained-v3d`).
2. `launch tau2_after`, with the same customer, seed and trials as `tau2_before`.
3. `launch bfcl_after`, with the same categories as `bfcl_before`. **Do not run it before training**; it needs the merged model.
4. Write `reports/final.md` with before and after:
   - test split: the trained model with v3d against the untrained 4B with v3d (71.9%) and v3c (72.9%);
   - τ²-bench and each BFCL category;
   - confidence intervals, critical violations, per-family results;
   - null or negative results stated plainly.

### 7.4 Strongly recommended checks
- **Is the trained model just following the prompt?** Evaluate it with prompt v2 as well as v3d, on dev (not test). If it improves only under v3d, say so.
- **A clean held-out number.** The test split has been seen twice. Generating fresh test companies with the task builder would give an untouched held-out set. That is a task-design change and needs review.

## 8. Open issues and risks

| Issue | Effect | Suggested action |
|---|---|---|
| F10 attachments are never opened by the model | The injection family tests receipt logic, not injection resistance | Make the attachment necessary to solve the task (task-design change, needs review) |
| `quantity_exceeds_receipt` vs `short_receipt` | An easy reason-code trap (8/8 attempts on two test tasks) | The verifier is right; consider clearer policy wording (task change) |
| Test split looked at twice | The trained model's test number is a third look | One final test run only; report it as such |
| ~~Training time vs the 225-minute stop~~ Modal spot preemption can kill a container mid-run | ~~Training may stop before 150 steps~~ The auto-restarted function used to die on `FileExistsError` | Resolved 2026-10-26: `run_training` resumes a same-config interrupted run from its latest checkpoint (per-attempt lineage in `manifest["attempts"]`); run finished all 150 steps |
| GRPO signal | With v3d, 18 of 36 training tasks always pass and 2 never pass, giving no gradient | Generated variants add more; watch `frac_reward_zero_std` |
| `docs/review/status.md` header still says "GPU phases: NOT approved" | Stale reviewer record; the sign-off approves | The reviewer updates it (reviewer-owned file) |
| `Qwen/Qwen3-8B` fallback supports only 40,960 tokens | It would fail with the 131,072 default | Pass a smaller `max_model_len` if it is ever used |
| Ledger overestimates spend | Jobs may be refused although credit remains | Reconcile with the dashboard; the owner adjusts `spend_limit_usd` |
| Environment network access | Modal needs more hosts than the client's own API | Allow `api.modal.com`, `api.modal2.com`, `*.modal.com` (incl. `input-plane.us-east.modal.com`) and `*.modal-storage.com` (volume downloads) |

## 9. How to work on this project

- **Commits and pushes:** commit as **ShahidAhmed7 &lt;ahmedshahid2929@gmail.com&gt;** and push to **`main`**. No co-author lines or AI attribution in commits. No pull request unless the owner asks.
- **Never raise `spend_limit_usd`** or the rates yourself; only the owner releases credit. Never put tokens in files, commits or chat.
- **One job at a time unless the guard's worst cases fit together.** After each job: read `reports/modal/<job>.json` and its ledger line, check the success condition, and commit the reports.
- **Re-runs:** re-run a failed job only after fixing the cause and running the checks below. Never re-run one that hit its hard timeout.
- **Test-split discipline:** design and select on train and dev only; never tune on test transcripts.
- **Before every push:**
  ```bash
  uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pytest
  ```
  CI also runs `invoiceops build-tasks --check`, `openenv validate`, and the container isolation check.
- **Report real numbers only,** including bad ones. If something did not run, say so.
- **Downloading transcripts** (needs `*.modal-storage.com` allowed):
  ```bash
  uv run --group modal modal volume get invoiceops-runs invoiceops/<run-tag> <local-dir>
  ```
  Episodes are `EpisodeRecord` JSON (`src/invoiceops/runs.py`); replaying them through `Episode` and `verify_episode` must reproduce the recorded verdict.

## 10. Map of the important files

| Path | What it is |
|---|---|
| `src/invoiceops/` | Environment: episode and tools, verifier, tasks and world builder, agents (oracle, scripted, OpenAI-compatible runner), adapters (TRL, OpenEnv), evaluation, CLI |
| `src/invoiceops/agents/prompts/system_*.md` | Prompts: v1, v2 (frozen, reviewed), v3a–v3d, v4. **v3d is the training prompt** |
| `tasks/` | 72 tasks: `public.json` (agent-visible) and `private.json` (verifier only) |
| `modal_app/launch.py` | The only way to start GPU jobs: budget guard, ledger, per-call time limits, `--prompt` for prompt jobs |
| `modal_app/app.py` | Modal functions and images (serve, train, CPU) |
| `modal_app/budget.yaml` | Rates, released credit, per-job caps and hard timeouts |
| `modal_app/settings.py` | Pinned model revisions, benchmark versions, lengths, decoding, `AGENT_PROMPT` |
| `modal_app/train_grpo.py`, `train_config.json` | GRPO training job and its config; resumes an interrupted same-config run from the latest checkpoint |
| `src/invoiceops/adapters/rollout_log.py`, `modal_app/trajectory_logging.py`, `modal_app/grpo_safety.py` | Durable per-rollout trajectory recorder (atomic shards + manifest), vLLM call capture, safety-mask batch hooks |
| `modal_app/sync_run.py` | Incremental volume→local mirror with sha256 verification (`--once` / `--verify-only`) |
| `scripts/audit_training_run.py`, `scripts/replay_rollouts.py` | Offline audit of a mirrored run; per-record replay/regrade against frozen bundles |
| `modal_app/tau2_driver.py`, `vllm_server.py` | τ²-bench driver; vLLM server start-up |
| `reports/` | `baseline.md`, `external_baseline.md`, `compatibility.md`, `prompt_trials.md`, `transcript_audit.md`, `modal_spend.md`, `modal/*.json`, `modal_ledger.jsonl`, `model_verification.json` |
| `docs/review/` | Pre-GPU review guide, sign-off, builder responses, completed review records |
| `BUILD_PLAN.md`, `docs/MODAL_RUNBOOK.md` | Full plan; GPU runbook |
