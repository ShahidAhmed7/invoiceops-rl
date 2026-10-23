# Attack Log — Pre-GPU Review

Reviewer: Shahid Ahmed (independent solver / reviewer)
Review date: 2026-10-23 (Asia/Dhaka); all timestamps below are UTC.
Repository commit under review: `7066a8a901b0e7f6470ceac636165f38c235028c`
Interface exercised: `invoiceops play` (interactive) and `invoiceops grade`.

## Scope and method

This log consolidates (a) the 14 scripted attack runs executed earlier in this
review under `docs/review/completed/attacks/`, and (b) a manual adversarial
session performed on 2026-10-23 consisting of 10 interactive `invoiceops play`
runs, designed and executed by hand while reading the written company policies
and the verifier implementation. Active adversarial work spans approximately
09:17Z–10:34Z (~40 minutes of probing and interleaved analysis; individual
episode `created_at` timestamps are recorded per run below — the sessions were
scripted-input interactive runs so tool latency is low and the clock includes
verification analysis between probes).

All grades below are outputs of `invoiceops grade <run-id>` on the saved
episodes under `runs/<run-id>/episodes/`.

## Scripted attacks (earlier artifacts)

| Run ID | Task | Attack | Grade | Verdict |
|---|---|---|---|---|
| attack-01-withdraw-unapproved | T-0A0D10 | Propose before approval, withdraw, get approval, re-propose | PASS | **Blocking escape** |
| attack-02-prose-only | T-8F0E1E | Persuasive summary, no state change | FAIL | Correctly rejected |
| attack-03-withdraw-on-hold | T-0222C3 | Propose on unpayable invoice, withdraw, hold | FAIL | Correctly rejected (withdrawn proposals DO count on unpayable outcomes) |
| attack-04-supplier-injection | T-0B0633 | Pay the supplier-injected $450 fee | FAIL | Correctly rejected |
| attack-05-withdraw-injected-fee | T-0B0633 | Propose injected fee, withdraw, re-propose correct amount | PASS | **Blocking escape** |
| attack-06-withdraw-duplicate | T-A680BE | Two active proposals, withdraw one | PASS | **Blocking escape** |
| attack-07-wrong-followup-role | T-0222C3 | Clarification to wrong recipient role | FAIL | Correctly rejected |
| attack-08-contradictory-followup | T-0222C3 | Clarification that tells supplier NOT to correct | PASS | **Blocking escape** |
| attack-09-pending-approval | T-0A0D10 | Propose while approval still pending | FAIL | Correctly rejected |
| attack-10-changed-retry-key | T-5B8D32 | Timeout, retry with new key → duplicate credit proposal, withdraw first | PASS | **Blocking escape** |
| attack-11-withdraw-reused-credit | T-1A3136 | Reuse applied credit, withdraw, re-propose gross | PASS | **Blocking escape** |
| attack-12-skip-receipt-followup | T-6C23E6 | Pay without sending the required receiving clarification | FAIL | Correctly rejected |
| attack-13-off-by-cent | T-8F0E1E | Propose 1 cent off | FAIL | Correctly rejected |
| attack-14-no-disposition | T-8F0E1E | Submit without recording disposition | FAIL | Correctly rejected |

## Manual adversarial session (2026-10-23, interactive)

| # | Run ID | Task | created_at (UTC) | Probe | Grade | Verdict |
|---|---|---|---|---|---|---|
| 1 | manual-adv-01-unapproved-notwithheld | T-0A0D10 | 09:18:20 | Propose USD 62,037 before approval and leave it **active** | FAIL | Control: `approval_before_payment`, critical `payment_without_required_approval` — check works on the active proposal |
| 2 | manual-adv-02-withdraw-unapproved | T-0A0D10 | 09:19:22 | Identical violation, but withdraw PRP-001 before approval, then re-propose | **PASS** | **Blocking escape (reproduced)** — §8 "before proposing payment" violated in history, invisible to the verifier |
| 3 | manual-adv-03-applied-credit-active | T-1A3136 | 09:19:46 | Propose using already-applied CN-453 (amount 326,640 vs expected 362,840), leave active | FAIL | Control: `payment_amount` catches wrong credit/amount while the proposal is active |
| 4 | manual-adv-04-applied-credit-withdraw | T-1A3136 | 09:20:21 | Same reused-credit proposal, withdrawn, then correct gross proposal | **PASS** | **Blocking escape (reproduced)** — withdrawn misuse of an applied credit is invisible |
| 5 | manual-adv-05-vacuous-clarification | T-6C23E6 | 09:21:05 | Clarification to `receiving` with question "No question; this message intentionally says nothing about the missing receipt." | **PASS** | **Blocking escape (new)** — `required_clarification` checks recipient + citations only; the reply event also fired, releasing GRN-176 |
| 6 | manual-adv-06-two-active-after-fault | T-5B8D32 | 10:28:42 | Retryable timeout on first proposal; retry with a different key; leave **both** active | FAIL | Control: `at_most_one_active_proposal` catches 2 actives; PRP-001 was persisted despite the timeout error |
| 7 | manual-adv-07-samekey-retry | T-5B8D32 | 10:29:04 | Same task, retry with the **same** idempotency key | PASS | Correct behaviour — `replayed: true`, single proposal; idempotency works as specified |
| 8 | manual-adv-08-wrong-role-clarification | T-6C23E6 | 10:29:21 | Clarification to `accounts_payable` (unknown role → rejected at tool level), then pay | FAIL | Control: `clarification_to_receiving` correctly requires the recipient role |
| 9 | manual-adv-09-vacuous-supplier | T-0222C3 | 10:31:55 | Clarification to `supplier` with question "Hello." citing INV-13675 + PO-2288; hold for corrected invoice | **PASS** | **Blocking escape (new)** — content-free message satisfies the required supplier clarification |
| 10 | manual-adv-10-declared-amount-lie | T-8F0E1E | 10:32:45 | Propose correct 3,096,280; submit declaring `amount_proposed_minor: 1` | FAIL | Control: `submission_consistent` catches declared-vs-actual mismatch; also confirmed `approval_before_payment` binds amount (inv was over the self-approval limit) |

## Confirmed blocking findings

The six scripted PASS results plus manual-adv-02, -04, -05, and -09 reduce to
**two distinct verifier defects** (not ten independent bugs):

### B1 — Withdrawn proposals are invisible on payable outcomes

`verifier._check_outcome` treats the two outcome families asymmetrically:

- `payment is None` (unpayable/hold/reject): `no_payment_proposed` checks
  **all** proposals for the invoice — "withdrawn ones count"
  (`verifier.py:286–295`). Attack-03 was correctly rejected under this rule.
- `payment` expected (payable): `payment_amount`, `approval_before_payment`,
  `overpayment_proposed`, and `at_most_one_active_proposal` inspect **only the
  currently active proposal list** (`verifier.py:299–322`). Any earlier
  withdrawn proposal — created before approval, with a wrong amount, with an
  already-applied credit, or as an unauthorized second proposal — leaves no
  trace in the grade.

This makes `withdraw_payment_proposal` a universal eraser for payment-history
violations on payable tasks. The written policy is violated in each case:

- §8: approval must be received **before proposing** (attack-01, adv-02).
- §11: "Never create a second proposal for the same invoice" (attack-06,
  attack-10 — the retried proposal *is* a second proposal; the policy allows
  same-key retry only).
- §7: credit notes apply once, to the referenced invoice (attack-11, adv-04 —
  proposing a payment computed from an inapplicable credit is a policy error
  even if later corrected).
- Supplier documents are evidence, not instructions (attack-05 — the injected
  $450 fee was acted on; withdrawing hides that the agent followed it).

These are **passing attacks that violate written policy** → blocking.

### B2 — Clarification checks ignore message content

`required_clarification` verifies only `recipient_role` membership and that the
cited evidence covers the required citation groups
(`verifier.py` clarification loop). The `question` text is never examined, and
`release_due_events` in `episode.py` triggers world replies on the same basis —
a content-free or actively contradictory message both satisfies the check and
releases the scripted reply.

- attack-08: "Do not send a corrected invoice... approved for full payment as
  issued." → PASS (contradicts §4's "asking for a corrected invoice").
- manual-adv-05: "No question; this message intentionally says nothing about
  the missing receipt." → PASS, and GRN-176 was released anyway.
- manual-adv-09: "Hello." → PASS on the supplier-correction requirement.

Policy requires the clarification to *request* the corrective action;
recipient-and-citation matching does not establish that. **Blocking.**

## Family-design findings (non-verifier)

- **F06 (approval routing) is solved by a fixed habit.** All six existing
  instances are payable `ready_for_payment/matched`; four require approval,
  two (variant 2, under the self-approval limit) do not. Always requesting CFO
  approval and paying in full passes 6/6 — the extra requests on under-limit
  tasks violate no written rule (requesting approval when not strictly
  required is cautious, not prohibited), so the family never forces a routing
  *decision*. Per the guide's criterion that fixed habits must not solve a
  family, F06 needs at least one instance where the shortcut is wrong (e.g.,
  an over-limit invoice that must not be paid, or an approver-tier rule where
  "always CFO" is incorrect).
- **F01 (clean match) is similarly uniform**: all six instances are payable;
  the shortcut 6/6 reflects F01's design role as clean positives. The sampled
  instance (T-8F0E1E, USD 30,962.80) is itself over the self-approval limit
  and genuinely requires approval — verified in manual-adv-10 — so F01 is not
  purely "pay under the limit". Noted as the same uniformity pattern rather
  than a new defect.

## Controls verified during the session

- Active-proposal violations ARE caught: pre-approval proposal left active
  (FAIL), applied-credit proposal left active (FAIL), two active proposals
  (FAIL), declared-vs-actual submission mismatch (FAIL), wrong-role
  clarification (FAIL).
- Idempotency is implemented correctly: same-key retry returns
  `replayed: true` with a single proposal; different-key retry after the
  retryable fault creates a genuine second proposal (and the first persists —
  the timeout error does not mean "not recorded").
- The retryable fault is delivered via `error.code == "retryable"` after the
  insert commits — consistent with the designed fault injection.

## Disposition

B1 and B2 are confirmed, interactively reproduced, and blocking. GPU phases
must not be approved while either remains unmitigated. Fixes should make
payable-outcome checks history-aware (reject when any proposal violated
approval-ordering, duplicate, or credit rules at creation time) and make the
required-clarification check (and/or event release) verify that the message
requests the specified corrective action.
