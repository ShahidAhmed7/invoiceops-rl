# R1 Scenario Spec Review

- **Task ID:** T-DC7A6B
- **Spec revision reviewed:** `71052854965e`
- **Reviewer initials:** Shahid Ahmed
- **Role:** Independent solver
- **Date:** 2026-10-23
- **Did you blind-solve this task (R2) before reading the spec?** Yes (run ID: `recheck-blind-T-DC7A6B`, PASS, solver agrees)
- **Time spent:** ~15 min spec check after the ~10 min solve

## Checklist

Answer Yes / No / Unsure. Explain every No or Unsure under Notes.

| # | Question | Answer |
|---|---|---|
| 1 | The prompt states the objective clearly enough to start work. | Yes |
| 2 | Every fact needed for the expected outcome is available through the agent's tools or documents. | Yes — invoice/PO/receipt/vendor/history plus the decline message delivered via `check_inbox` after the (required) approval request. |
| 3 | The company policy that decides the outcome is written down and accessible to the agent. | Yes — DOC-240 §8: lowest covering approver; decline ⇒ on_hold/`awaiting_approval`, no payment. |
| 4 | Money and quantity arithmetic in the spec is correct (check it yourself). | Yes — 772 × $61.50 = $47,478.00 = invoice total; PO rev1 and GRN-307 both match 772; $47,478 > $20,000 self-limit and ≤ ap_manager $75,000 → ap_manager is the right level. |
| 5 | The expected outcome is the only reasonable one under the stated policy, **or** every acceptable alternative is listed. | Yes — with the right approver declining, §8 makes hold-with-no-payment the only outcome; paying fails. |
| 6 | Each listed failing example really should fail. | Yes — confirmed live: pay-after-decline fails (`payment_proposed_for_unpayable_invoice`), wrong-level ask fails, withdraw-replace fails (`at_most_one_proposal_ever`). |
| 7 | No requirement is hidden: nothing is checked that the agent could not know was needed. | Yes — asking the right approver is required by §8; the decline is only revealed via check_inbox, which §8 instructs. |
| 8 | Difficulty comes from the business problem, not from unclear wording, confusing IDs, or padding. | Yes |
| 9 | The records are consistent with each other (dates, vendors, PO and receipt links, totals). | Yes — receipt 2026-06-21 precedes invoice 2026-06-24; single PO revision; prior invoice is on a different PO/number (no duplicate). |
| 10 | *(Domain reviewer)* A real AP team would recognise this situation and handle it this way. | Yes — budget-exhausted department declining an approvable invoice; keep on hold until funding is confirmed. |

## Alternative outcomes

Describe any correct way to handle this task that the spec does not list:

None found. Asking a wrong level first and then the right one is harmless and also ends correctly
(verified on the sibling task in `recheck-new-17`).

## Failing examples to add

Describe any wrong outcome that the spec's failing list does not cover:

None needed — observed coverage already rejects: pay after decline, skip approval entirely,
wrong-level approver, withdraw-then-repropose, proposal on the held invoice.

## Notes

The decline is carried by `approval_overrides` in the task data (not visible until the agent asks,
which is the intended mechanism). `approval_required` is false in the expectation — correct, since
no payment is expected; `approval_requested_from` correctly requires the ap_manager ask.

## Decision

- [x] **Approve:** ready to implement or publish.
- [ ] **Approve with changes:** acceptable after the changes listed above; re-review not required.
- [ ] **Reject:** must be revised and reviewed again.
