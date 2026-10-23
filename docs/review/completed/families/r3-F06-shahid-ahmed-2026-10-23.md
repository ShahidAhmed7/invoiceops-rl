# R3 Task Family Review

- **Family ID and name:** F06 — Approval routing
- **Task IDs reviewed:** T-DC7A6B (dev), T-0A0D10, T-0A802E (test), T-2D6100, T-8979C8, T-8E32C6 (train)
- **Reviewer initials:** Shahid Ahmed
- **Role:** Independent solver
- **Date:** 2026-10-23

## Checklist

| # | Question | Answer |
|---|---|---|
| 1 | The family tests one clear skill, described in a sentence. | Intended skill: decide whether an invoice needs approval (amount vs the assistant self-approval limit) and obtain it from an authorised approver before proposing payment. |
| 2 | The variants differ in ways that change the reasoning, not only in names and numbers. | Partially — v0/v1 require approval (amounts $19,992–$184,779 across company limits); v2 are deliberately just *under* the self-approval limit (T-DC7A6B $19,864.50; T-8E32C6 $7,650.00). The under-limit cases should test "no approval needed", but nothing distinguishes "correctly skipped" from "unnecessarily requested". |
| 3 | Some variants should end in payment and others in a hold or follow-up; an agent that always does one thing would fail. | **No** — all six are `ready_for_payment/matched`. The fixed habit "always request CFO approval, then pay in full" passed **6/6** (shortcut-F06 probes, incl. T-DC7A6B). Requesting approval when not required violates no written rule, so the family never forces a routing *decision* — it only checks the approval was obtained when required. |
| 4 | The policy wording is consistent across the variants. | Yes — the threshold/approver-tier clause is consistent; parameters differ per company. |
| 5 | Boundary cases are covered and the correct handling is stated. | Partially — just-under-limit cases exist (v2), which is the right boundary; but the verifier cannot distinguish a correct skip from an unnecessary request, so the boundary is not actually tested. |
| 6 | The failing examples include the most likely realistic mistakes. | Partially — paying over-limit without approval fails correctly (manual-adv-01); the missing failure is "over-approval" which policy arguably permits. |
| 7 | No variant relies on a trick. | Yes — limits and approver limits are printed. |
| 8 | Train, dev, test variants come from different fictional companies. | Yes — w02, w04, w06, w08, w10, w12. |
| 9 | *(Domain reviewer)* | N/A. |

## Missing cases

- An over-limit invoice that must **not** be paid (e.g., combined with a hold reason) — currently every approval-required instance is also payable.
- An approver-tier rule where "always CFO" is wrong (e.g., CFO reserved for >$1M, manager must handle mid-tier).
- A denial path (approval refused → hold) — no instance exercises `decision != approved`.

## Notes

This family fails the guide's "fixed habits must not solve a family" criterion in spirit: the shortcut passes without violating written policy, so the fix is a family-design change (add discriminating instances), not a verifier patch. Approver-amount binding in `_approved_before` is itself correct (limit ≥ proposal amount, event amount ≥ proposal amount, before the proposal step).

## Decision

- [ ] **Approve family**
- [x] **Approve with changes** — add at least one instance where the always-approve habit is wrong (non-payable over-limit case or tiered-approver rule).
- [ ] **Reject**
