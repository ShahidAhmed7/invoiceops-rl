# R3 Task Family Review

- **Family ID and name:** F11 — Transient tool failure / idempotent retry
- **Task IDs reviewed:** T-C45901 (dev), T-5B8D32, T-5C4594 (test), T-5B4B11, T-CFE072, T-E4FDD8 (train)
- **Reviewer initials:** Shahid Ahmed
- **Role:** Independent solver
- **Date:** 2026-10-23

## Checklist

| # | Question | Answer |
|---|---|---|
| 1 | The family tests one clear skill, described in a sentence. | Yes — when a payment tool call returns a retryable fault, retry with the SAME idempotency key so no duplicate proposal is created. |
| 2 | The variants differ in ways that change the reasoning, not only in names and numbers. | Yes — the fault is constant (lost_response on first `propose_payment`) but the business cases differ: plain pays, credit-note pays, and price-variance holds. |
| 3 | Some variants should end in payment and others in a hold or follow-up; an agent that always does one thing would fail. | Yes — 4 pay / 2 hold; and on payable instances a changed-key retry creates a duplicate that must fail. |
| 4 | The policy wording is consistent across the variants. | Yes — same-key retry rule plus §11's no-second-proposal rule. |
| 5 | Boundary cases are covered and the correct handling is stated. | Yes — the fault itself is the boundary (uncertain state); same-key retry verified benign (manual-adv-07, `replayed: true`, PASS), changed-key + two actives verified failing (manual-adv-06, FAIL). |
| 6 | The failing examples include the most likely realistic mistakes. | Mostly — changed-key + withdraw escapes (attack-10 → PASS); see attack-log B1. Two-active and no-retry cases fail correctly. |
| 7 | No variant relies on a trick. | Yes — the fault is deterministic (on_call=1) and the tool error tells the agent to retry with the same key; it is not random flakiness. |
| 8 | Train, dev, test variants come from different fictional companies. | Yes — w01, w03, w05, w07, w09, w11. |
| 9 | *(Domain reviewer)* | N/A. |

## Missing cases

- A retryable fault on `create_clarification` or `request_approval` (currently only `propose_payment` is faulted).
- Two sequential faults (retry once, fault again) — tests whether agents loop correctly.

## Notes

Sampled T-5B8D32 verified: lost-response fault + open CN-875 → same-key retry, pay $2,312.00 with credit. The idempotent path is genuinely exercised end-to-end.

## Decision

- [x] **Approve family**
- [ ] **Approve with changes**
- [ ] **Reject**
