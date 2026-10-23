# R1 Scenario Spec Review

- **Task ID:** T-0A0D10
- **Spec revision reviewed:** `a2e1856e7f2e` (new revision after the policy change; prior review covered `8bc1cd9818ac`)
- **Reviewer initials:** Shahid Ahmed
- **Role:** Independent solver
- **Date:** 2026-10-23
- **Did you blind-solve this task (R2) before reading the spec?** Yes — first review (`play-T-0A0D10-2026-10-22T224259Z`, PASS) plus ~10 grading runs on it during this re-check
- **Time spent:** ~15 min

## Checklist

Answer Yes / No / Unsure. Explain every No or Unsure under Notes.

| # | Question | Answer |
|---|---|---|
| 1 | The prompt states the objective clearly enough to start work. | Yes |
| 2 | Every fact needed for the expected outcome is available through the agent's tools or documents. | Yes |
| 3 | The company policy that decides the outcome is written down and accessible to the agent. | Yes — §8 now states the lowest-covering-approver rule and that other levels decline. |
| 4 | Money and quantity arithmetic in the spec is correct (check it yourself). | Yes — 113 × $549.00 = $62,037.00 = total; PO rev1 matches; receipts 10+50+11+113=184 ≥ 113; $62,037 > self-limit, ≤ ap_manager $90,000 → ap_manager is the right level. |
| 5 | The expected outcome is the only reasonable one under the stated policy, **or** every acceptable alternative is listed. | Yes — pay $62,037 with `matched` after ap_manager approval is the only listed and only reasonable outcome. |
| 6 | Each listed failing example really should fail. | Yes — verified live this session: propose-before-approval, wrong-level approver, non-approver, under-approved amount, pending approval, withdraw-only, withdraw-and-replace all FAIL. |
| 7 | No requirement is hidden: nothing is checked that the agent could not know was needed. | Yes |
| 8 | Difficulty comes from the business problem, not from unclear wording, confusing IDs, or padding. | Yes |
| 9 | The records are consistent with each other (dates, vendors, PO and receipt links, totals). | Yes |
| 10 | *(Domain reviewer)* A real AP team would recognise this situation and handle it this way. | Yes |

## Alternative outcomes

Describe any correct way to handle this task that the spec does not list:

None. Over-approval (asking for more than the proposal amount) still passes as in the first
review — approval must cover, not equal — verified in `recheck-new-18`.

## Failing examples to add

Describe any wrong outcome that the spec's failing list does not cover:

None needed — the new checks cover the previously-passing shapes (`at_most_one_proposal_ever`,
history-aware `approval_before_payment`).

## Notes

The approval rule change is what this re-review targets: `approval_required: true` with
`approval_requested_from: []` correctly accepts any sufficient approval at the right level;
wrong-level asks decline with a routing message (verified `recheck-new-01/02`).

## Decision

- [x] **Approve:** ready to implement or publish.
- [ ] **Approve with changes:** acceptable after the changes listed above; re-review not required.
- [ ] **Reject:** must be revised and reviewed again.
