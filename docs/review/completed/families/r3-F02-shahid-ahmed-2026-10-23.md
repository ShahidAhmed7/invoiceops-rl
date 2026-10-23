# R3 Task Family Review

- **Family ID and name:** F02 — Price discrepancy and tolerance
- **Task IDs reviewed:** T-D30567 (dev), T-89B109, T-B2A72C (test), T-25DE39, T-6698FA, T-B97FAB (train)
- **Reviewer initials:** Shahid Ahmed
- **Role:** Independent solver
- **Date:** 2026-10-23

## Checklist

| # | Question | Answer |
|---|---|---|
| 1 | The family tests one clear skill, described in a sentence. | Yes — compute the PO-implied amount vs the invoiced amount, apply the percent-plus-cap tolerance, and hold+clarify (procurement) when over tolerance. |
| 2 | The variants differ in ways that change the reasoning, not only in names and numbers. | Yes — v0/v2 are payable (within tolerance or exact); v1 is over tolerance → `on_hold/price_variance` + procurement clarification. The reasoning differs (pay vs hold). |
| 3 | Some variants should end in payment and others in a hold or follow-up; an agent that always does one thing would fail. | Yes — 4 pay / 2 hold. Always-pay fails the two holds; always-hold fails the four pays. |
| 4 | The policy wording is consistent across the variants. | Yes — same tolerance clause rendered with per-company parameters (2.5%/$500 Juniper, etc.). |
| 5 | Boundary cases are covered (for example, a price exactly at the tolerance limit) and the correct handling is stated. | Unsure — within-tolerance and over-tolerance both exist, but no instance sits exactly at the tolerance boundary (percent-vs-cap edge, e.g., variance == cap). |
| 6 | The failing examples include the most likely realistic mistakes. | Yes — paying an over-tolerance invoice, and holding without the procurement clarification, are the realistic errors. |
| 7 | No variant relies on a trick: unclear IDs, hidden requirements, padding, or random failures. | Yes — all parameters are in the policy document; PO revisions are visible. |
| 8 | Train, development, and test variants come from different fictional companies. | Yes — w02, w04, w06, w08, w10, w12. |
| 9 | *(Domain reviewer)* | N/A — independent solver. |

## Missing cases

- Exact-tolerance boundary (variance exactly equal to the tolerance amount; whether inclusive is a policy-reading test).
- A case where the *cap* binds rather than the percentage (high-value invoice where 2.5% > $500 cap is the active limit) — verify the suite exercises both branches of min(pct, cap).

## Notes

Sampled T-89B109 verified: variance $91.67 > $61.54 tolerance → hold correctly. The `matched_within_tolerance` reason code on within-tolerance pays keeps them distinct from exact matches.

## Decision

- [x] **Approve family**
- [ ] **Approve with changes**
- [ ] **Reject**
