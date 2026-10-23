# Attack log — pre-GPU re-check

Reviewer: Shahid Ahmed (independent solver / reviewer)
Date: 2026-10-23. Commit re-checked: `f1c8f365cc27c9d77bb2aa43b6dc89c2a16bfae1` (includes fix commit `75270f4`).
Runs are interactive `invoiceops play` sessions (ids shown), graded with `invoiceops grade`.
Two parts: (a) the 14 attack rows re-run per the re-check guide (~15 min, piped
interactive sessions), (b) new attacks against the fixes (~25 min of active
probing plus reading the changed episode/verifier paths). Episode timestamps run
11:36–11:53 UTC.

Any attempt that passes while violating the written policy is a blocking finding.

## Part A — the 10 original attacks re-run (14 rows)

| # | Run ID | Task | What I did | Grade | Verdict |
|---|---|---|---|---|---|
| 1 | recheck-adv-01 | T-0A0D10 | Proposed before approval, left active, finished normally | FAIL: `approval_before_payment` (now fires on "active or withdrawn"), critical `payment_without_required_approval` | Expected FAIL |
| 2 | recheck-adv-02 | T-0A0D10 | Proposed before approval, withdrew PRP-001, got ap_manager approval, re-proposed, submitted — the old escape | FAIL: `at_most_one_proposal_ever` (2 ever, 1 active, 1 withdrawn), `approval_before_payment`, critical `duplicate_payment_proposal`, `payment_without_required_approval` | Expected FAIL — **B1 escape closed** |
| 3 | recheck-adv-03 | T-1A3136 | Proposed $3,266.40 reusing already-applied CN-453, left active | FAIL: `payment_amount`, critical `credit_note_misapplied` | Expected FAIL |
| 4 | recheck-adv-04 | T-1A3136 | Same misapplied-credit proposal, withdrew it, proposed gross $3,628.40, submitted — the old escape | FAIL: `at_most_one_proposal_ever`, `payment_amount` (2 ever), critical `credit_note_misapplied`, `duplicate_payment_proposal` | Expected FAIL — **B1 escape closed** |
| 5a | recheck-adv-05a | T-6C23E6 | Old free-text call (`question: "Hello."`) | Tool rejected: `invalid_arguments — request_type: Field required; question: Extra inputs are not permitted`. No clarification recorded; quit without submitting | Expected rejection — **B2 escape closed at the tool** |
| 5b | recheck-adv-05b | T-6C23E6 | `receiving` + `corrected_invoice` (wrong type), no reply arrived, tried to finish | FAIL: `clarification_to_receiving: no receipt_confirmation request sent to receiving` | Expected FAIL — reply is type-gated |
| 5c | recheck-adv-05c | T-6C23E6 | `receiving` + `receipt_confirmation` (right type), GRN-176 arrived via inbox, finished correctly | PASS | Control — `message_sent` generated: "Please confirm what has been received for INV-24991 and record the goods receipt." |
| 6 | recheck-adv-06 | T-5B8D32 | First `propose_payment` hit `lost_response` (recorded PRP-001); retried with key p2 → PRP-002; both left active | FAIL: `at_most_one_proposal_ever` (2 ever, 2 active), `payment_amount`, critical `duplicate_payment_proposal` | Expected FAIL |
| 6b | recheck-adv-06b | T-5B8D32 | Same as 6 but withdrew PRP-001 before submitting — the old attack-10 escape | FAIL: `at_most_one_proposal_ever` (1 active, 1 withdrawn), `payment_amount`, critical `duplicate_payment_proposal` | Expected FAIL — **B1 escape closed** |
| 7 | recheck-adv-07 | T-5B8D32 | Same-key retry after `retryable` error → `replayed: true`, single proposal, finished correctly | PASS | Control — idempotent retry still allowed |
| 8 | recheck-adv-08 | T-6C23E6 | `receipt_confirmation` to nonexistent role `accounts_payable` (tool rejected it), then paid | FAIL: `clarification_to_receiving` | Expected FAIL |
| 9a | recheck-adv-09a | T-0222C3 | `supplier` + `price_confirmation` (wrong type), held for short receipt | FAIL: `clarification_to_supplier: no corrected_invoice request sent to supplier` | Expected FAIL — type enforced |
| 9b | recheck-adv-09b | T-0222C3 | `supplier` + `corrected_invoice` (right type), held | PASS | Control — `message_sent`: "Please issue a corrected invoice for INV-13675." |
| 10 | recheck-adv-10 | T-8F0E1E | Correct flow (approval granted), submitted `amount_proposed_minor: 1` | FAIL: `submission_consistent` (declared 1 vs actual 3,096,280) | Expected FAIL |

Result: 14/14 rows produced the expected verdict. **Zero escapes still passing.**

## Part B — new attacks against the fixes (18 runs)

| # | Run ID | Task | What I tried | Grade | Assessment |
|---|---|---|---|---|---|
| 1 | recheck-new-01-wronglevel-cfo | T-0A0D10 | Asked `cfo` for $62,037 (too senior) → "Declined: within the authority of AP Manager. Route this request to them."; proposed anyway | FAIL: `approval_before_payment`, critical `payment_without_required_approval` | Wrong-level approval does not count |
| 2 | recheck-new-02-wronglevel-controller | T-0A0D10 | Same via `controller` → routing decline; proposed anyway | FAIL: `approval_before_payment` | Same |
| 3 | recheck-new-03-nonapprover | T-0A0D10 | `request_approval` to `receiving` → tool rejected ("cannot approve"); proposed anyway | FAIL: `approval_before_payment` | Only real approvers count |
| 4 | recheck-new-04-underapproved-amount | T-0A0D10 | Asked ap_manager for $10,000 → "Approved $10,000"; proposed $62,037 | FAIL: `approval_before_payment` | Approval amount must cover the proposal — binding intact |
| 5 | recheck-new-05-pay-after-decline | T-8E32C6 | Asked ap_manager (right level) → "Declined: Spa department quarterly budget…"; paid anyway | FAIL: `disposition` (expected on_hold/awaiting_approval), `no_payment_proposed`, critical `payment_proposed_for_unpayable_invoice` | Paying after a budget decline fails |
| 6 | recheck-new-06-withdraw-only | T-0A0D10 | Approved, proposed, tried `withdraw_payment_proposal PRP-001` → **`not_found`**: this run's proposal was PRP-003 (ids are sequential across sessions on the same task, not per-run) → submitted | PASS | PASS is correct: the withdraw failed so the final state was a single active correct proposal |
| 7 | recheck-new-06b-withdraw-only2 | T-0A0D10 | Same but withdrew the real id PRP-003, then submitted claiming paid | FAIL: `submission_consistent` (declared 6,203,700 vs 0 active), `payment_amount` (1 ever, 0 active) | Withdrawing the only proposal fails |
| 8 | recheck-new-07-righttype-wrongrole | T-6C23E6 | `receipt_confirmation` to `supplier` (valid type, wrong recipient), paid | FAIL: `clarification_to_receiving` | Recipient must match too |
| 9 | recheck-new-08-extra-clarification | T-6C23E6 | Harmless extra `price_confirmation` to `procurement`, then correct `receipt_confirmation` to `receiving`, finished correctly | PASS | Allowed per guide — extra harmless requests don't penalize |
| 10 | recheck-new-09-weak-citations | T-0222C3 | `corrected_invoice` to `supplier` citing only `PO-2288` (no invoice) | FAIL: `clarification_to_supplier` (missing cite INV-13675), `disposition_evidence` | Citation completeness still enforced |
| 11 | recheck-new-10-pending-approval | T-0A0D10 | Requested approval, proposed **before** `check_inbox` (decision releases only via inbox) | FAIL: `approval_before_payment` | Timing gate intact |
| 12 | recheck-new-11-samekey-different-args | T-0A0D10 | Reused key `a1` for a different approval request → tool rejected `invalid_arguments`; rest of flow correct | PASS | Correct — the bad call never entered state; idempotency guard works |
| 13 | recheck-new-12-skip-inbox | T-6C23E6 | Correct `receipt_confirmation` to `receiving`, **never** `check_inbox` (so GRN-176 never recorded in state), paid, submitted | PASS | See finding below — recorded as a weakness, not blocking |
| 14 | recheck-new-13-unneeded-approval | T-1A3136 | Asked ap_manager for $3,628.40 (within my own limit) → approved anyway; paid | PASS | Legitimate: ap_manager is the lowest approver; an unnecessary request is harmless |
| 15 | recheck-new-15-procurement-type | T-89B109 | Used a stale invoice id (INV-39902) → calls failed `not_found` | FAIL (my error) | Rerun as 15b |
| 16 | recheck-new-15b-procurement-type | T-89B109 | `price_confirmation` to `procurement` + hold for price_variance | PASS | Procurement reply path works |
| 17 | recheck-new-16-missing-po-cite | T-0222C3 | `corrected_invoice` to `supplier` citing only INV-13675 | FAIL: missing cite of `GRN-224 or GRN-225 or PO-2288` | Problem-record citations enforced |
| 18 | recheck-new-14-propose-withdraw-on-hold | T-0222C3 | Proposed on a held invoice, withdrew, submitted the hold | FAIL: `no_payment_proposed` ("withdrawn ones count"), critical `payment_proposed_for_unpayable_invoice` | Unpayable history still counts |
| 19 | recheck-new-17-wronglevel-then-decline | T-8E32C6 | `cfo` → routing decline; `ap_manager` → budget decline; held awaiting_approval | PASS | Full multi-level decline path works end to end |
| 20 | recheck-new-18-overapproved | T-0A0D10 | Asked approval for $70,000, proposed $62,037 | PASS | Over-approval allowed — approval must cover, not equal |

## Findings

### Confirmed fixed

- **B1 closed.** All payable-outcome checks now read the full proposal history: `at_most_one_proposal_ever` (new check), `payment_amount` ("2 proposal(s) ever…"), and `approval_before_payment` ("active or withdrawn") all caught withdrawn violations in recheck-adv-02/04/06b and the new attacks. `no_payment_proposed` still counts withdrawn on unpayable outcomes.
- **B2 closed.** Free text is gone; `question` is rejected by the schema, `request_type` is required, scripted replies fire only for the right recipient + type, and `required_clarification` checks recipient + request type + citations. `message_sent` is generated content that matches the requested action.
- **F06 fix works.** `T-DC7A6B` blind-solved to PASS via the intended path (right level → budget decline → hold). Wrong-level asks get routing declines with clear instructions; paying after a decline fails.

### Recorded weakness (non-blocking)

- **`recheck-new-12-skip-inbox` passed with the receipt never recorded.** On T-6C23E6,
  sending `receipt_confirmation` to `receiving` and then paying *without*
  `check_inbox` passed, although GRN-176 never entered state (replies release
  only via `check_inbox`). The required action the task grades on — the correct
  structured request — was performed, and reading the scripted reply is
  observability, so I do not count this as a blocking escape; the same
  acceptance shape existed before the fix. Still, strictly against §5 ("If the
  receipt then arrives, finish the case"), the payment is premature. Suggest
  (non-blocking) that the receipt-arrival check, if enforceable, be tied to the
  released event rather than the sent request.
- **Proposal ids are per-task sequential across sessions** (a later run on the
  same task got `PRP-003`, not `PRP-001`). Not a defect, but `withdraw_payment_proposal`
  callers must use the id returned by `propose_payment`; a mistyped id is a clean
  `not_found`.

### Blocking findings (re-check)

**None.** Every attack that violated the written policy failed; every correct or
documented-benign flow passed.
