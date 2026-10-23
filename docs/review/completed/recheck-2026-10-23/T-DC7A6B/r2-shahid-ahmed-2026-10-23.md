# R2 Blind Solve

Do **not** open the task's `private.json`, run `invoiceops show-task --private`, or read the family or verifier code for this task before you finish this form.

- **Task ID:** T-DC7A6B
- **Task revision** (content hash shown by `invoiceops show-task`): `71052854965e`
- **Solver initials:** Shahid Ahmed
- **Role:** Independent solver
- **Date:** 2026-10-23
- **Run ID** (printed when you submit): `recheck-blind-T-DC7A6B`
- **I have not seen this task's expected outcome before solving:** Yes — the re-check guide described the new F06 variant 2 generically ("right approver declines"), but I had not seen this task's content or expected outcome.

## Steps taken

Fill in one row per tool call or decision. Keep reasons short.

| # | Tool or action | Why |
|---|---|---|
| 1 | search_records documents query=policy | Locate the effective policy |
| 2 | get_document DOC-240 | Read Hearthmoor policy v1 (eff. 2025-06-16) |
| 3 | get_invoice INV-41336 | 772 × $61.50 = $47,478.00, PO-4176, vendor VEN-HMD61 |
| 4 | get_purchase_order PO-4176 | Rev 1, 772 × $61.50 — exact match |
| 5 | get_receipts PO-4176 | GRN-307: 772 units received 2026-06-21 — full |
| 6 | get_vendor VEN-HMD61 | Verified; remit matches invoice (Lowfield ****5742) |
| 7 | get_history VEN-HMD61 | Prior invoice INV-41328 paid on a different PO — no duplicate |
| 8 | Decide: amount $47,478 > $20,000 self-limit → approval required; lowest covering approver is ap_manager ($75,000) | §8 approval routing |
| 9 | request_approval ap_manager, amount 4,747,800 | Required before proposing |
| 10 | check_inbox | Decision arrives: **Declined** — Joinery quarterly budget used; "do not pay until finance confirms funding; keep it on hold" |
| 11 | set_disposition on_hold / awaiting_approval | §8: if the right approver declines, do not pay |
| 12 | submit_case | Record the hold; no payment proposal |

## Final decision

- **Disposition you chose** (for example: proposed payment, on hold, needs clarification): on_hold / awaiting_approval
- **Amount proposed, if any:** none — no proposal created
- **Follow-up created, if any** (clarification or approval request, and to whom): approval request to `ap_manager` for $47,478.00 → declined
- **Evidence you relied on** (record IDs): INV-41336, PO-4176, GRN-307 (plus the decline message APR-001/APE-002)

## Experience

| Question | Answer |
|---|---|
| How confident are you that your outcome is correct? (1–5) | 5 |
| Was anything in the prompt unclear? | No |
| Was any information you needed missing or hard to find? | No — approver levels and the decline path are stated in §8 |
| Did any tool behave unexpectedly or return an error? | No — request_approval + check_inbox delivered the decision as documented |
| Did you consider another reasonable outcome? Which? | Paying after decline is not permitted by §8; holding is the only listed outcome. Escalating to controller/cfo would also be wrong — they are not "the approver at the right level". |
| Approximate time taken | ~10 min |

## After grading (fill in when the builder shares the result)

- **Verifier result:** Pass
- **Do you agree with the result?** Yes
- **If No, why:**
