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
| Strict success (all scored attempts) | 33.3% |
| Task-mean success (95% task-bootstrap CI) | 33.3% (8.3% to 58.3%) |
| pass@1 | 33.3% |
| pass^1 | 33.3% |
| Attempts with a critical violation | 8 |
| False completions | 0 |
| Exception cases not paid | 0/6 |
| Clean cases paid correctly | 4/6 |
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
| F06 | 0.0% |
| F07 | 100.0% |
| F08 | 0.0% |
| F09 | 0.0% |
| F10 | 0.0% |
| F11 | 0.0% |
| F12 | 0.0% |

## Critical violations

| Violation | Attempts |
|---|---|
| payment_proposed_for_unpayable_invoice | 6 |
| payment_without_required_approval | 2 |
