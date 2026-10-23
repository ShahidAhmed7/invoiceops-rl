# R1 Scenario Spec Review

- **Task ID:** T-6BAF87
- **Spec revision reviewed:** `089ec602b9ff`
- **Reviewer initials:** Shahid Ahmed
- **Role:** Independent solver (fictional policy simulator)
- **Date:** 2026-10-23
- **Did you blind-solve this task (R2) before reading the spec?** Yes (run ID: play-T-6BAF87-2026-10-22T224533Z, graded PASS)
- **Time spent:** ~15 min

## Checklist

| # | Question | Answer |
|---|---|---|
| 1 | The prompt states the objective clearly enough to start work. | Yes. |
| 2 | Every fact needed for the expected outcome is available through the agent's tools or documents. | Yes — invoice, PO-2946, receipts GRN-837/GRN-838, prior invoice INV-41543 + payment PAY-52238 all readable. |
| 3 | The company policy that decides the outcome is written down and accessible to the agent. | Yes — DOC-304 (tolerance 1% cap $150; rule `pay_received_portion`). |
| 4 | Money and quantity arithmetic in the spec is correct (check it yourself). | Yes — invoice 16×$142.70 = $2,283.20 = 228,320 minor; PO 40 units; receipts 24+16=40; prior billing INV-41543 covered 24 (paid $3,424.80 = 24×$142.70); remaining 40−24=16 exactly matches this invoice. |
| 5 | The expected outcome is the only reasonable one under the stated policy, **or** every acceptable alternative is listed. | Yes — the invoice fits the remaining PO capacity exactly; pay in full. (Had it exceeded 16 units, the payable portion would differ.) |
| 6 | Each listed failing example really should fail. | Yes — paying more than the remaining 16 units, or rejecting, would both be wrong. |
| 7 | No requirement is hidden: nothing is checked that the agent could not know was needed. | Yes — prior billing is discoverable via invoice/payment records on the same PO. |
| 8 | Difficulty comes from the business problem, not from unclear wording, confusing IDs, or padding. | Yes — PO-capacity accounting across two receipts and a prior invoice is the intended work. |
| 9 | The records are consistent with each other (dates, vendors, PO and receipt links, totals). | Yes — receipts 2026-03-13/28, prior invoice 2026-03-15 paid 2026-03-27, this invoice 2026-03-30/04-01, as_of 2026-04-27. |
| 10 | *(Domain reviewer)* A real AP team would recognise this situation and handle it this way. | N/A — independent solver. |

## Alternative outcomes

None — the arithmetic pins a single payable amount.

## Failing examples to add

None.

## Notes

A well-constructed partial-billing case: the agent must combine receipts with payment history, not just match against the PO total.

## Decision

- [x] **Approve:** ready to implement or publish.
- [ ] **Approve with changes**
- [ ] **Reject**
