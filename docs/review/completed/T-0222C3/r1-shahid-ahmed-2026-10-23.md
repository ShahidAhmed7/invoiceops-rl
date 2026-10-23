# R1 Scenario Spec Review

- **Task ID:** T-0222C3
- **Spec revision reviewed:** `16b7213f35a5`
- **Reviewer initials:** Shahid Ahmed
- **Role:** Independent solver (fictional policy simulator)
- **Date:** 2026-10-23
- **Did you blind-solve this task (R2) before reading the spec?** Yes (run ID: play-T-0222C3-2026-10-22T224203Z, graded PASS)
- **Time spent:** ~25 min (incl. interactive probes manual-adv-09)

## Checklist

| # | Question | Answer |
|---|---|---|
| 1 | The prompt states the objective clearly enough to start work. | Yes. |
| 2 | Every fact needed for the expected outcome is available through the agent's tools or documents. | Yes — receipts GRN-224/GRN-225 are tool-readable; policy DOC-396 states the short-receipt rule. |
| 3 | The company policy that decides the outcome is written down and accessible to the agent. | Yes — Velloran's rule is `require_corrected_invoice`: hold `short_receipt` and ask the supplier for a corrected invoice. |
| 4 | Money and quantity arithmetic in the spec is correct (check it yourself). | Yes — invoice 20×$129.75 = $2,595.00; PO-2288 = 20 units; received 10 + 5 = 15 < 20 billed → genuine short receipt. |
| 5 | The expected outcome is the only reasonable one under the stated policy, **or** every acceptable alternative is listed. | Yes — under `require_corrected_invoice`, paying the billed amount or paying only 15 units both violate the company rule; hold + supplier clarification is the unique outcome. |
| 6 | Each listed failing example really should fail. | Yes — payment of any amount must fail (and does: attack-03, which left a withdrawn proposal on this task, was rejected). |
| 7 | No requirement is hidden: nothing is checked that the agent could not know was needed. | Yes — recipient (supplier) and citation requirements are derivable from the written policy and the evidence chain. |
| 8 | Difficulty comes from the business problem, not from unclear wording, confusing IDs, or padding. | Yes — summing two partial receipts against billed quantity is the real work. |
| 9 | The records are consistent with each other (dates, vendors, PO and receipt links, totals). | Yes — receipts dated 2026-02-17/21 precede the invoice date 2026-02-23, consistent with a supplier billing against the PO before final delivery. |
| 10 | *(Domain reviewer)* A real AP team would recognise this situation and handle it this way. | N/A — independent solver. |

## Alternative outcomes

None under this company's rule. (Another company in the suite uses `pay_received_portion` — a deliberately different policy; this spec is unambiguous about which rule applies.)

## Failing examples to add

- The required supplier clarification is enforced only on recipient + citations: attack-08 (contradictory message) and manual-adv-09 ("Hello.") both PASS. The spec's intent — "asking for a corrected invoice" — is not enforced.

## Notes

This task hosted two confirmed escapes (attack-08, manual-adv-09) under B2 in the attack log. The spec itself is correct and solvable; the defect is in grader enforcement.

## Decision

- [x] **Approve:** spec is sound; verifier enforcement gap tracked separately.
- [ ] **Approve with changes**
- [ ] **Reject**
