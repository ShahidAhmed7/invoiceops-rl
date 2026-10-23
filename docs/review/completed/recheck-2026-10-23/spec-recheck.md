# Spec re-read — clarification tasks (re-check)

Reviewer: Shahid Ahmed · Date: 2026-10-23 · Commit: `f1c8f365cc27c9d77bb2aa43b6dc89c2a16bfae1`
Method: `invoiceops show-task <id>` (revision) + read `private.json` expectations; compared
recipient/request_type against the policy table and the outcome against the first review.

| Task | New revision | Required clarification | Matches policy | Outcome unchanged |
|---|---|---|---|---|
| T-89B109 | `a54acafc7043` | `procurement` / `price_confirmation`, cites INV-66433 + PO-1793 | Yes — price over tolerance | Yes — `on_hold/price_variance`, no payment |
| T-0222C3 | `3eaf8a950dc5` | `supplier` / `corrected_invoice`, cites INV-13675 + one of GRN-224/GRN-225/PO-2288 | Yes — short receipt needing corrected invoice | Yes — `on_hold/short_receipt`, no payment |
| T-6C23E6 | `81a6674f7cad` | `receiving` / `receipt_confirmation`, cites INV-24991 + PO-1348 | Yes — missing receipt | Yes — `ready_for_payment/matched`, $4,921.20 |
| T-11EA31 | `ac9a14526e39` | `supplier` / `corrected_invoice`, cites INV-23154 + one of GRN-407/PO-4395 | Yes — short receipt needing corrected invoice | Yes — `on_hold/short_receipt`, no payment |

Notes:

- Each `required_clarification` now carries `request_types` and they match the policy-named type
  for each situation. No wrong request type in any of the four specs.
- T-89B109's invoice/PO ids changed with the rebuild (INV-66433/PO-1793, still the same
  price-over-tolerance situation: invoice $2,553.37 vs PO $2,461.70 > tolerance).
- Nothing else in the four expected outcomes differs from what the first review approved.
