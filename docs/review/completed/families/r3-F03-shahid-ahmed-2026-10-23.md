# R3 Task Family Review

- **Family ID and name:** F03 — Short receipt
- **Task IDs reviewed:** T-0222C3 (dev), T-175EBC, T-202621 (test), T-46FBCC, T-8B3FCC, T-C94302 (train)
- **Reviewer initials:** Shahid Ahmed
- **Role:** Independent solver
- **Date:** 2026-10-23

## Checklist

| # | Question | Answer |
|---|---|---|
| 1 | The family tests one clear skill, described in a sentence. | Yes — detect that billed quantity exceeds received quantity, then apply the company's short-receipt rule (pay received portion vs hold for corrected invoice). |
| 2 | The variants differ in ways that change the reasoning, not only in names and numbers. | Yes — the *same scenario shape* yields opposite outcomes depending on the company's written rule: v0/v1 under `pay_received_portion` companies → `ready_for_payment/partial_receipt_paid`; v2 and others under `require_corrected_invoice` → `on_hold/short_receipt` + supplier clarification. |
| 3 | Some variants should end in payment and others in a hold or follow-up; an agent that always does one thing would fail. | Yes — 2 pay-portion / 4 hold. Always-pay fails the holds (pays goods not received); always-hold fails the portions. |
| 4 | The policy wording is consistent across the variants. | Yes — each company states its own short-receipt rule; the difference is a parameter, not inconsistent wording. |
| 5 | Boundary cases are covered and the correct handling is stated. | Partially — short receipts at various ratios exist; no zero-receipt or multi-line partial boundary observed in the six instances. |
| 6 | The failing examples include the most likely realistic mistakes. | Yes — paying the billed amount is the classic error and fails (plus the attack-03 control demonstrated the hold-path rejects stray proposals). |
| 7 | No variant relies on a trick. | Yes — receipts are visible; the company rule is written. |
| 8 | Train, dev, test variants come from different fictional companies. | Yes — w01, w03, w05, w07, w09, w11. |
| 9 | *(Domain reviewer)* | N/A. |

## Missing cases

- Short receipt where the company rule is `pay_received_portion` AND the invoice also needs approval (compound requirement).
- A receipt posted *after* the invoice date (recency edge).

## Notes

Sampled T-0222C3 verified: 15/20 received under `require_corrected_invoice` → hold + supplier clarification. This family hosts the B2 clarification-content escapes (attack-08, manual-adv-09) — spec design is sound; enforcement is the gap.

## Decision

- [x] **Approve family**
- [ ] **Approve with changes**
- [ ] **Reject**
