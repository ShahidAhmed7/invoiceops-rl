# R3 Task Family Review

- **Family ID and name:** F05 — Credit note application
- **Task IDs reviewed:** T-9362E5 (dev), T-1A3136, T-6F7DAA (test), T-1D6F14, T-6D1A65, T-A50BE6 (train)
- **Reviewer initials:** Shahid Ahmed
- **Role:** Independent solver
- **Date:** 2026-10-23

## Checklist

| # | Question | Answer |
|---|---|---|
| 1 | The family tests one clear skill, described in a sentence. | Yes — decide whether a visible credit note may be applied to this invoice (correct invoice, open status, exactly once). |
| 2 | The variants differ in ways that change the reasoning, not only in names and numbers. | Yes — v0 has an open credit for this invoice (apply → `matched_with_credit`); v1 has an already-applied credit for another invoice (do NOT apply → pay gross); v2 has a credit belonging to a different invoice (do NOT apply). The payable verdict is uniform but the *amount and credit list* differ materially. |
| 3 | Some variants should end in payment and others in a hold or follow-up; an agent that always does one thing would fail. | Partially — all six end in `ready_for_payment`, but a fixed "always apply the visible credit" habit fails on v1/v2 amounts, and "never apply" fails v0. The discrimination is inside the payable outcome, not across statuses. |
| 4 | The policy wording is consistent across the variants. | Yes — credits apply once, only to the referenced invoice; consistent across companies. |
| 5 | Boundary cases are covered and the correct handling is stated. | Yes — the applied-credit (v1) and wrong-invoice-credit (v2) traps are the boundaries that matter. |
| 6 | The failing examples include the most likely realistic mistakes. | Yes — underpaying by reusing CN-453 (T-1A3136) or applying a foreign credit are the realistic errors; both fail while active (manual-adv-03). |
| 7 | No variant relies on a trick. | Yes — credit `applied_to`/status fields are agent-visible. |
| 8 | Train, dev, test variants come from different fictional companies. | Yes — w01, w03, w05, w07, w09, w11. |
| 9 | *(Domain reviewer)* | N/A. |

## Missing cases

- An *open* credit for a different invoice that the agent might wrongly apply anyway (v2 covers this via wrong-invoice — confirm whether a truly foreign-vendor credit exists).
- A credit larger than the invoice (negative payable boundary).

## Notes

Sampled T-1A3136 verified: CN-453 already applied to PAY-78604 on a different invoice → pay gross $3,628.40. This task also hosts the B1 escape (attack-11/manual-adv-04: misuse + withdraw → PASS).

## Decision

- [x] **Approve family**
- [ ] **Approve with changes**
- [ ] **Reject**
