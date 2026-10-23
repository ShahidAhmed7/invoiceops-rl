# R1 Scenario Spec Review

- **Task ID:** T-11EA31
- **Spec revision reviewed:** `9e6201acbb2d`
- **Reviewer initials:** Shahid Ahmed
- **Role:** Independent solver (fictional policy simulator)
- **Date:** 2026-10-23
- **Did you blind-solve this task (R2) before reading the spec?** Yes (run ID: play-T-11EA31-2026-10-22T224632Z, graded PASS)
- **Time spent:** ~15 min

## Checklist

| # | Question | Answer |
|---|---|---|
| 1 | The prompt states the objective clearly enough to start work. | Yes. |
| 2 | Every fact needed for the expected outcome is available through the agent's tools or documents. | Yes — invoice, PO-4395, GRN-407, and BOTH policy versions (stale DOC-672 eff to 2026-07-06; current DOC-679 eff from 2026-07-06) are readable. |
| 3 | The company policy that decides the outcome is written down and accessible to the agent. | Yes — the current policy's short-receipt rule is `require_corrected_invoice`; the superseded document's `pay_received_portion` is a designed distractor, and effective dates are visible in the documents. |
| 4 | Money and quantity arithmetic in the spec is correct (check it yourself). | Yes — invoice 180×$23.90 = $4,302.00; PO-4395 = 180 units; GRN-407 received 135 → short receipt of 45 units. |
| 5 | The expected outcome is the only reasonable one under the stated policy, **or** every acceptable alternative is listed. | Yes — under the CURRENT policy: hold `short_receipt` + supplier clarification citing the invoice and receipt/PO. Paying the received portion is what the STALE policy would have said — a deliberate trap, not a genuine alternative. |
| 6 | Each listed failing example really should fail. | Yes — following the stale policy must fail; that is the point of the family. |
| 7 | No requirement is hidden: nothing is checked that the agent could not know was needed. | Yes — effective dates are printed in each document; the agent can determine which governs the 2026-08-05 business date. |
| 8 | Difficulty comes from the business problem, not from unclear wording, confusing IDs, or padding. | Yes — policy-version discrimination is the intended difficulty. |
| 9 | The records are consistent with each other (dates, vendors, PO and receipt links, totals). | Yes — DOC-672 effective until 2026-07-06, DOC-679 effective from 2026-07-06 (no gap/overlap); receipt 2026-06-26, invoice 2026-06-28/30, as_of 2026-08-05. |
| 10 | *(Domain reviewer)* A real AP team would recognise this situation and handle it this way. | N/A — independent solver. |

## Alternative outcomes

None — the superseded policy's answer is not a legitimate alternative once effective dates are checked.

## Failing examples to add

None — but the clarification-content gap (B2) applies here too.

## Notes

Cleanest version-discrimination case in the suite: both documents are present and dated, so correctness is fully determined by public evidence.

## Decision

- [x] **Approve:** ready to implement or publish.
- [ ] **Approve with changes**
- [ ] **Reject**
