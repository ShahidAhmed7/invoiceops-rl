# R2 Blind Solve

- **Task ID:** T-0222C3
- **Task revision:** 16b7213f35a5
- **Solver initials:** Shahid Ahmed
- **Role:** Independent solver; fictional-policy review, no AP practitioner certification
- **Date:** 2026-10-23 (Asia/Dhaka)
- **Run ID:** play-T-0222C3-2026-10-22T224203Z
- **I have not seen this task's expected outcome before solving:** Yes

## Steps taken

| # | Tool or action | Why |
|---|---|---|
| 1 | search_records documents policy | Locate policy |
| 2 | get_document DOC-400 (not found) | Incorrectly reused previous task ID; corrected from search |
| 3 | get_invoice INV-13675 | Read billed quantities and case version |
| 4 | get_document DOC-396 | Read this episode policy |
| 5 | get_vendor VEN-VMB51 | Verify supplier and bank |
| 6 | get_history VEN-VMB51 | Exclude duplicate and prior consumption |
| 7 | get_purchase_order PO-2288 | Verify authorized price and quantity |
| 8 | get_receipts PO-2288 | Aggregate 10+5 units received |
| 9 | set_disposition on_hold/short_receipt | Do not pay unreceived units |
| 10 | create_clarification supplier | Request corrected invoice with receipt evidence |
| 11 | submit_case | Report hold and zero proposal |

## Final decision

- **Disposition chosen:** on_hold / short_receipt
- **Amount proposed:** None; 0 cents
- **Follow-up created:** CLR-001 to supplier for corrected invoice
- **Evidence relied on:** INV-13675, PO-2288, GRN-224, GRN-225, DOC-396, VEN-VMB51

## Experience

| Question | Answer |
|---|---|
| Confidence (1–5) | 5 |
| Prompt unclear? | No; the policy determines the required workflow. |
| Missing or hard-to-find information? | None; all needed facts were available through public tools. |
| Unexpected tool behavior or errors? | One not_found from reusing DOC-400; searched ID DOC-396 worked. This was solver error, not missing evidence. |
| Other reasonable outcome considered? | Paying only 15 units considered and rejected: policy explicitly prohibits partial payment in this company. |
| Approximate time taken | Approximately 3 minutes |

## Pre-grade reasoning

20 × 12975 =259500 cents billed. Receipts total 10+5=15 units; shortage 5 ×12975 =64875 cents. No duplicate or bank mismatch. Policy requires supplier correction and short_receipt hold without any proposal.

This form, through the reasoning above, was saved before the grade command was invoked. No private task, family, or verifier source was read during the solve.

## After grading

```text
T-0222C3 attempt 0: PASS
```

- **Verifier result:** Pass.
- **Do you agree with the result?** Yes. The five-unit shortage requires a supplier correction and hold, with no proposal.
