# Clarification walkthrough — T-6C23E6 (re-check)

Reviewer: Shahid Ahmed · Date: 2026-10-23 · Run: `recheck-walkthrough-T-6C23E6` · Grade: **PASS**

## Questions

- **Was it clear which `request_type` to use?** Yes. `create_clarification`'s schema describes each
  type in one line, and policy §5 names `receipt_confirmation` for a missing receipt. The tool
  also rejects unknown roles and unknown types with clear `invalid_arguments` messages.
- **Did `message_sent` say what you expected?** Yes — it returned the generated message
  "Please confirm what has been received for INV-24991 and record the goods receipt.", which is
  exactly the request §5 requires (confirm and record the receipt). No way to inject free text.
- **Did the reply arrive through `check_inbox`?** Yes — one call after the clarification returned
  the scripted reply "Found it: the delivery for PO-1348 was booked late. Receipt GRN-176 is now
  recorded.", and `get_receipts` then showed GRN-176 (18 units).

## Notes

The flow feels natural for a person: pick the type the policy names, cite the invoice + PO,
check the inbox, then finish. The old free-text path is gone — `question` is a schema error —
so the B2 gap (content-free clarifications) is closed at the tool level, not only at grading.
