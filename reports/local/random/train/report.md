# Evaluation: random

## Configuration

- **agent:** `random`
- **attempts:** `1`
- **prompt_version:** `n/a`
- **splits:** `['train']`
- **tasks:** `36`

## Results

| Metric | Value |
|---|---|
| Tasks x attempts | 36 x 1 |
| Strict success (all scored attempts) | 0.0% |
| Task-mean success (95% task-bootstrap CI) | 0.0% (0.0% to 0.0%) |
| pass@1 | 0.0% |
| pass^1 | 0.0% |
| Attempts with a critical violation | 34 |
| False completions | 36 |
| Exception cases not paid | 0/15 |
| Clean cases paid correctly | 0/21 |
| Unscorable attempts (infrastructure) | 0 |
| Mean tool calls per attempt | 18.0 |

## Success by family

| Family | Task-mean success |
|---|---|
| F01 | 0.0% |
| F02 | 0.0% |
| F03 | 0.0% |
| F04 | 0.0% |
| F05 | 0.0% |
| F06 | 0.0% |
| F07 | 0.0% |
| F08 | 0.0% |
| F09 | 0.0% |
| F10 | 0.0% |
| F11 | 0.0% |
| F12 | 0.0% |

## Critical violations

| Violation | Attempts |
|---|---|
| duplicate_payment_proposal | 31 |
| overpayment_proposed | 5 |
| payment_before_receipt | 2 |
| payment_proposed_for_unpayable_invoice | 15 |
| payment_without_required_approval | 4 |
