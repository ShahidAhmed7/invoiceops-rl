# Project Handoff: InvoiceOps RL

This is the brief for whoever continues the project. It covers what the project is, everything that has run, what we learned, the decisions made and why, what is left, what it will cost, and the rules to follow.

Last updated: 2026-10-24, at commit `fae71f1` on `main` (or a later commit that updated this file).

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
| 13 | GRPO training | **Next.** Needs the reviewer's approval of the training config and more credit (§7) |
| 14 | Selection, final test, τ²-bench and BFCL after | After training |
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
- Training uses a 16,384-token completion budget and a 20,480-token vLLM context.

## 5. Decisions made, and why

| Decision | Why | Where |
|---|---|---|
| Train, select checkpoints and run the final test with **prompt v3d** | Won the train/dev selection rule; ties v3c on test with fewer critical violations; leaves 16 learnable training tasks (2 never pass) | `modal_app/settings.py` `AGENT_PROMPT`, `modal_app/train_config.json` (`run_name: grpo-v3d`) |
| Context 131,072, 16,384 new tokens per turn, runner context guard | No context errors or mid-turn truncation; measured need is far smaller | `modal_app/settings.py`, `src/invoiceops/agents/openai_runner.py` |
| τ² user simulator context 32,768 | It shares the H100 at 45% memory (about 38k tokens of KV cache) | `settings.USER_SIM_MAX_MODEL_LEN` |
| Training: completion 16,384, vLLM context 20,480, batch 2 × 16, bf16, truncated rollouts masked, model at the pinned revision | Thorough rollouts fit; logits fit in memory; same weights as the evaluations | `modal_app/train_grpo.py` |
| `VLLM_USE_DEEP_GEMM=0` | DeepGEMM's FP8 kernels need nvcc 12.9+, and the image has 12.8; the FP8 reference failed to start without this | `modal_app/app.py` `ENV` |
| τ²-bench installed from a pinned checkout with `TAU2_DATA_DIR` | A pip install from git leaves out tau2's data | `modal_app/app.py` `serve_image` |
| `soundfile` in the BFCL environment | `qwen_agent` imports it without declaring it | same |
| `modal[api-proxy-support]` | The Modal client needs `python-socks` to connect through an HTTPS proxy | `pyproject.toml` |
| Reference model on test with prompt v2 (not v1) | v1 mostly measures whether a model guesses that a proposal is needed | `modal_app/launch.py` `test_reference` |

**Not reviewed yet.** The pre-GPU review approved the tasks, the verifier and prompt v2. Everything since was decided by the owner and the builder: the length settings, the runner guard, prompts v3a–v4 and choosing v3d, and the training config changes. Each is logged in [`review/builder-response.md`](review/builder-response.md) and the reports. The runbook asks the reviewer to approve the training config before `train_grpo`.

## 6. Money

**Released credit and ledger:**
- The project budget is USD 50. The owner has released **USD 11.00** (`spend_limit_usd` in `modal_app/budget.yaml`).
- The ledger (`reports/modal_ledger.jsonl`, 26 runs) shows **USD 9.11 spent**.

**The ledger overestimates.** It charges wall-clock time, including image builds and start-up, at the GPU rate. The owner read about $3.68 left on the Modal account before the last three prompt runs. Always compare against the Modal dashboard; the per-job table is in [`../reports/modal_spend.md`](../reports/modal_spend.md).

**Rates** (Modal pricing page, 2026-10-23): H100 $3.95/h and L40S $1.95/h. Plus $0.50/h for CPU and memory, the guard uses **H100 $4.45/h, L40S $2.45/h**.

**A second Modal account** with about $29.50 was mentioned by the owner. Using it needs its token in the environment and a decision on how the ledger tracks two accounts. Neither is done.

**What the remaining jobs need.** The guard refuses a job unless *ledger spend + the job's worst case* (hard timeout × rate) fits under `spend_limit_usd`:

| Job | GPU, hard limit | Worst case | Plan cap | Typical actual (ledger) |
|---|---|---|---|---|
| `train_grpo` | H100, 250 min | **$18.54** | $15.80 | unknown; the wall-clock stop is 225 min |
| `select_and_test` | L40S, 40 + 10 + 30 min | $3.27 | $2.45 | about $1 (smoke chain: $0.48) |
| `tau2_after` | H100, 60 min | $4.45 | $3.30 | about $1.20 (`tau2_before`: $1.16) |
| `bfcl_after` | L40S, 35 min | $1.43 | $0.80 | about $0.45 (`bfcl_before`: $0.42) |

- **To start training:** `spend_limit_usd` must be at least 9.11 + 18.54 = **27.65**.
- **For the whole remaining programme**, released step by step, the worst cases sum to $27.69. Real spend will be lower.
- **Only the owner raises `spend_limit_usd`.**

## 7. Next steps, in order

### 7.1 Before training
1. **Reviewer approval of the training config.** Review `modal_app/train_grpo.py` `DEFAULTS` and `modal_app/train_config.json`:
   - prompt v3d, run `grpo-v3d`;
   - LoRA r=16, alpha 32, learning rate 2e-5;
   - 8 generations per prompt; 2 per device × 16 accumulation steps (32 rollouts per step);
   - 150 steps, training temperature 1.0, at most 30 tool-calling iterations;
   - completion 16,384, vLLM context 20,480;
   - 144 generated training variants plus the 36 training tasks;
   - 225-minute wall-clock stop.

   Record the approval in `docs/review/`.
2. **Release credit:** `spend_limit_usd` ≥ 27.65 (owner).
3. Optional: decide whether to use the second Modal account (§6).

### 7.2 Training
```bash
uv run --group modal python -m modal_app.launch train_grpo --dry-run
uv run --group modal python -m modal_app.launch train_grpo
```
- **Watch the first steps' `step_time`.** The smoke run took 23–27 s per step of 8 rollouts. The real run has 32 rollouts per step; if time scaled linearly, 150 steps would take about 250 min and the 225-minute stop would end training near step 135. That is acceptable: the final adapter is saved either way.
- **Also watch** `sampling/importance_sampling_ratio` (0.45–0.79 in the smoke run), `frac_reward_zero_std` (groups with no learning signal), and `completions/clipped_ratio` (should stay near 0).
- **Success:** `checkpoints` and `final_adapter` exist under `/runs/train/grpo-v3d`, and `log_history` shows rewards.
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
| Training time vs the 225-minute stop | Training may stop before 150 steps | Watch `step_time`; acceptable, but record the step reached |
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
| `modal_app/train_grpo.py`, `train_config.json` | GRPO training job and its config |
| `modal_app/tau2_driver.py`, `vllm_server.py` | τ²-bench driver; vLLM server start-up |
| `reports/` | `baseline.md`, `external_baseline.md`, `compatibility.md`, `prompt_trials.md`, `transcript_audit.md`, `modal_spend.md`, `modal/*.json`, `modal_ledger.jsonl`, `model_verification.json` |
| `docs/review/` | Pre-GPU review guide, sign-off, builder responses, completed review records |
| `BUILD_PLAN.md`, `docs/MODAL_RUNBOOK.md` | Full plan; GPU runbook |
