# Evaluation: always_pay

## Configuration

- **agent:** `always_pay`
- **attempts:** `1`
- **prompt_version:** `n/a`
- **splits:** `['test']`
- **tasks:** `24`

## Results

| Metric | Value |
|---|---|
| Tasks x attempts | 24 x 1 |
| Strict success (all scored attempts) | 29.2% |
| Task-mean success (95% task-bootstrap CI) | 29.2% (12.5% to 45.8%) |
| pass@1 | 29.2% |
| pass^1 | 29.2% |
| Attempts with a critical violation | 17 |
| False completions | 0 |
| Exception cases not paid | 0/9 |
| Clean cases paid correctly | 7/15 |
| Unscorable attempts (infrastructure) | 0 |
| Mean tool calls per attempt | 5.0 |

## Success by family

| Family | Task-mean success |
|---|---|
| F01 | 100.0% |
| F02 | 50.0% |
| F03 | 0.0% |
| F04 | 0.0% |
| F05 | 50.0% |
| F06 | 0.0% |
| F07 | 0.0% |
| F08 | 0.0% |
| F09 | 50.0% |
| F10 | 50.0% |
| F11 | 50.0% |
| F12 | 0.0% |

## Critical violations

| Violation | Attempts |
|---|---|
| overpayment_proposed | 5 |
| payment_before_receipt | 2 |
| payment_proposed_for_unpayable_invoice | 9 |
| payment_without_required_approval | 2 |
