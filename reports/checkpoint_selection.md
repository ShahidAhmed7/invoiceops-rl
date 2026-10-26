# Development checkpoint selection

Completed 2026-10-26 on the funded Modal account (`kazigalib143`). The pre-existing
selection plan compared four distinct saved adapters: final step 150, then steps 125,
100 and 75. Each received the same 12 dev tasks × 2 attempts, prompt v3d, temperature
0.7, top-p 0.8, 131,072-token context, 16,384 output tokens per turn and 40 tool calls.
Only strict task-mean verifier success on dev determined the winner. Test outcomes
were not used for selection.

| Checkpoint | Dev passes | Task-mean success |
|---|---:|---:|
| **Step 125 — selected** | **24/24** | **100.00%** |
| Final step 150 | 23/24 | 95.83% |
| Step 100 | 22/24 | 91.67% |
| Step 75 | 21/24 | 87.50% |

Step 125 was the unique winner. A perfect score on 12 dev tasks with two attempts
does not establish perfect generalization; the selected model's test result is
reported separately. No selection settings were changed in response to these scores.

The four adapters were transferred from local training artifacts into the funded
account's account-scoped `invoiceops-runs` volume. A CPU preflight verified the size
and SHA-256 of all eight config/weight files and the expected candidate list before
GPU allocation. See `reports/modal/grpo-v3d-evaluation-transfer-manifest.json` and
`reports/modal/grpo-v3d-evaluation-transfer-verified.json`.

All 96 dev trajectories are saved locally under
`runs/modal/training/grpo-v3d/selection/<checkpoint>/episodes/`. Each candidate also
has its config, summary, report and download manifest. All episodes replayed exactly:
zero state-hash, observation, final-snapshot or verifier mismatches, and recomputed
summaries equal the saved summaries. Audit files are
`reports/modal/dev-<checkpoint>-audit.json`.

Selection decision: `runs/modal/training/grpo-v3d/selection.json`, also included in the
completed `select_and_test` launcher result. The selected adapter is merged into
`/runs/train/grpo-v3d/selected_merged` for the trained InvoiceOps and tau2 evaluations.

The earlier BFCL evaluation used **final step 150**. Its result must remain labelled
as such and must not be attributed to the dev-selected step-125 checkpoint.
The owner subsequently requested the selected checkpoint's BFCL evaluation too; that
run is now complete on the first account. See `reports/bfcl_selected.md` for the
matching step-125 comparison used in the final evaluation suite.
