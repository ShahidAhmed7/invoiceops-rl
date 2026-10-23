# R3 Task Family Review

- **Family ID and name:** F09 — Shared PO capacity / prior billing
- **Task IDs reviewed:** T-CC052D (dev), T-6BAF87, T-C07FE6 (test), T-5E46C3, T-A40DCC, T-F3AD7D (train)
- **Reviewer initials:** Shahid Ahmed
- **Role:** Independent solver
- **Date:** 2026-10-23

## Checklist

| # | Question | Answer |
|---|---|---|
| 1 | The family tests one clear skill, described in a sentence. | Yes — compute remaining PO capacity (ordered minus already-billed-and-received) and decide whether this invoice's quantity fits. |
| 2 | The variants differ in ways that change the reasoning, not only in names and numbers. | Yes — v0/v1/v2 differ by whether the invoice fits the remainder (pay / pay-portion) or exceeds it (hold `quantity_exceeds_receipt`/`short_receipt` + clarification). |
| 3 | Some variants should end in payment and others in a hold or follow-up; an agent that always does one thing would fail. | Yes — 3 pay (full or portion) / 3 hold. |
| 4 | The policy wording is consistent across the variants. | Yes. |
| 5 | Boundary cases are covered and the correct handling is stated. | Yes — T-6BAF87 is exactly at the boundary: 40 received, 24 billed, invoice for the remaining 16 → fits. Exceeding-by-1 would flip the outcome; the boundary itself is exercised. |
| 6 | The failing examples include the most likely realistic mistakes. | Yes — paying a quantity beyond the remainder is the realistic error. |
| 7 | No variant relies on a trick. | Yes — prior invoices/payments on the same PO are agent-visible. |
| 8 | Train, dev, test variants come from different fictional companies. | Yes — w01, w03, w05, w07, w09, w11. |
| 9 | *(Domain reviewer)* | N/A. |

## Missing cases

- Prior billing *unpaid* (invoice exists but payment pending — does capacity count billed or paid?).
- A credit note returning capacity to the PO.

## Notes

Sampled T-6BAF87 verified: INV-41551's 16 units = 40 received − 24 previously billed → pay $2,283.20. Arithmetic is unambiguous and requires joining receipts with payment history.

## Decision

- [x] **Approve family**
- [ ] **Approve with changes**
- [ ] **Reject**
