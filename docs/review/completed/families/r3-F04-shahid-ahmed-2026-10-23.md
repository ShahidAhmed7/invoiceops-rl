# R3 Task Family Review

- **Family ID and name:** F04 — Duplicate invoice
- **Task IDs reviewed:** T-84D47B (dev), T-739D69, T-BBE12C (test), T-5E2670, T-A42411, T-FBECFF (train)
- **Reviewer initials:** Shahid Ahmed
- **Role:** Independent solver
- **Date:** 2026-10-23

## Checklist

| # | Question | Answer |
|---|---|---|
| 1 | The family tests one clear skill, described in a sentence. | Yes — check payment/invoice history for a prior billing of the same goods before paying; reject true duplicates. |
| 2 | The variants differ in ways that change the reasoning, not only in names and numbers. | Yes — v0/v1 are true duplicates (same vendor/PO/total/date, different invoice number, prior invoice already paid) → `rejected/duplicate_invoice`; v2 instances (T-84D47B, T-A42411) are *apparent* duplicates that turn out clean (e.g., different PO line or quantity justifying a second billing) → pay. |
| 3 | Some variants should end in payment and others in a hold or follow-up; an agent that always does one thing would fail. | Yes — 4 reject / 2 pay. Always-reject fails the two clean cases; always-pay fails the four duplicates. |
| 4 | The policy wording is consistent across the variants. | Yes — duplicate check is in the standard work order before matching. |
| 5 | Boundary cases are covered and the correct handling is stated. | Yes — the v2 false-duplicates are exactly the boundary: shared vendor and similar amounts but legitimately distinct billing. |
| 6 | The failing examples include the most likely realistic mistakes. | Yes — paying the duplicate, and rejecting a legitimate second invoice, are both covered. |
| 7 | No variant relies on a trick. | Yes — history is agent-visible; the distinguishing fact (different PO line/quantity) is checkable. |
| 8 | Train, dev, test variants come from different fictional companies. | Yes — w02, w04, w06, w08, w10, w12. |
| 9 | *(Domain reviewer)* | N/A. |

## Missing cases

- Duplicate by *vendor invoice number* rather than amount/date (same number resubmitted) — the current duplicates differ in number and match on content; a number-collision variant would test the other direction.
- A duplicate where the first invoice was also rejected/hold rather than paid.

## Notes

Sampled T-739D69 verified: INV-36943 duplicates paid INV-36936 (same vendor/PO/total/date, new number) → reject citing the original. Evidence requirements correctly force naming the prior invoice.

## Decision

- [x] **Approve family**
- [ ] **Approve with changes**
- [ ] **Reject**
