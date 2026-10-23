# R1 Scenario Spec Review

- **Task ID:** T-739D69
- **Spec revision reviewed:** `b3eff90a0c2c`
- **Reviewer initials:** Shahid Ahmed
- **Role:** Independent solver (fictional policy simulator)
- **Date:** 2026-10-23
- **Did you blind-solve this task (R2) before reading the spec?** Yes (run ID: play-T-739D69-2026-10-22T224445Z, graded PASS)
- **Time spent:** ~15 min

## Checklist

| # | Question | Answer |
|---|---|---|
| 1 | The prompt states the objective clearly enough to start work. | Yes — investigate INV-36943 at Juniper Fold. |
| 2 | Every fact needed for the expected outcome is available through the agent's tools or documents. | Yes — invoice, PO-1860, GRN-740, prior invoice INV-36936 and its payment PAY-84360 all tool-readable. |
| 3 | The company policy that decides the outcome is written down and accessible to the agent. | Yes — DOC-762's duplicate check precedes matching in the stated work order. |
| 4 | Money and quantity arithmetic in the spec is correct (check it yourself). | Yes — 23×$236.50 = $5,439.50; identical total/date/vendor/PO as already-paid INV-36936 (paid 2026-06-21). |
| 5 | The expected outcome is the only reasonable one under the stated policy, **or** every acceptable alternative is listed. | Yes — same vendor, same PO, same amount, same invoice date, different vendor invoice number → `rejected/duplicate_invoice`, citing the original INV-36936. Paying would double-pay PO-1860's 23 units. |
| 6 | Each listed failing example really should fail. | Yes — paying this invoice is the core duplicate-billing failure the check exists to prevent. |
| 7 | No requirement is hidden: nothing is checked that the agent could not know was needed. | Yes — the prior invoice is discoverable via the invoice/payment records; the evidence cite points to it. |
| 8 | Difficulty comes from the business problem, not from unclear wording, confusing IDs, or padding. | Yes — the trap is that the invoice otherwise matches perfectly; only history reveals the duplicate. |
| 9 | The records are consistent with each other (dates, vendors, PO and receipt links, totals). | Yes — both invoices dated 2026-06-07 against PO-1860 (23 units, one receipt GRN-740); a second billing of the same goods is exactly the duplicate pattern. |
| 10 | *(Domain reviewer)* A real AP team would recognise this situation and handle it this way. | N/A — independent solver. |

## Alternative outcomes

None. Holding instead of rejecting is not listed and is not equivalent — the policy's verb is "reject".

## Failing examples to add

None beyond those covered.

## Notes

The evidence requirement `[[INV-36936]]` correctly forces the agent to name the prior paid invoice rather than merely label the case a duplicate.

## Decision

- [x] **Approve:** ready to implement or publish.
- [ ] **Approve with changes**
- [ ] **Reject**
