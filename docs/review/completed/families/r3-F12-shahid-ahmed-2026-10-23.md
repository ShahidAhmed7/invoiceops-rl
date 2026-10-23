# R3 Task Family Review

- **Family ID and name:** F12 — Stale policy / effective-date discrimination
- **Task IDs reviewed:** T-F88990 (dev), T-11EA31, T-FB1EDA (test), T-02FF9D, T-852F31, T-FA734A (train)
- **Reviewer initials:** Shahid Ahmed
- **Role:** Independent solver
- **Date:** 2026-10-23

## Checklist

| # | Question | Answer |
|---|---|---|
| 1 | The family tests one clear skill, described in a sentence. | Yes — both a superseded and a current policy document exist in the store; determine which is effective on the business date and apply its rule. |
| 2 | The variants differ in ways that change the reasoning, not only in names and numbers. | Yes — the current-vs-stale rule pair flips between instances: T-11EA31's current rule is `require_corrected_invoice` (stale was `pay_received_portion`); T-852F31's outcome is `pay_received_portion`, i.e., the current rule is the other one. Price-variance holds also occur. The agent must read dates, not memorise "the newer rule is X". |
| 3 | Some variants should end in payment and others in a hold or follow-up; an agent that always does one thing would fail. | Yes — 5 hold / 1 pay across the six; and which rule governs changes per instance. |
| 4 | The policy wording is consistent across the variants. | Yes — each world renders both versions with explicit effective ranges. |
| 5 | Boundary cases are covered and the correct handling is stated. | Yes — T-11EA31 verified contiguous ranges (stale to 2026-07-06, current from 2026-07-06, no gap/overlap). |
| 6 | The failing examples include the most likely realistic mistakes. | Yes — applying the superseded rule produces a concretely wrong outcome (pay portion vs hold) and fails. |
| 7 | No variant relies on a trick. | Yes — effective dates are printed in the documents; the distractor is discoverable, not hidden. |
| 8 | Train, dev, test variants come from different fictional companies. | Yes — w02, w04, w06, w08, w10, w12. |
| 9 | *(Domain reviewer)* | N/A. |

## Missing cases

- A business date *within* the stale policy's range (agent must apply the OLD rule, not just pick the newest document).
- Three stacked versions or an overlapping effective range (ambiguous case — should probably be avoided intentionally).

## Notes

Sampled T-11EA31 verified: short receipt under current `require_corrected_invoice` → hold + supplier clarification; the stale `pay_received_portion` would have produced a payment — the discrimination is real.

## Decision

- [x] **Approve family**
- [ ] **Approve with changes**
- [ ] **Reject**
