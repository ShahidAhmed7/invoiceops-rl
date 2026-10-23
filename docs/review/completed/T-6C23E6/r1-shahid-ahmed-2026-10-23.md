# R1 Scenario Spec Review

- **Task ID:** T-6C23E6
- **Spec revision reviewed:** `7b855b65ebd5`
- **Reviewer initials:** Shahid Ahmed
- **Role:** Independent solver (fictional policy simulator)
- **Date:** 2026-10-23
- **Did you blind-solve this task (R2) before reading the spec?** Yes (run ID: play-T-6C23E6-2026-10-22T224333Z, graded PASS)
- **Time spent:** ~30 min (incl. interactive probes manual-adv-05/-08)

## Checklist

| # | Question | Answer |
|---|---|---|
| 1 | The prompt states the objective clearly enough to start work. | Yes. |
| 2 | Every fact needed for the expected outcome is available through the agent's tools or documents. | Yes — invoice, PO-1348 (no receipts initially), policy's missing-receipt clause, and the scripted reply event releasing GRN-176 after a receiving clarification. |
| 3 | The company policy that decides the outcome is written down and accessible to the agent. | Yes — DOC-138: missing receipt → clarify receiving; once the receipt posts, matched invoices proceed to payment. |
| 4 | Money and quantity arithmetic in the spec is correct (check it yourself). | Yes — 18×$273.40 = $4,921.20 = 492,120 minor; released GRN-176 covers all 18 units. |
| 5 | The expected outcome is the only reasonable one under the stated policy, **or** every acceptable alternative is listed. | Yes — clarify receiving, then pay in full once GRN-176 posts. Paying without the clarification fails correctly (attack-12; manual-adv-08). |
| 6 | Each listed failing example really should fail. | Mostly — skipping the clarification fails, but a content-free clarification currently passes and still triggers the event (manual-adv-05 → PASS). Spec intent is that the message must ask for the receipt. |
| 7 | No requirement is hidden: nothing is checked that the agent could not know was needed. | Yes — the recipient role and citation requirements follow from the written clause. |
| 8 | Difficulty comes from the business problem, not from unclear wording, confusing IDs, or padding. | Yes — discovering the absence of a receipt and obtaining it via the inbox workflow is the intended difficulty. |
| 9 | The records are consistent with each other (dates, vendors, PO and receipt links, totals). | Yes — invoice 2026-08-13/15 vs as_of 2026-09-14 leaves a plausible late-booked receipt; released GRN-176 dated 2026-09-13. |
| 10 | *(Domain reviewer)* A real AP team would recognise this situation and handle it this way. | N/A — independent solver. |

## Alternative outcomes

Holding for the missing receipt without asking is not equivalent — the policy routes through the clarification, and only that path releases the receipt.

## Failing examples to add

- Vacuous or contradictory clarification text satisfies `required_clarification` and releases the event (manual-adv-05). See attack-log B2.

## Notes

The event mechanism itself is well-formed (recipient-gated, releases the correct receipt); the gap is that neither the event trigger nor the verifier examines message semantics.

## Decision

- [x] **Approve:** spec sound; trigger/verifier gap tracked separately.
- [ ] **Approve with changes**
- [ ] **Reject**
