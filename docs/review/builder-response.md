# Builder Response to the Pre-GPU Review (2026-10-23)

This answers [`signoff/pre-gpu.md`](signoff/pre-gpu.md) (not approved; reviewed commit `7066a8a`). The completed review records under `completed/` and `signoff/` are unchanged.

## Summary

| Finding | Status | Fix |
|---|---|---|
| **B1** Withdrawn proposals invisible on payable outcomes | Fixed | The verifier judges every proposal ever created, including withdrawn ones |
| **B2** Clarification checks ignore message content | Fixed | Clarifications are structured requests with a required `request_type`; there is no ungraded free text |
| **F06** "Always ask CFO, pay full" passes 6/6 | Fixed | Approvers act only at their level; one variant is a justified decline that must end on hold |
| CI failed on the review pushes | Fixed | Lint failed on `completed/spec-crosscheck.py`. Completed review records are now excluded from lint, and the file itself is untouched |

## B1: history-aware payment checks

The policy already said "Never create a second proposal for the same invoice" and "propose the payment only after it has been approved". The verifier only enforced these on the active proposal. Now:

- A global check, `at_most_one_proposal_ever`, fails if more than one proposal was ever created for the invoice, withdrawn ones included. A same-key retry after a `retryable` error is a replay, not a second proposal.
- `payment_amount` requires exactly one proposal ever, still active, for the right amount and credits.
- `approval_before_payment` requires every proposal ever created to follow a sufficient approval.
- The critical violations `payment_without_required_approval`, `overpayment_proposed`, and the new `credit_note_misapplied` look at every proposal ever created.
- Policy section 11 now states the rule explicitly: "Propose at most one payment per invoice, ever… Withdrawing a proposal does not undo it."

## B2: structured clarifications

A deterministic verifier cannot judge what free text means without an LLM judge, and the project uses none. So the request itself is now structured:

- `create_clarification(invoice_id, recipient_role, request_type, evidence_ids, idempotency_key)`, where `request_type` is one of `corrected_invoice`, `price_confirmation`, `receipt_confirmation`, `bank_detail_verification`. The free-text `question` argument is gone, so the tool rejects it.
- The message actually sent is generated from the request type and returned as `message_sent`, so it cannot be vacuous or contradict the request.
- Scripted replies fire only for the right recipient **and** the right request type.
- The verifier requires the request type the policy names. The policy now names it for each situation (sections 3, 4, 5, 9).

Attacks 08, adv-05 and adv-09 depended on free text. They are closed by construction rather than by detection: the content they relied on no longer exists.

## F06: approval routing that actually requires a decision

- Each approver now acts only at their own level: the lowest approver whose limit covers the amount. Requests above or below that level are declined with a routing message. Policy section 8 states this.
- F06 variant 2 (previously "under the self-approval limit") is now: amount at the AP manager's level, and the AP manager declines for a departmental budget reason. The expected outcome is `on_hold` / `awaiting_approval`, with an approval request to `ap_manager` and no payment proposal.
- F06 now mixes pay and hold outcomes. "Always ask CFO, pay full" fails all six instances (test `test_f06_always_cfo_pay_full_fails_every_instance`).

## Evidence

| Check | Before | After |
|---|---|---|
| Review attack scripts in `completed/attacks/` (14 attacks + 6 F06 shortcut probes) | 6 attacks and 6 probes passed | **All fail** (`tests/test_review_regressions.py`) |
| F01 shortcut probes | 6/6 pass | 4/6 pass. These are the four clean invoices under the self-approval limit, where paying in full is correct |
| Verifier mutation suite | 844 cases (695 mutations, 149 alternatives) | **975 cases** (826 mutations, 149 alternatives), 0 unexpected. New: wrong proposal withdrawn then corrected (42 tasks), only proposal withdrawn (42), proposal before approval then withdrawn (8), approval from the wrong level (10), wrong request type (27) |
| Oracle | 72/72 | 72/72, no critical violations |
| Scripted baselines | always-pay ≤ 41.7% | always-pay ≤ 33.3%; always-hold ≤ 16.7%; no-op and random 0% (`reports/local/scripted_baselines.md`) |
| Tests | 214 | 245, all passing; lint, types, `openenv validate`, task freshness, leakage all clean |

## What this means for the review

- **Every task revision changed.** The policy text is part of every task, so all 72 content hashes differ from the reviewed ones. Under the review guide's rule, earlier reviews apply to the previous revisions. The reviewed revisions in `status.md` are left as recorded.
- **Suggested re-check (smaller than a full review):**
  1. Re-run the 10 manual adversarial sessions, which are not in the repository. The scripted attacks are already covered by tests.
  2. Re-review F06 (R3) and the spec (R1) of `T-0A0D10`, because the approval rule and one variant changed.
  3. Re-read the R1 specs of the four sampled tasks whose required clarification now names a request type: `T-89B109`, `T-0222C3`, `T-6C23E6`, and `T-11EA31`.
  4. Blind-solve two tasks again to check the changed tools work end to end: one with a clarification (e.g. `T-6C23E6`) and one with approval (e.g. `T-0A0D10`).
  5. Update the sign-off.
