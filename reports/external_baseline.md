# External baseline: BFCL (untrained candidate)

The BFCL score for the untrained candidate is frozen here so the trained model can be compared against it.

## Settings

| | |
|---|---|
| Model | `Qwen/Qwen3-4B-Instruct-2507` @ `cdbee75f17c01a7cc42f958dc650907174af0554`, function-calling handler `Qwen/Qwen3-4B-Instruct-2507-FC` |
| Benchmark | `bfcl-eval` 2026.3.23, `bfcl generate --backend vllm --skip-server-setup --num-threads 16 --temperature 0.001`, then `bfcl evaluate` |
| Serving | vLLM 0.31.0 on an L40S, `--max-model-len 131072`, Hermes tool-call parser. BFCL caps output at 4,096 tokens per request (its own setting). |
| Categories | `simple_python`, `multiple`, `parallel`, `parallel_multiple`, `irrelevance`, `live_simple`, `live_multiple`, `multi_turn_base` (`settings.BFCL_CATEGORIES`), every case in each |
| Job | `bfcl_before`, 2026-10-23, `reports/modal/bfcl_before.json` |

## Accuracy by category

| Category | Accuracy |
|---|---|
| `simple_python` | 95.25% |
| `multiple` | 94.50% |
| `parallel` | 93.00% |
| `parallel_multiple` | 90.00% |
| `irrelevance` | 88.75% |
| `live_simple` | 78.29% |
| `live_multiple` | 76.83% |
| `multi_turn_base` | 27.00% |

The overall figures BFCL prints (Overall 21.68%, Multi Turn Acc 6.75%) average over categories this run did not include, scoring them as zero. They are **not** a score for this model and should not be quoted. Compare category by category.

## τ²-bench

| | |
|---|---|
| Benchmark | τ²-bench @ `318fa35b1431a42e3ffdad05197378f506fac9d4`, retail domain, test split (40 tasks), 4 trials, seed 300 |
| Evaluation | `EvaluationType.ENV`: database state and environment assertions only, no LLM judge |
| Agent | the untrained candidate, temperature 0.7, top-p 0.8, on vLLM (H100, 40% memory, 131,072-token context) |
| Simulated customer | `Qwen/Qwen3-30B-A3B-Instruct-2507-FP8` @ `5a5a776`, temperature 0.0, on the same H100 (45% memory, 32,768-token context) |
| Job | `tau2_before`, 2026-10-23, `reports/modal/tau2_before.json` (per-task rewards inside) |

| Metric | Untrained candidate |
|---|---|
| pass^1 (mean reward over all simulations) | **36.9%** |
| pass^4 (tasks solved in all 4 trials) | **20.0%** |
| Simulations | 160, none without a reward |
| Wall clock | 9.5 minutes for the simulations (3.6 s per simulation at concurrency 16) |

Both the agent and the customer are local open models, and grading is ENV-only, so these numbers are **not comparable with the public leaderboard**. They exist for the before/after comparison: `tau2_after` must use the same customer model, seed, trials and settings.
