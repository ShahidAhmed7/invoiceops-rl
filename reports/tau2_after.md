# tau2 after training: dev-selected checkpoint 125

Completed 2026-10-26. The selected step-125 model was evaluated on the same 40 retail test
tasks × 4 trials as the untrained baseline, with the same local simulated customer,
seed and ENV-only grading protocol.

| Metric | Untrained | Trained step 125 | Change |
|---|---:|---:|---:|
| Mean reward / pass^1 | 59/160 (36.875%) | **62/160 (38.750%)** | +1.875 pp |
| pass^4 (all trials succeed) | 8/40 (20.000%) | **9/40 (22.500%)** | +2.500 pp |
| Simulations with rewards | 160/160 | 160/160 | |

The gain is small. A paired task bootstrap of mean-reward differences (40 tasks,
10,000 resamples, seed 0) gives a 95% interval of **−6.25 to +10.00 percentage points**.
This experiment does not establish a reliable improvement or regression on tau2.

## Matched protocol

- tau2-bench commit `318fa35b1431a42e3ffdad05197378f506fac9d4`, retail domain,
  test split, four trials, seed 300, concurrency 16.
- Grading: `EvaluationType.ENV`, database state and environment assertions only.
  No LLM judge, natural-language assertion grading or public leaderboard comparison.
- Agent: pinned `Qwen/Qwen3-4B-Instruct-2507` base
  `cdbee75f17c01a7cc42f958dc650907174af0554`, merged with `grpo-v3d/checkpoint-125`.
- Adapter SHA-256: `451f24b51081dbe1e2779a07f30bbb2fee884291a4e948b1951f9a454aaa18f7`.
  Provenance matches the selected InvoiceOps and BFCL model.
- Agent decoding: temperature 0.7, top-p 0.8; 131,072-token context.
- Simulated customer: `Qwen/Qwen3-30B-A3B-Instruct-2507-FP8`, revision
  `5a5a776300a41aaa681dd7ff0106608ef2bc90db`, temperature 0.0, 32,768-token context.
- Both served by vLLM 0.31.0 on one H100, agent 40% and customer 45% GPU memory.
- Funded account profile: `kazigalib143`.

## Coverage and arithmetic audit

All 160 simulations have unique simulation IDs and unique `(task_id, trial)` pairs.
Every one of the 40 baseline task IDs has exactly trials 0, 1, 2 and 3, a transcript
and a reward. Recomputed per-task means, overall mean and pass^4 match the saved summary
exactly. All three remote artifact files match the download manifest's sizes and hashes.

For 159 normally terminated simulations, the product of the saved reward-breakdown
components equals the reported reward. Task 55, trial 0 reached the benchmark's maximum
step count and received the harness's explicit zero reward for premature termination.
It remains in the denominator as a scored failure; it was not discarded or rerun.
The other 159 simulations ended with `user_stop`. No HTTP 400 or 500 responses occurred.

This is an independent coverage/arithmetic audit of the official saved grading results,
not a second replay of all tau2 environments. The full transcripts and reward details
are retained for subsequent grading audits.

## Non-fatal log warnings

Nineteen golden-action warnings cover five expected fallback patterns in tasks 38,
39, 55, 64 and 68: invalid first identity lookups, or an exchange attempted on a pending
order before using the pending-order modification tool. The pinned golden sequences
include the subsequent valid actions. These warnings do not indicate missing rewards;
the upstream ENV evaluator catches the failed actions and continues the golden sequence.
See the [pinned task definitions](https://raw.githubusercontent.com/sierra-research/tau2-bench/318fa35b1431a42e3ffdad05197378f506fac9d4/data/tau2/domains/retail/tasks.json)
and [ENV evaluator](https://raw.githubusercontent.com/sierra-research/tau2-bench/318fa35b1431a42e3ffdad05197378f506fac9d4/src/tau2/evaluator/evaluator_env.py).

LiteLLM also warns that the local aliases `agent` and `user-sim` have no price mapping.
Those token-cost estimates are not used for grading or our Modal wall-clock cost ledger.

ENV-only grading is intentionally narrower than full conversational correctness:
natural-language answers are not judged, so a task that requires no database change can
receive a database-state success without establishing that the spoken answer is correct.
The same limitation applies to the frozen untrained comparison.

## Raw artifacts and cost

- Full raw results, 160 transcripts and reward details:
  `runs/modal/tau2-selected-checkpoint-125/results.json` (about 12.6 MB).
- Run config, summary and download manifest: `runs/modal/tau2-selected-checkpoint-125/`.
- Launcher result: `reports/modal/tau2_after.json`.
- Coverage, arithmetic, per-task differences and artifact hashes:
  `reports/modal/tau2_after_audit.json`.
- Server and harness log: `runs/local-logs/tau2-selected-checkpoint-125.log`.
- Remote backup: funded account's `invoiceops-runs`, `/tau2/after`.
- [Modal run](https://modal.com/apps/kazigalib143/main/ap-tMsFFCqWPQPGu0JgQ0U4vG).

Estimated Modal cost: **$1.3429**, including 18.1 minutes of launcher wall time at the
configured $4.45/hour rate. Simulations themselves took 581.6 seconds. This is a ledger
estimate, not an account invoice. The job's hard timeout is 60 minutes, priced at $4.45
before launch, within the funded account's separate $10 post-training allocation.

Raw directories are gitignored and preserved locally. Neither the baseline nor any
failed trajectory was overwritten or omitted from the score.
