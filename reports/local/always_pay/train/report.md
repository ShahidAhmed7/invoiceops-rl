# Evaluation: always_pay

## Configuration

- **agent:** `always_pay`
- **attempts:** `1`
- **prompt_version:** `n/a`
- **splits:** `['train']`
- **tasks:** `36`

## Results

| Metric | Value |
|---|---|
| Tasks x attempts | 36 x 1 |
| Strict success (all scored attempts) | 33.3% |
| Task-mean success (95% task-bootstrap CI) | 33.3% (19.4% to 50.0%) |
| pass@1 | 33.3% |
| pass^1 | 33.3% |
| Attempts with a critical violation | 23 |
| False completions | 0 |
| Exception cases not paid | 0/14 |
| Clean cases paid correctly | 12/22 |
| Unscorable attempts (infrastructure) | 0 |
| Mean tool calls per attempt | 5.0 |

## Success by family

| Family | Task-mean success |
|---|---|
| F01 | 66.7% |
| F02 | 66.7% |
| F03 | 0.0% |
| F04 | 33.3% |
| F05 | 66.7% |
| F06 | 33.3% |
| F07 | 33.3% |
| F08 | 0.0% |
| F09 | 33.3% |
| F10 | 33.3% |
| F11 | 33.3% |
| F12 | 0.0% |

## Critical violations

| Violation | Attempts |
|---|---|
| overpayment_proposed | 5 |
| payment_proposed_for_unpayable_invoice | 14 |
| payment_without_required_approval | 4 |
