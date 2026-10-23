# R3 Task Family Review

- **Family ID and name:** F01 — Clean match (three-way match → pay)
- **Task IDs reviewed:** T-8F0E1E (dev), T-CF549E, T-E673B5 (test), T-BE5CAB, T-C4C410, T-D2DA12 (train)
- **Reviewer initials:** Shahid Ahmed
- **Role:** Independent solver
- **Date:** 2026-10-23

## Checklist

| # | Question | Answer |
|---|---|---|
| 1 | The family tests one clear skill, described in a sentence. | Yes — execute the full match workflow (invoice ↔ PO ↔ receipt ↔ vendor) and pay correctly, including recognising when approval is required. |
| 2 | The variants differ in ways that change the reasoning, not only in names and numbers. | Partially — v0/v1 differ in scale and distractor POs; v2 adds the approval threshold (T-8F0E1E $30,962.80 > $12,000; T-C4C410 $54,675.95 > limit). The approval dimension does change reasoning, but every instance still ends in `pay/matched`. |
| 3 | Some variants should end in payment and others in a hold or follow-up; an agent that always does one thing would fail. | **No** — all six instances are `ready_for_payment/matched`. A fixed "always pay after CFO approval" habit passes 6/6 (shortcut-F01 probes). The family is a clean-positive baseline by design, but it has no negative case. |
| 4 | The policy wording is consistent across the variants. | Yes — same policy skeleton rendered per company; thresholds vary by world parameters only. |
| 5 | Boundary cases are covered (for example, a price exactly at the tolerance limit) and the correct handling is stated. | Unsure — v2 probes the approval boundary from above; no instance sits just under the limit, and no near-miss match (e.g., 1-unit quantity difference) exists. |
| 6 | The failing examples include the most likely realistic mistakes. | Yes — wrong amount, missing approval, wrong PO matching are the realistic errors (all confirmed fail modes during probes). |
| 7 | No variant relies on a trick: unclear IDs, hidden requirements, padding, or random failures. | Yes — all facts are agent-visible. |
| 8 | Train, development, and test variants come from different fictional companies. | Yes — six distinct worlds (w01, w03, w05, w07, w09, w11). |
| 9 | *(Domain reviewer)* This situation occurs in real AP work, and the handling matches common practice. | N/A — independent solver. |

## Missing cases

- A just-under-self-approval-limit invoice (pay without approval where over-approving wastes approver time — currently never penalised).
- A clean-match instance where the *bank details* differ (bridges to F07).

## Notes

The uniform outcome makes F01 weak as a discrimination instrument but reasonable as a "does the harness work at all" family. The shortcut probe result (6/6 via always-approve + pay full) is honest evidence, not a verifier bug — nothing in written policy forbids over-approving.

## Decision

- [x] **Approve family** — as a clean-positive baseline; its uniformity is documented.
- [ ] **Approve with changes**
- [ ] **Reject**
