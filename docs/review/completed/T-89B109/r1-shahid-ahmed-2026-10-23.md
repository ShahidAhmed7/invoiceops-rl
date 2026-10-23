# R1 Scenario Spec Review

- **Task ID:** T-89B109
- **Spec revision reviewed:** `9dac6af8fb2e`
- **Reviewer initials:** Shahid Ahmed
- **Role:** Independent solver (fictional policy simulator)
- **Date:** 2026-10-23
- **Did you blind-solve this task (R2) before reading the spec?** Yes (run ID: play-T-89B109-2026-10-22T224420Z, graded PASS)
- **Time spent:** ~20 min

## Checklist

| # | Question | Answer |
|---|---|---|
| 1 | The prompt states the objective clearly enough to start work. | Yes — investigate INV-66433 at Juniper Fold Logistics. |
| 2 | Every fact needed for the expected outcome is available through the agent's tools or documents. | Yes — invoice, PO-1793, GRN-144, effective policy DOC-465 all readable. |
| 3 | The company policy that decides the outcome is written down and accessible to the agent. | Yes — DOC-465: tolerance 2.5% capped at $500.00; over-tolerance variance → hold `price_variance` and clarify to procurement. |
| 4 | Money and quantity arithmetic in the spec is correct (check it yourself). | Yes — invoice 103×$24.79 = $2,553.37; PO 103×$23.90 = $2,461.70; variance $91.67 > tolerance min(2.5%×$2,461.70=$61.54, $500.00). |
| 5 | The expected outcome is the only reasonable one under the stated policy, **or** every acceptable alternative is listed. | Yes — over-tolerance unit-price variance with full receipt → `on_hold/price_variance`, clarify procurement citing the invoice and PO. Payment is not a defensible alternative (variance is real, not within tolerance). |
| 6 | Each listed failing example really should fail. | Yes — paying the inflated price or holding without the procurement clarification both violate policy. |
| 7 | No requirement is hidden: nothing is checked that the agent could not know was needed. | Yes — the tolerance formula and the escalation role are both in the policy document. |
| 8 | Difficulty comes from the business problem, not from unclear wording, confusing IDs, or padding. | Yes — requires computing PO-line expected amount vs invoiced unit price, and the percent-vs-cap tolerance combination. |
| 9 | The records are consistent with each other (dates, vendors, PO and receipt links, totals). | Yes — PO approved 2026-06-23, receipt 2026-07-01, invoice 2026-07-02, as_of 2026-08-05; vendor VEN-JFA68 verified and remit matches. |
| 10 | *(Domain reviewer)* A real AP team would recognise this situation and handle it this way. | N/A — independent solver. |

## Alternative outcomes

None — a unit-price difference of $0.89/unit (3.7% of line) over the 2.5% tolerance admits no payable reading under the written policy.

## Failing examples to add

None — and note the required clarification is validated only on recipient + citations, not message content (attack-log B2).

## Notes

The cite requirement `(INV-66433)+(PO-1793)` correctly forces the agent to reference the PO that grounds the expected price.

## Decision

- [x] **Approve:** ready to implement or publish.
- [ ] **Approve with changes**
- [ ] **Reject**
