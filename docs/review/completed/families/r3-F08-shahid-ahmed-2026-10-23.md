# R3 Task Family Review

- **Family ID and name:** F08 — Missing receipt and clarification
- **Task IDs reviewed:** T-71E1D2 (dev), T-6C23E6, T-7E294F (test), T-1F835F, T-80BC88, T-D27F95 (train)
- **Reviewer initials:** Shahid Ahmed
- **Role:** Independent solver
- **Date:** 2026-10-23

## Checklist

| # | Question | Answer |
|---|---|---|
| 1 | The family tests one clear skill, described in a sentence. | Yes — when no receipt exists, send the required clarification to receiving, then handle whatever the reply event changes (receipt posted → resolve per policy; no receipt → hold `missing_receipt`). |
| 2 | The variants differ in ways that change the reasoning, not only in names and numbers. | Yes — T-6C23E6/T-80BC88 get a releasing event (receipt posts → pay); T-71E1D2/T-D27F95 get no release → hold `missing_receipt`; T-7E294F requires two clarifications and ends in corrected-invoice hold; T-1F835F ends in partial pay. The reply determines the outcome. |
| 3 | Some variants should end in payment and others in a hold or follow-up; an agent that always does one thing would fail. | Yes — 3 payable / 3 hold across the six, gated on post-clarification state. |
| 4 | The policy wording is consistent across the variants. | Yes — the missing-receipt clause and the receiving role are consistent; downstream handling differs by company rule. |
| 5 | Boundary cases are covered and the correct handling is stated. | Yes — released vs unreleased is the boundary; the reply-dependent branching is the intended design. |
| 6 | The failing examples include the most likely realistic mistakes. | Yes — skipping the clarification fails (attack-12, manual-adv-08). |
| 7 | No variant relies on a trick. | **Mostly** — the event release mechanism is legitimate, but a content-free clarification also releases the receipt (manual-adv-05): the trigger keys on recipient only, not on a meaningful request. This is a verification/event-fidelity gap rather than a spec trick; see attack-log B2. |
| 8 | Train, dev, test variants come from different fictional companies. | Yes — w02, w04, w06, w08, w10, w12. |
| 9 | *(Domain reviewer)* | N/A. |

## Missing cases

- A reply event that posts only a *partial* receipt (then the short-receipt rule must engage).
- An invoice whose receipt is already present (agent must not send an unnecessary clarification — currently unpenalised).

## Notes

Sampled T-6C23E6 verified end-to-end: vacuous clarification still released GRN-176 and the full pay flow passed — the release semantics are recipient-triggered. Spec design is good; the semantic trigger is the weak point.

## Decision

- [x] **Approve family** — spec sound; event-trigger semantics flagged under B2.
- [ ] **Approve with changes**
- [ ] **Reject**
