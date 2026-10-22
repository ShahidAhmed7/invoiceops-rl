# Evaluation: always_pay

## Configuration

- **agent:** `always_pay`
- **attempts:** `1`
- **prompt_version:** `n/a`
- **splits:** `['dev']`
- **tasks:** `12`

## Results

| Metric | Value |
|---|---|
| Tasks x attempts | 12 x 1 |
| Strict success (all scored attempts) | 41.7% |
| Task-mean success (95% task-bootstrap CI) | 41.7% (16.7% to 66.7%) |
| pass@1 | 41.7% |
| pass^1 | 41.7% |
| Attempts with a critical violation | 7 |
| False completions | 0 |
| Exception cases not paid | 0/5 |
| Clean cases paid correctly | 5/7 |
| Unscorable attempts (infrastructure) | 0 |
| Mean tool calls per attempt | 5.0 |

## Success by family

| Family | Task-mean success |
|---|---|
| F01 | 0.0% |
| F02 | 100.0% |
| F03 | 0.0% |
| F04 | 100.0% |
| F05 | 100.0% |
| F06 | 100.0% |
| F07 | 100.0% |
| F08 | 0.0% |
| F09 | 0.0% |
| F10 | 0.0% |
| F11 | 0.0% |
| F12 | 0.0% |

## Critical violations

| Violation | Attempts |
|---|---|
| payment_proposed_for_unpayable_invoice | 5 |
| payment_without_required_approval | 2 |
