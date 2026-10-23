# R1 Scenario Spec Review

- **Task ID:** T-5B8D32
- **Spec revision reviewed:** `eb8a19a358b1`
- **Reviewer initials:** Shahid Ahmed
- **Role:** Independent solver (fictional policy simulator)
- **Date:** 2026-10-23
- **Did you blind-solve this task (R2) before reading the spec?** Yes (run ID: play-T-5B8D32-2026-10-22T224607Z, graded PASS)
- **Time spent:** ~25 min (incl. interactive probes manual-adv-06/-07)

## Checklist

| # | Question | Answer |
|---|---|---|
| 1 | The prompt states the objective clearly enough to start work. | Yes. |
| 2 | Every fact needed for the expected outcome is available through the agent's tools or documents. | Yes — invoice, PO-6096, GRN-279, open credit CN-875 for this invoice, policy DOC-828, and the retryable-fault hint ("Retry with the same idempotency key") in the tool error itself. |
| 3 | The company policy that decides the outcome is written down and accessible to the agent. | Yes — apply the open credit to its own invoice; retry a lost response with the same key. |
| 4 | Money and quantity arithmetic in the spec is correct (check it yourself). | Yes — 12×$214.00 = $2,568.00; minus CN-875 $256.00 → $2,312.00 = 231,200 minor, credits [CN-875]. |
| 5 | The expected outcome is the only reasonable one under the stated policy, **or** every acceptable alternative is listed. | Yes — `matched_with_credit` paying $2,312.00 with CN-875 attached is the unique correct result; the same-key retry is the unique correct retry behaviour. |
| 6 | Each listed failing example really should fail. | Mostly — a different-key retry leaving two active proposals fails (manual-adv-06 FAIL), but changing the key and then withdrawing the first proposal escapes (attack-10 → PASS). See attack-log B1. |
| 7 | No requirement is hidden: nothing is checked that the agent could not know was needed. | Yes — the tool error message itself instructs same-key retry. |
| 8 | Difficulty comes from the business problem, not from unclear wording, confusing IDs, or padding. | Yes — fault injection + credit application is the designed difficulty. |
| 9 | The records are consistent with each other (dates, vendors, PO and receipt links, totals). | Yes — CN-875 open, issued 2026-01-16 for INV-60418; receipt 2026-01-11; invoice 2026-01-13/15. |
| 10 | *(Domain reviewer)* A real AP team would recognise this situation and handle it this way. | N/A — independent solver. |

## Alternative outcomes

None.

## Failing examples to add

- Changed-key retry + withdrawal of the first proposal currently passes (attack-10). Covered under B1.

## Notes

Idempotency itself verified live: same-key retry returns `replayed: true` with a single proposal (manual-adv-07 PASS); the retryable fault fires after the insert commits, so the "lost" proposal is real.

## Decision

- [x] **Approve:** spec sound; verifier escape tracked separately.
- [ ] **Approve with changes**
- [ ] **Reject**
