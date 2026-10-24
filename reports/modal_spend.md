# Modal spend

The owner released **USD 9.50**, then USD 1.50 more (USD 11.00) for the post-training pipeline check. Rates in `modal_app/budget.yaml` are all-in: GPU price plus $0.50/h for CPU and memory, giving H100 $4.45/h and L40S $2.45/h. The GPU prices were read from Modal's pricing page on 2026-10-23: H100 $3.95/h, L40S $1.95/h.

| Started (UTC) | Job | GPU | Status | Minutes | Rate | Ledger cost |
|---|---|---|---|---|---|---|
| 2026-10-23T20:37:20Z | `inspect_models` | CPU | failed | 6.6 | $0.00 | $0.00 |
| 2026-10-23T20:46:28Z | `inspect_models` | CPU | failed | 0.3 | $0.00 | $0.00 |
| 2026-10-23T20:47:42Z | `inspect_models` | CPU | succeeded | 0.3 | $0.00 | $0.00 |
| 2026-10-23T20:50:50Z | `smoke_serve_candidate` | L40S | failed | 4.3 | $2.45 | $0.18 |
| 2026-10-23T21:07:13Z | `smoke_serve_candidate` | L40S | succeeded | 5.6 | $2.45 | $0.23 |
| 2026-10-23T21:13:12Z | `probe_and_dev` | L40S | succeeded | 7.7 | $2.45 | $0.31 |
| 2026-10-23T21:22:53Z | `smoke_train` | H100 | failed | 0.6 | $4.45 | $0.04 |
| 2026-10-23T21:25:15Z | `smoke_train` | H100 | succeeded | 4.3 | $4.45 | $0.32 |
| 2026-10-23T21:30:02Z | `test_candidate` | L40S | succeeded | 8.5 | $2.45 | $0.35 |
| 2026-10-23T21:39:15Z | `smoke_tau2` | H100 | failed | 3.3 | $4.45 | $0.24 |
| 2026-10-23T21:45:06Z | `smoke_tau2` | H100 | failed | 6.4 | $4.45 | $0.48 |
| 2026-10-23T22:24:55Z | `smoke_tau2` | H100 | succeeded | 7.3 | $4.45 | $0.54 |
| 2026-10-23T22:24:50Z | `bfcl_before` | L40S | succeeded | 10.4 | $2.45 | $0.42 |
| 2026-10-23T22:30:18Z | `probe_v2` | L40S | succeeded | 7.4 | $2.45 | $0.30 |
| 2026-10-23T22:35:44Z | `tau2_before` | H100 | succeeded | 15.6 | $4.45 | $1.16 |
| 2026-10-23T22:53:02Z | `test_reference` | H100 | succeeded | 4.7 | $4.45 | $0.35 |
| 2026-10-23T22:58:17Z | `tau2_reference` | H100 | succeeded | 11.5 | $4.45 | $0.85 |
| 2026-10-23T23:11:18Z | `dev_v2` | L40S | succeeded | 4.8 | $2.45 | $0.20 |
| 2026-10-24T05:02:41Z | `prompt_trial` v3a | L40S | succeeded | 9.3 | $2.45 | $0.38 |
| 2026-10-24T05:02:50Z | `prompt_trial` v3b | L40S | succeeded | 9.6 | $2.45 | $0.39 |
| 2026-10-24T05:14:29Z | `prompt_trial` v3c | L40S | succeeded | 12.1 | $2.45 | $0.49 |
| 2026-10-24T05:27:03Z | `test_prompt` v3c | L40S | succeeded | 6.1 | $2.45 | $0.25 |
| 2026-10-24T05:37:00Z | `prompt_trial` v3d | L40S | succeeded | 11.7 | $2.45 | $0.48 |
| 2026-10-24T05:49:07Z | `test_prompt` v3d | L40S | succeeded | 6.2 | $2.45 | $0.25 |
| 2026-10-24T06:08:21Z | `prompt_trial` v4 | L40S | succeeded | 10.4 | $2.45 | $0.43 |
| 2026-10-24T08:23:37Z | `smoke_post_train` | L40S | succeeded | 11.6 | $2.45 | $0.48 |
| | | | | | **Total** | **$9.11** |

The ledger multiplies wall-clock time by the rate. Wall-clock time includes image builds and container start-up before the GPU is attached, so the ledger is an overestimate. **Modal dashboard figure for the same period: not yet read** (to be filled in by the owner).

**Remaining by the ledger: $1.89 of the released $11.00.** The owner read about $2.00 of credit left on the Modal account before `smoke_post_train`. What each remaining job needs is in `docs/PROJECT_HANDOFF.md` §6.
