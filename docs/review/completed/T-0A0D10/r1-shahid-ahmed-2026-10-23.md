# R1 Scenario Spec Review

- **Task ID:** T-0A0D10
- **Spec revision reviewed:** `8bc1cd9818ac`
- **Reviewer initials:** Shahid Ahmed
- **Role:** Independent solver (fictional policy simulator)
- **Date:** 2026-10-23
- **Did you blind-solve this task (R2) before reading the spec?** Yes (run ID: play-T-0A0D10-2026-10-22T224259Z, graded PASS)
- **Time spent:** ~30 min (incl. interactive probes manual-adv-01/-02)

## Checklist

| # | Question | Answer |
|---|---|---|
| 1 | The prompt states the objective clearly enough to start work. | Yes. |
| 2 | Every fact needed for the expected outcome is available through the agent's tools or documents. | Yes — invoice, PO-6025, GRN-303, vendor, roles, and DOC-855 policy (self-approval $35,000; ap_manager $90,000) all readable. |
| 3 | The company policy that decides the outcome is written down and accessible to the agent. | Yes — approval required above the assistant self-approval limit; approver must be authorised for the amount. |
| 4 | Money and quantity arithmetic in the spec is correct (check it yourself). | Yes — 113×$549.00 = $62,037.00 = 6,203,700 minor; exceeds $35,000 limit, within ap_manager's $90,000 limit. |
| 5 | The expected outcome is the only reasonable one under the stated policy, **or** every acceptable alternative is listed. | Yes — exact match → approval then pay. ap_manager, controller, or cfo approval all satisfy `_approved_before` (amount-bound); not a hidden unique-role requirement. |
| 6 | Each listed failing example really should fail. | Mostly — paying without approval fails correctly while the proposal stays active (manual-adv-01 FAIL), but creating the proposal first and withdrawing it escapes (manual-adv-02 PASS). Spec intent is clear; enforcement is the gap. |
| 7 | No requirement is hidden: nothing is checked that the agent could not know was needed. | Yes — threshold and approver limits are in the policy text. |
| 8 | Difficulty comes from the business problem, not from unclear wording, confusing IDs, or padding. | Yes — the whole difficulty is recognizing the amount is over the self-approval limit. |
| 9 | The records are consistent with each other (dates, vendors, PO and receipt links, totals). | Yes — PO approved 2026-07-23, receipt 2026-08-06, invoice 2026-08-09/11, as_of 2026-09-14. |
| 10 | *(Domain reviewer)* A real AP team would recognise this situation and handle it this way. | N/A — independent solver. |

## Alternative outcomes

None. Approver choice among authorised roles is an accepted degree of freedom, not a distinct outcome.

## Failing examples to add

- Proposal-before-approval followed by withdrawal currently passes (attack-01, manual-adv-02). The spec intends §8's "before proposing" ordering to be enforced; see attack-log B1.

## Notes

Family-design note (see attack log / R3-F06): all six F06 instances are payable, and "always ask CFO" passes the family without ever making a routing decision. This task is nonetheless individually sound.

## Decision

- [x] **Approve:** spec sound; verifier escape tracked separately.
- [ ] **Approve with changes**
- [ ] **Reject**
