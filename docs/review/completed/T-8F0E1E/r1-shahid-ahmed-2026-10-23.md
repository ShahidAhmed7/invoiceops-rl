# R1 Scenario Spec Review

- **Task ID:** T-8F0E1E
- **Spec revision reviewed:** `3eb1d38939da`
- **Reviewer initials:** Shahid Ahmed
- **Role:** Independent solver (fictional policy simulator)
- **Date:** 2026-10-23
- **Did you blind-solve this task (R2) before reading the spec?** Yes (run ID: play-T-8F0E1E-2026-10-22T224107Z, graded PASS)
- **Time spent:** ~25 min (digest review + arithmetic recheck + interactive probe manual-adv-10)

## Checklist

| # | Question | Answer |
|---|---|---|
| 1 | The prompt states the objective clearly enough to start work. | Yes — investigate INV-18967, apply policy, submit. |
| 2 | Every fact needed for the expected outcome is available through the agent's tools or documents. | Yes — invoice, PO-6504, GRN-484, vendor master, and effective policy DOC-400 are all tool-readable. |
| 3 | The company policy that decides the outcome is written down and accessible to the agent. | Yes — DOC-400 (effective 2025-02-23): match PO + receipts, self-approval limit $12,000. |
| 4 | Money and quantity arithmetic in the spec is correct (check it yourself). | Yes — 461×$22.40 = $10,326.40; 120×$85.90 = $10,308.00; 302×$34.20 = $10,328.40; total $30,962.80 = 3,096,280 minor. PO-6504 lines and GRN-484 quantities match exactly. |
| 5 | The expected outcome is the only reasonable one under the stated policy, **or** every acceptable alternative is listed. | Yes — exact match, verified vendor, remit matches; amount $30,962.80 > $12,000 self-limit → approval mandatory; then pay in full. Any authorised approver (ap_manager $50k / controller $200k / cfo $1.5M) is acceptable — the check binds amount, not a single role, which is reasonable. |
| 6 | Each listed failing example really should fail. | Yes — failing variants (pay without approval, wrong amount, hold) all genuinely violate policy. Confirmed live: manual-adv-10 failed for proposing without approval on this task. |
| 7 | No requirement is hidden: nothing is checked that the agent could not know was needed. | Yes — approval requirement is derivable from the written limit and the invoice total. |
| 8 | Difficulty comes from the business problem, not from unclear wording, confusing IDs, or padding. | Yes — difficulty is the approval threshold plus distractor POs (PO-6493 different vendor; PO-6512 same vendor/item but qty 464 ≠ 461). |
| 9 | The records are consistent with each other (dates, vendors, PO and receipt links, totals). | Yes — invoice dated 2026-02-26 after PO approval 2026-02-10; receipt 2026-02-24 precedes as_of 2026-03-30; prior payments internally consistent. |
| 10 | *(Domain reviewer)* A real AP team would recognise this situation and handle it this way. | N/A — independent solver; fictional policy simulator. |

## Alternative outcomes

None found. Approver identity is an accepted degree of freedom, not a distinct outcome.

## Failing examples to add

- A proposal created *before* approval and later withdrawn currently escapes (see attack-log B1) — the spec's intent is that it should fail.

## Notes

The private expectation requires `approval_required=true`; the blind solve and the live probe agree the check is enforced on the active proposal.

## Decision

- [x] **Approve:** ready to implement or publish.
- [ ] **Approve with changes:** acceptable after the changes listed above; re-review not required.
- [ ] **Reject:** must be revised and reviewed again.

(Spec itself is sound; the verifier escape noted above is a grader defect tracked separately, not a spec defect.)
