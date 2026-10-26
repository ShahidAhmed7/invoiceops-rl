# Completed post-training evaluation

Completed 2026-10-26. **Checkpoint 125** was selected on dev and then used consistently
for the trained InvoiceOps test, BFCL and tau2. It was the unique dev winner: 24/24,
versus 23/24 at step 150, 22/24 at step 100 and 21/24 at step 75. Benchmark test scores
were not used to choose or change the checkpoint.

| Metric | Untrained | Selected step 125 | Change |
|---|---:|---:|---:|
| InvoiceOps strict success | 76/96 (79.167%) | **84/96 (87.500%)** | **+8.333 pp** |
| InvoiceOps pass^4 | 14/24 (58.333%) | **18/24 (75.000%)** | +16.667 pp |
| InvoiceOps pass@4 | 23/24 (95.833%) | 23/24 (95.833%) | unchanged |
| tau2 mean reward | 59/160 (36.875%) | 62/160 (38.750%) | +1.875 pp |
| tau2 pass^4 | 8/40 (20.000%) | 9/40 (22.500%) | +2.500 pp |
| BFCL multi-turn base | 54/200 (27.000%) | 51/200 (25.500%) | −1.500 pp |

The InvoiceOps comparison uses the fresh current-code untrained control. Its point estimate
and repeat reliability improved, but the paired task-bootstrap interval for the success
difference spans 0 to +17.708 percentage points. Critical-violation attempts increased
from three to four while false completions fell from three to zero. Test has only four
companies and has already been inspected during prompt work, so the gain is exploratory.

External transfer is limited: tau2's small increase has a paired task-bootstrap interval
of −6.25 to +10.00 points. On BFCL, five categories declined slightly, two improved and
one stayed unchanged; changes range from −1.50 to +0.39 points. There is no established
general benchmark improvement. BFCL covers all 2,751 cases in the eight planned baseline
categories, not every category of the entire benchmark; its printed Overall is unsuitable
for this subset. Tau2 uses a local customer model and ENV-only grading, not leaderboard
grading.

| BFCL category | Untrained | Selected step 125 | Change (pp) |
|---|---:|---:|---:|
| Simple Python | 95.25% | 95.00% | −0.25 |
| Multiple | 94.50% | 93.50% | −1.00 |
| Parallel | 93.00% | 92.50% | −0.50 |
| Parallel multiple | 90.00% | 89.50% | −0.50 |
| Irrelevance | 88.75% | 88.75% | 0.00 |
| Live simple | 78.29% | 78.68% | +0.39 |
| Live multiple | 76.83% | 77.21% | +0.38 |
| Multi-turn base | 27.00% | 25.50% | −1.50 |

## Detailed results and evidence

- [Dev selection](checkpoint_selection.md): four candidates, 96 raw episodes, exact replay.
- [InvoiceOps test](trained_invoiceops.md): 96 raw episodes, exact replay and matched control fingerprints.
- [Selected-checkpoint BFCL](bfcl_selected.md): all eight categories, 2,751 unique case results.
- [tau2](tau2_after.md): 160 unique task/trial pairs, complete rewards and arithmetic checks.
- [Fresh untrained control](fresh_untrained_control.md): 96 raw episodes, exact replay.

All raw trajectories, configs, verdicts and logs are local under `runs/modal/` and
`runs/local-logs/`; those folders are gitignored. Detailed reports identify the exact paths
and remote volume backups. Model provenance identifies the same selected adapter SHA-256
on both accounts: `451f24b51081dbe1e2779a07f30bbb2fee884291a4e948b1951f9a454aaa18f7`.

The earlier [step-150 BFCL diagnostic](bfcl_after.md) remains frozen and separately
labelled. The selected-checkpoint BFCL result above is the final suite's comparison.

## Accounts and cost

| Job | Account profile | Ledger estimate |
|---|---|---:|
| Dev selection + merge + InvoiceOps test | `kazigalib143` | $0.7879 |
| tau2 | `kazigalib143` | $1.3429 |
| Selected-checkpoint BFCL + merge | `invoiceops-thinking` | $0.4420 |
| **This batch** | | **$2.5728** |

The funded account's two jobs total $2.1308 against its $10 allocation. BFCL used the first
account, $0.4420 against its separate $2.50 allocation. Earlier fresh-control and step-150
BFCL costs are separate. These are conservative launcher wall-clock estimates, not
dashboard-reconciled invoices. Both accounts showed no running containers after completion.

The matching selected-checkpoint results and their raw evidence are the basis for the
repository's result figures and statistical analysis.
