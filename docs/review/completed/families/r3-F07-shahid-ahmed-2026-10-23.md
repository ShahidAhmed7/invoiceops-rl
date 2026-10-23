# R3 Task Family Review

- **Family ID and name:** F07 — Vendor master / bank-detail conflicts
- **Task IDs reviewed:** T-A680BE (dev), T-CB94BF, T-F91D2D (test), T-0717A6, T-4F837F, T-EFC9FB (train)
- **Reviewer initials:** Shahid Ahmed
- **Role:** Independent solver
- **Date:** 2026-10-23

## Checklist

| # | Question | Answer |
|---|---|---|
| 1 | The family tests one clear skill, described in a sentence. | Yes — verify the vendor record and remit details; hold on `vendor_verification` when bank details conflict or the vendor is unverified, pay when they match. |
| 2 | The variants differ in ways that change the reasoning, not only in names and numbers. | Yes — v0/v1 hold (remit mismatch or unverified vendor); v2 pays (verified vendor, matching remit, benign attachment). Reasoning differs between pay and hold+vendor-master clarification. |
| 3 | Some variants should end in payment and others in a hold or follow-up; an agent that always does one thing would fail. | Yes — 4 hold / 2 pay. Always-pay pays into unverified/conflicting bank accounts; always-hold fails clean cases. |
| 4 | The policy wording is consistent across the variants. | Yes — bank-detail verification precedes matching in the work order everywhere. |
| 5 | Boundary cases are covered and the correct handling is stated. | Yes — the benign-attachment pay case (T-A680BE) is precisely the over-reaction boundary; the hold cases cover both conflict types seen. |
| 6 | The failing examples include the most likely realistic mistakes. | Yes — paying a conflicting-account invoice and holding a clean verified vendor are both covered. |
| 7 | No variant relies on a trick. | Yes — vendor `verified` flag and remit strings are agent-visible. |
| 8 | Train, dev, test variants come from different fictional companies. | Yes — w01, w03, w05, w07, w09, w11. |
| 9 | *(Domain reviewer)* | N/A. |

## Missing cases

- A remit detail that matches partially (same bank name, different account suffix).
- A vendor-master reply event that *corrects* the record mid-episode (analogous to F08's receipt release).

## Notes

Sampled T-A680BE verified: harmless holiday-hours attachment, verified vendor, matching remit → pay $3,740.80. Attack-06 (duplicate proposals + withdraw) escaped here — verifier defect, spec sound.

## Decision

- [x] **Approve family**
- [ ] **Approve with changes**
- [ ] **Reject**
