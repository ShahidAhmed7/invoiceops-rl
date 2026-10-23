# R1 Scenario Spec Review

- **Task ID:** T-1A3136
- **Spec revision reviewed:** `90627c206c5e`
- **Reviewer initials:** Shahid Ahmed
- **Role:** Independent solver (fictional policy simulator)
- **Date:** 2026-10-23
- **Did you blind-solve this task (R2) before reading the spec?** Yes (run ID: play-T-1A3136-2026-10-22T224230Z, graded PASS)
- **Time spent:** ~25 min (incl. interactive probes manual-adv-03/-04)

## Checklist

| # | Question | Answer |
|---|---|---|
| 1 | The prompt states the objective clearly enough to start work. | Yes. |
| 2 | Every fact needed for the expected outcome is available through the agent's tools or documents. | Yes — invoice, PO-7254, GRN-670, credit note CN-453 (with `applied_to: PAY-78604`), prior invoice/payment all readable. |
| 3 | The company policy that decides the outcome is written down and accessible to the agent. | Yes — DOC-152: credits apply once and only to the referenced invoice. |
| 4 | Money and quantity arithmetic in the spec is correct (check it yourself). | Yes — 94×$38.60 = $3,628.40 = 362,840 minor; CN-453 ($362.00) belongs to INV-44079 and was already applied to PAY-78604 ($3,628.40 − $362.00 = $3,266.40 paid). |
| 5 | The expected outcome is the only reasonable one under the stated policy, **or** every acceptable alternative is listed. | Yes — pay the gross $3,628.40 with no credits; CN-453 is spent and references a different invoice, so no credit may be deducted. |
| 6 | Each listed failing example really should fail. | Yes — deducting CN-453 (→ $3,266.40) underpays this invoice; confirmed live in manual-adv-03 (FAIL while the wrong proposal stayed active). |
| 7 | No requirement is hidden: nothing is checked that the agent could not know was needed. | Yes — the credit's `applied_to` field is agent-visible, making the trap discoverable rather than hidden. |
| 8 | Difficulty comes from the business problem, not from unclear wording, confusing IDs, or padding. | Yes — the distractor is real: same vendor, same amount item (PO-7251) already billed via INV-44079; the agent must attribute the credit correctly. |
| 9 | The records are consistent with each other (dates, vendors, PO and receipt links, totals). | Yes — CN-453 issued 2025-12-18, applied to PAY-78604 on 2025-12-23; INV-44083 against PO-7254 received in full 2026-01-08. |
| 10 | *(Domain reviewer)* A real AP team would recognise this situation and handle it this way. | N/A — independent solver. |

## Alternative outcomes

None — reusing an applied credit is not a defensible alternative under "apply once, to the referenced invoice".

## Failing examples to add

- Proposing with CN-453 and then withdrawing before submission currently escapes (attack-11, manual-adv-04 → PASS). The spec intends this to fail; see attack-log B1.

## Notes

This is the strongest trap task reviewed: the credit record is honest and visible, so the failure mode is purely the agent's reasoning. The verifier escape is separate from spec quality.

## Decision

- [x] **Approve:** spec sound; verifier escape tracked separately.
- [ ] **Approve with changes**
- [ ] **Reject**
