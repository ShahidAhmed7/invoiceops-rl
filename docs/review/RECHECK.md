# Pre-GPU Re-check: Instructions for the Reviewer

## What this is

The first pre-GPU review ([`signoff/pre-gpu.md`](signoff/pre-gpu.md)) was **not approved**. It found two ways to cheat the grader (B1, B2) and one weak task family (F06). The builder has fixed all three; [`builder-response.md`](builder-response.md) explains how.

Your job is to confirm, independently, that the fixes work and broke nothing, then update the sign-off. This is a **targeted** re-check, not a full review. It takes about **2½–3 hours**. Give your honest verdict: if anything below still passes when it should fail, the re-check is not approved.

Don't fix anything yourself. Record what you find, and the builder makes the changes.

## What changed since you reviewed (commit `7066a8a` → `75270f4`)

1. **Payment history counts (fix for B1).** Only one payment proposal per invoice is allowed, ever. Withdrawing a proposal no longer erases it: a wrong proposal, or one made before approval, fails the task even if withdrawn. Retrying the *same* call with the *same* idempotency key after a `retryable` error is still fine; it doesn't create a second proposal.
2. **Clarifications are structured (fix for B2).** `create_clarification` no longer takes free text (`question` is gone). It takes a required `request_type`: `corrected_invoice`, `price_confirmation`, `receipt_confirmation`, or `bank_detail_verification`. The message sent is generated from the type and shown to you as `message_sent`. Scripted replies only arrive for the right recipient **and** the right request type, and the grader checks both.
3. **Approval levels (fix for F06).** Each approver approves only payments at their own level: the approver with the lowest limit that still covers the amount. Asking someone too senior or too junior gets a "Declined, route to …" reply. F06 variant 2 is new: the right approver declines for a budget reason, so the correct outcome is a hold with no payment.
4. **The policy text changed** to describe all of the above (sections 3, 4, 5, 8, 9, 11). That changes every task's revision hash.

## Rules

- **Blind solve first.** Step 1 is a blind solve of a task whose content is new. Do it before anything else, and do **not** run `show-family F06` or `show-task T-DC7A6B --private` until you have finished it.
- **Work from the current `main`.** Use commit `75270f4` or later, and write the commit hash in your forms.
- **Save everything** under `docs/review/completed/recheck-<YYYY-MM-DD>/` (create it). Don't edit your earlier review files; they are the record of the first review.
- **Run IDs:** give every session an ID with `--run-id`, for example `--run-id recheck-adv-02`. Grade it with `uv run invoiceops grade <run-id>`.

## Step 0: Setup (10 minutes)

```bash
git pull origin main
git log -1 --format=%H                 # write this hash down
uv sync --frozen --extra openenv
uv run pytest -q                       # must pass; if not, stop and report it
uv run invoiceops build-tasks --check  # must say "task files are up to date"
mkdir -p docs/review/completed/recheck-$(date +%F)
```

Re-read the current policy for one company before you start. Sections 4, 8 and 11 are the ones that changed:

```bash
uv run invoiceops play --task T-DC7A6B   # inside: search_records collection=documents query=policy
                                          # then:  get_document document_id=<the policy id>
                                          # then:  quit
```

That quick look is fine: it only shows what any agent sees. Don't look at that task's answer.

## Step 1: Blind solve of the new F06 task (30 minutes)

Task **`T-DC7A6B`** (dev split) was rebuilt for the F06 fix, so you haven't seen this version.

1. Copy [`templates/r2-blind-solve.md`](templates/r2-blind-solve.md) to `completed/recheck-<date>/T-DC7A6B/r2-<your-initials>-<date>.md`.
2. Run `uv run invoiceops play --task T-DC7A6B --run-id recheck-blind-T-DC7A6B`.
3. Solve it the way the policy requires. Use `help` and `tools` inside the session.
4. Fill in "Steps taken" and "Experience" **before** grading.
5. Run `uv run invoiceops grade recheck-blind-T-DC7A6B` and fill in "After grading".

If you believe your answer was right and the grade says FAIL (or the reverse), that's a blocking finding. Describe exactly why.

## Step 2: Re-run your 10 manual attacks (60–75 minutes)

Run each one in its own `invoiceops play` session and grade it. The table says what to do now and the result the fix should produce. Write each actual result in `completed/recheck-<date>/attack-log.md`, using the same format as your first attack log.

Command syntax inside `play` (either form works):

```text
propose_payment {"invoice_id": "INV-30638", "amount_minor": 6203700, "credit_note_ids": [], "evidence_ids": ["INV-30638"], "idempotency_key": "p1"}
create_clarification invoice_id=INV-24991 recipient_role=receiving request_type=receipt_confirmation evidence_ids=INV-24991,PO-1348 idempotency_key=c1
withdraw_payment_proposal proposal_id=PRP-001 reason=mistake
```

| # | Run ID | Task | What to do | Expected grade |
|---|---|---|---|---|
| 1 | `recheck-adv-01` | T-0A0D10 | Propose the payment **before** asking for approval and leave it active. Then finish normally. | FAIL: `approval_before_payment` |
| 2 | `recheck-adv-02` | T-0A0D10 | Propose before approval, **withdraw** it, then ask `ap_manager`, `check_inbox`, propose again, and submit. Your first review's escape. | **FAIL**: `at_most_one_proposal_ever`, critical `payment_without_required_approval` |
| 3 | `recheck-adv-03` | T-1A3136 | Propose using the credit note that was already applied to an earlier payment; leave it active. | FAIL: `payment_amount` |
| 4 | `recheck-adv-04` | T-1A3136 | Same wrong proposal, **withdraw** it, then propose the correct full amount and submit. Your first review's escape. | **FAIL**: critical `credit_note_misapplied`, `duplicate_payment_proposal` |
| 5a | `recheck-adv-05a` | T-6C23E6 | Try the old free-text call: `create_clarification {"invoice_id": "INV-24991", "recipient_role": "receiving", "question": "Hello.", "evidence_ids": ["INV-24991"], "idempotency_key": "c1"}`. | The **tool rejects it** with `invalid_arguments`, and no clarification is recorded. Then `quit`. |
| 5b | `recheck-adv-05b` | T-6C23E6 | Send `receiving` the **wrong** type (e.g. `request_type=corrected_invoice`), call `check_inbox`, then try to finish the case. | No reply and no receipt arrive. Grade **FAIL** |
| 5c | `recheck-adv-05c` | T-6C23E6 | Send `receiving` the **right** type (`receipt_confirmation`), `check_inbox`, then finish the case correctly. | The receipt arrives. Grade PASS (control) |
| 6 | `recheck-adv-06` | T-5B8D32 | First `propose_payment` returns `retryable`. Retry with a **different** idempotency key and leave both. | FAIL: `at_most_one_proposal_ever` |
| 6b | `recheck-adv-06b` | T-5B8D32 | Same as 6, but **withdraw** the first proposal before submitting. This is the old attack-10 escape. | **FAIL**: `at_most_one_proposal_ever` |
| 7 | `recheck-adv-07` | T-5B8D32 | After the `retryable` error, retry with the **same** key, then finish correctly. | PASS (control: same-key retry is allowed) |
| 8 | `recheck-adv-08` | T-6C23E6 | Send the clarification to a role that doesn't exist (e.g. `accounts_payable`), then pay. | FAIL |
| 9a | `recheck-adv-09a` | T-0222C3 | Hold the invoice for the short receipt, but send `supplier` the **wrong** type (e.g. `price_confirmation`). | **FAIL**: no `corrected_invoice` request to supplier |
| 9b | `recheck-adv-09b` | T-0222C3 | Same, but with `request_type=corrected_invoice`. | PASS (control) |
| 10 | `recheck-adv-10` | T-8F0E1E | Do everything correctly, but submit with `amount_proposed_minor: 1`. | FAIL: `submission_consistent` |

Then spend **at least 20 minutes on new attacks** against the fixes. Ideas:

- **Wrong approval level:** on `T-0A0D10`, ask `cfo` (too senior), propose anyway, and submit. It should FAIL. Then ask `controller`; it should be declined too.
- **Pay after a decline:** on `T-8E32C6` (train, the other new F06 task), ask the right approver, read the decline, and pay anyway. It should FAIL with `payment_proposed_for_unpayable_invoice`.
- **Withdraw the only proposal:** on any clean task, propose correctly, withdraw, and submit claiming it is paid. It should FAIL.
- **Clarification combinations:** the right type to the wrong role, a mismatched type plus the right type in one session, and so on. Check whether the grader still accepts the correct request when you also sent a harmless extra one. That's allowed.
- Anything else you can think of. **Every attack that passes while violating the written policy is blocking.**

Note: the 14 scripted attacks from your first review are already replayed automatically by `tests/test_review_regressions.py`. All 14 must fail, and Step 0's `pytest` run proves it. You don't need to redo them by hand.

## Step 3: Re-review F06 (30 minutes)

Do this only after Step 1.

1. Run `uv run invoiceops show-family F06`. There are six instances: two at the AP manager's level, two at the controller's level, and two "right approver declines" (`T-8E32C6`, `T-DC7A6B`).
2. Copy [`templates/r3-family-review.md`](templates/r3-family-review.md) to `completed/recheck-<date>/families/r3-F06-<initials>-<date>.md` and answer it. Key questions:
   - Does any fixed habit pass? Consider "always ask the CFO and pay in full", "always ask the AP manager", and "always hold". None should pass the family.
   - Is the "lowest limit that covers the amount" rule clearly stated in policy section 8?
   - Is the budget-decline message clear enough that a careful agent would hold, not pay?
3. R1 (spec review) for **`T-DC7A6B`**, now that you have solved it, and for **`T-0A0D10`**, whose approval rule changed. Use `show-task <id> --private` and save the forms in `completed/recheck-<date>/<task-id>/r1-<initials>-<date>.md`.

## Step 4: Re-read four sampled specs that use clarifications (20 minutes)

For each of **`T-89B109`**, **`T-0222C3`**, **`T-6C23E6`**, and **`T-11EA31`**:

1. Run `uv run invoiceops show-task <id> --private`.
2. Check that the required clarification now names a request type, and that it is the one the policy names for that situation:

   | Situation | Recipient | Request type |
   |---|---|---|
   | Price over tolerance | `procurement` | `price_confirmation` |
   | Short receipt (corrected invoice needed) | `supplier` | `corrected_invoice` |
   | Missing receipt | `receiving` | `receipt_confirmation` |
   | Bank details or unverified supplier | `vendor_master` | `bank_detail_verification` |

3. Check nothing else in the expected outcome changed from what you approved before. Record the new revision hash.

One short note per task is enough. Write all four in `completed/recheck-<date>/spec-recheck.md`.

## Step 5: Clarification walkthrough (15 minutes; not a blind solve)

You've already seen `T-6C23E6`'s answer, so this is a walkthrough, not a blind solve. The goal is to confirm the new clarification tool works naturally for a person:

```bash
uv run invoiceops play --task T-6C23E6 --run-id recheck-walkthrough-T-6C23E6
uv run invoiceops grade recheck-walkthrough-T-6C23E6
```

Answer in `completed/recheck-<date>/walkthrough-T-6C23E6.md`: Was it clear which `request_type` to use? Did `message_sent` say what you expected? Did the reply arrive through `check_inbox`?

## Step 6: Automated checks (15 minutes)

```bash
uv run invoiceops verify-mutations --report docs/review/completed/recheck-$(date +%F)/mutations.md
uv run invoiceops evaluate --agent all-scripted --split dev --split test
uv run invoiceops audit-visibility --task T-DC7A6B > docs/review/completed/recheck-$(date +%F)/visibility-T-DC7A6B.txt
```

Confirm, and note in your sign-off:

- [ ] The mutation report says **975 cases, 0 unexpected**: every mutation rejected, every alternative accepted. Open three of the new mutation kinds (`wrong_proposal_withdrawn_then_corrected`, `approval_from_wrong_level`, `clarification_wrong_request_type`) and check that the rejection reasons make sense.
- [ ] Scripted baselines: oracle 100%; no-op 0%; random 0%; always-hold ≤ 16.7%; always-pay ≤ 33.3% on each split.
- [ ] Visibility: the budget-decline note for `T-DC7A6B` does **not** appear in the visibility output. The agent should only see it after asking the approver.

## Step 7: Update the sign-off (15 minutes)

Edit `docs/review/signoff/pre-gpu.md`. **Keep everything already there**, and add this section at the end:

```markdown
## Re-check (YYYY-MM-DD)

- Reviewer:
- Repository commit re-checked:
- Blind solve T-DC7A6B: PASS/FAIL, solver agrees yes/no
- Manual attacks re-run: __ / 14 rows; escapes still passing: __ (list)
- New attacks tried: __; passing: __ (list)
- F06 family re-review: approved / approved with changes / rejected
- R1 T-DC7A6B: ___   R1 T-0A0D10: ___
- Spec re-read (T-89B109, T-0222C3, T-6C23E6, T-11EA31): all correct yes/no
- Walkthrough T-6C23E6: tool clear yes/no
- Mutation report 975 / 0 unexpected: yes/no
- Scripted baselines within limits: yes/no
- Visibility clean for T-DC7A6B: yes/no

### Blocking findings
(list, or "none")
```

Then update the **Decision** at the end of the file:

- If there are **no blocking findings**, tick `- [x] Approved: GPU phases may start.` and untick `- [ ] Not approved…`. The GPU launcher reads exactly this line, so keep the wording `Approved` after the box.
- Otherwise, leave it **Not approved** and list what's still wrong.

**What counts as blocking:**
- any attack that passes while breaking the written policy;
- the blind solve disagreeing with the grade when you were right;
- a fixed habit that passes F06;
- a wrong request type in any of the four specs;
- a mutation report with unexpected results;
- the decline note being visible before the approval request.

## Step 8: Commit and push

```bash
git add docs/review/completed/recheck-* docs/review/signoff/pre-gpu.md
git commit -m "Pre-GPU re-check: <Approved | Not approved>"
git push origin main
```

Then tell the builder the result. If it's approved, the GPU phases can start, following [`../MODAL_RUNBOOK.md`](../MODAL_RUNBOOK.md).
