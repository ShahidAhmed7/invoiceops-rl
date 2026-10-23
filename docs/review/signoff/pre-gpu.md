# Pre-GPU Review Sign-off

- Reviewer: Shahid Ahmed
- Role: Independent solver
- Date: 2026-10-23
- Path: Standard
- Repository commit reviewed: `7066a8a901b0e7f6470ceac636165f38c235028c`
- Sample (from Step 1): T-8F0E1E (F01), T-89B109 (F02), T-0222C3 (F03),
  T-739D69 (F04), T-1A3136 (F05), T-0A0D10 (F06), T-A680BE (F07),
  T-6C23E6 (F08), T-6BAF87 (F09), T-0B0633 (F10), T-5B8D32 (F11),
  T-11EA31 (F12)

## Results
- Blind solves passed by verifier: 12 / 12 (solver agrees with every grade; no
  disagreement where the solver was right)
- Verifier disagreements found: 2 defect classes confirmed — see Blocking
  findings (all resolved: no)
- Spec reviews: 12 approved, 0 approved with changes, 0 rejected
  (`docs/review/completed/<TASK>/r1-shahid-ahmed-2026-10-23.md`)
- Family reviews: 11 approved, 1 approved with changes (F06), 0 rejected
  (`docs/review/completed/families/r3-FXX-shahid-ahmed-2026-10-23.md`)
- Mutation report: all rejected yes; all alternatives accepted yes —
  844 cases, 0 unexpected; manual assessment in
  `completed/mutation-assessment.md` (suite does not cover the confirmed
  escapes: no withdraw-then-submit or content-varying mutations exist)
- Attack attempts: 24 tried (14 scripted + 10 manual adversarial sessions,
  ~40 min active), 10 succeeded — all blocking
  (`docs/review/completed/attack-log.md`; one further manual run,
  manual-adv-07, passed but performed the intended same-key retry, so it is
  a control, not an attack success)
- Scripted baselines as expected: yes — oracle 100% every family; no-op 0%;
  always-hold 11.1% (only exception-family cases); always-pay 33.3% (every
  pass is a task whose expected outcome is "pay in full"); random 0%
- Visibility audit clean: yes — no private/hidden data reaches the agent;
  `completed/visibility-audit.md`
- Prompt v2: approved — general working advice only; no task IDs, answers,
  family mappings, or split info; sha256
  `da1dd707ab199f8b55877cda332d6121dd7844d2f2d3031ebab20c7485c98ae0`;
  `completed/prompt-v2-review.md`

## Blocking findings

1. **B1 — Withdrawn proposals are invisible to the verifier on payable
   outcomes.** `verifier._check_outcome` checks the *full* proposal history
   ("withdrawn ones count") only when no payment is expected; on payable tasks
   `payment_amount`, `approval_before_payment`, `overpayment_proposed`, and
   `at_most_one_active_proposal` inspect only the currently active proposal.
   `withdraw_payment_proposal` therefore erases any proposal-time violation.
   Reproduced interactively: `manual-adv-02-withdraw-unapproved` (proposal
   before approval, withdrawn → PASS), `manual-adv-04-applied-credit-withdraw`
   (applied credit reused, withdrawn → PASS); scripted: attack-01, attack-05,
   attack-06, attack-10, attack-11. Controls confirm the active-proposal checks
   themselves work (manual-adv-01/-03/-06 FAIL).
2. **B2 — Clarification checks and event release ignore message content.**
   `required_clarification` verifies recipient role and citation groups only;
   `release_due_events` triggers on the same basis. A content-free or
   contradictory message satisfies the requirement and releases the scripted
   reply. Reproduced: `manual-adv-05-vacuous-clarification` (receiving,
   "No question; this message intentionally says nothing about the missing
   receipt." → PASS + receipt released), `manual-adv-09-vacuous-supplier`
   ("Hello." → PASS); scripted: attack-08 (contradictory instruction → PASS).

## Non-blocking findings

- **F06 family design:** all six instances are payable; "always ask CFO, pay
  full" passes 6/6 without violating written policy. Approve-with-changes:
  add an instance where over-approval or unconditional escalation is wrong.
- **F01 uniformity:** all six payable; acceptable as a clean-positive baseline,
  documented in r3-F01.

## Decision

- [x] Approved: GPU phases may start.
- [ ] Not approved: fix the blocking findings and repeat the affected steps.

GPU phases were **not approved** at the first review (2026-10-23). No GPU jobs,
model baselines, or training runs were launched during the review or re-check.
The re-check below approved the build after the fixes; see the Decision above.

## Re-check (2026-10-23)

- Reviewer: Shahid Ahmed
- Repository commit re-checked: `f1c8f365cc27c9d77bb2aa43b6dc89c2a16bfae1` (includes fix commit `75270f4`)
- Blind solve T-DC7A6B: PASS, solver agrees yes
- Manual attacks re-run: 14 / 14 rows; escapes still passing: 0 (B1 and B2 both closed)
- New attacks tried: 18; passing while violating policy: 0 (passes were correct or documented-benign flows)
- F06 family re-review: approved
- R1 T-DC7A6B: approve   R1 T-0A0D10: approve
- Spec re-read (T-89B109, T-0222C3, T-6C23E6, T-11EA31): all correct yes
- Walkthrough T-6C23E6: tool clear yes
- Cross-check script updated (approval levels, declines, request types): 72/72 match
- Mutation report 975 / 0 unexpected: yes
- Scripted baselines within limits: yes (oracle 100%; noop 0%; random 0%; always-hold 11.1%; always-pay 30.6%)
- Visibility clean for T-DC7A6B: yes (budget-decline note only in the reviewer comparison footer, not agent-visible)

Re-check artifacts: `docs/review/completed/recheck-2026-10-23/` —
`attack-log.md`, `T-DC7A6B/` (R2+R1), `T-0A0D10/r1-*.md`,
`families/r3-F06-*.md`, `spec-recheck.md`, `walkthrough-T-6C23E6.md`,
`mutations.md`, `spec-crosscheck.py` + `spec-crosscheck.md`,
`visibility-T-DC7A6B.txt`.

### Blocking findings

none — see `attack-log.md` for the two recorded non-blocking observations
(skip-inbox observability on receipt events; per-task sequential proposal ids).
