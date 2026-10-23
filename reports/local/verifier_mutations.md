# Verifier mutation report

979 cases on 72 tasks; 0 unexpected results.

| Task | Kind | Case | Expected | Result | Verifier reason |
|---|---|---|---|---|---|
| T-D2DA12 | alternative | oracle | accepted | **accepted** | accepted |
| T-D2DA12 | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-D2DA12 | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/144000 but state is open/None/0); disposition (case is open/None; expected ready_for_ |
| T-D2DA12 | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/144000 but state is open/None/0); disposition (case is open/None; expected ready_for_ |
| T-D2DA12 | mutation | amount_off_by_one_cent | rejected | **rejected** | rejected: payment_amount (proposed 144001 with credits []; expected 144000 with credits []) |
| T-D2DA12 | mutation | duplicate_proposal | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (2 active, 0 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-D2DA12 | mutation | paid_but_marked_on_hold | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/144000 but state is on_hold/price_variance/144000); disposition (case is on_hold/pric |
| T-D2DA12 | mutation | wrong_proposal_withdrawn_then_corrected | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (1 active, 1 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-D2DA12 | mutation | only_proposal_withdrawn | rejected | **rejected** | rejected: payment_amount (1 proposal(s) ever, 0 active; expected exactly one proposal, still active) |
| T-D2DA12 | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-55023) |
| T-D2DA12 | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/144000 but state is ready_for_payment/matched/144000) |
| T-D2DA12 | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-55023) |
| T-D2DA12 | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-C94302 | alternative | oracle | accepted | **accepted** | accepted |
| T-C94302 | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-C94302 | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/short_receipt/0 but state is open/None/0); disposition (case is open/None; expected on_hold/short_recei |
| T-C94302 | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/short_receipt/0 but state is open/None/0); disposition (case is open/None; expected on_hold/short_recei |
| T-C94302 | mutation | missing_followups | rejected | **rejected** | rejected: clarification_to_supplier (no corrected_invoice request sent to supplier) |
| T-C94302 | mutation | forbidden_payment | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/short_receipt/0 but state is on_hold/short_receipt/1200000); no_payment_proposed (1 payment proposal(s) |
| T-C94302 | mutation | forbidden_payment_withdrawn | rejected | **rejected** | rejected: no_payment_proposed (1 payment proposal(s) were created (withdrawn ones count)) |
| T-C94302 | mutation | hold_flipped_to_ready | rejected | **rejected** | rejected: disposition (case is ready_for_payment/matched; expected on_hold/short_receipt) |
| T-C94302 | mutation | clarification_wrong_request_type | rejected | **rejected** | rejected: clarification_to_supplier (no corrected_invoice request sent to supplier) |
| T-C94302 | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-8807) |
| T-C94302 | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/0 but state is on_hold/short_receipt/0) |
| T-C94302 | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-8807) |
| T-C94302 | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-A50BE6 | alternative | oracle | accepted | **accepted** | accepted |
| T-A50BE6 | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-A50BE6 | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched_with_credit/462000 but state is open/None/0); disposition (case is open/None; expecte |
| T-A50BE6 | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched_with_credit/462000 but state is open/None/0); disposition (case is open/None; expecte |
| T-A50BE6 | mutation | amount_off_by_one_cent | rejected | **rejected** | rejected: payment_amount (proposed 462001 with credits ['CN-573']; expected 462000 with credits ['CN-573']) |
| T-A50BE6 | mutation | duplicate_proposal | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (2 active, 0 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-A50BE6 | mutation | paid_but_marked_on_hold | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched_with_credit/462000 but state is on_hold/price_variance/462000); disposition (case is  |
| T-A50BE6 | mutation | credit_not_applied | rejected | **rejected** | rejected: payment_amount (proposed 528000 with credits []; expected 462000 with credits ['CN-573']) |
| T-A50BE6 | mutation | wrong_proposal_withdrawn_then_corrected | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (1 active, 1 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-A50BE6 | mutation | only_proposal_withdrawn | rejected | **rejected** | rejected: payment_amount (1 proposal(s) ever, 0 active; expected exactly one proposal, still active) |
| T-A50BE6 | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-21541) |
| T-A50BE6 | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/462000 but state is ready_for_payment/matched_with_credit/462000) |
| T-A50BE6 | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-21541) |
| T-A50BE6 | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-4F837F | alternative | oracle | accepted | **accepted** | accepted |
| T-4F837F | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-4F837F | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/vendor_verification/0 but state is open/None/0); disposition (case is open/None; expected on_hold/vendo |
| T-4F837F | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/vendor_verification/0 but state is open/None/0); disposition (case is open/None; expected on_hold/vendo |
| T-4F837F | mutation | missing_followups | rejected | **rejected** | rejected: clarification_to_vendor_master (no bank_detail_verification request sent to vendor_master) |
| T-4F837F | mutation | forbidden_payment | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/vendor_verification/0 but state is on_hold/vendor_verification/479700); no_payment_proposed (1 payment  |
| T-4F837F | mutation | forbidden_payment_withdrawn | rejected | **rejected** | rejected: no_payment_proposed (1 payment proposal(s) were created (withdrawn ones count)) |
| T-4F837F | mutation | hold_flipped_to_ready | rejected | **rejected** | rejected: disposition (case is ready_for_payment/matched; expected on_hold/vendor_verification) |
| T-4F837F | mutation | clarification_wrong_request_type | rejected | **rejected** | rejected: clarification_to_vendor_master (no bank_detail_verification request sent to vendor_master) |
| T-4F837F | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-64709) |
| T-4F837F | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/0 but state is on_hold/vendor_verification/0) |
| T-4F837F | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-64709) |
| T-4F837F | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-5E46C3 | alternative | oracle | accepted | **accepted** | accepted |
| T-5E46C3 | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-5E46C3 | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/175920 but state is open/None/0); disposition (case is open/None; expected ready_for_ |
| T-5E46C3 | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/175920 but state is open/None/0); disposition (case is open/None; expected ready_for_ |
| T-5E46C3 | mutation | amount_off_by_one_cent | rejected | **rejected** | rejected: payment_amount (proposed 175921 with credits []; expected 175920 with credits []) |
| T-5E46C3 | mutation | duplicate_proposal | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (2 active, 0 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-5E46C3 | mutation | paid_but_marked_on_hold | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/175920 but state is on_hold/price_variance/175920); disposition (case is on_hold/pric |
| T-5E46C3 | mutation | wrong_proposal_withdrawn_then_corrected | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (1 active, 1 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-5E46C3 | mutation | only_proposal_withdrawn | rejected | **rejected** | rejected: payment_amount (1 proposal(s) ever, 0 active; expected exactly one proposal, still active) |
| T-5E46C3 | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-54662) |
| T-5E46C3 | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/175920 but state is ready_for_payment/matched/175920) |
| T-5E46C3 | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-54662) |
| T-5E46C3 | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-E4FDD8 | alternative | oracle | accepted | **accepted** | accepted |
| T-E4FDD8 | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-E4FDD8 | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/278980 but state is open/None/0); disposition (case is open/None; expected ready_for_ |
| T-E4FDD8 | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/278980 but state is open/None/0); disposition (case is open/None; expected ready_for_ |
| T-E4FDD8 | mutation | amount_off_by_one_cent | rejected | **rejected** | rejected: payment_amount (proposed 278981 with credits []; expected 278980 with credits []) |
| T-E4FDD8 | mutation | duplicate_proposal | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (2 active, 0 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-E4FDD8 | mutation | paid_but_marked_on_hold | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/278980 but state is on_hold/price_variance/278980); disposition (case is on_hold/pric |
| T-E4FDD8 | mutation | wrong_proposal_withdrawn_then_corrected | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (1 active, 1 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-E4FDD8 | mutation | only_proposal_withdrawn | rejected | **rejected** | rejected: payment_amount (1 proposal(s) ever, 0 active; expected exactly one proposal, still active) |
| T-E4FDD8 | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-57948) |
| T-E4FDD8 | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/278980 but state is ready_for_payment/matched/278980) |
| T-E4FDD8 | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-57948) |
| T-E4FDD8 | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-B97FAB | alternative | oracle | accepted | **accepted** | accepted |
| T-B97FAB | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-B97FAB | alternative | alternative_reason_matched | accepted | **accepted** | accepted |
| T-B97FAB | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched_within_tolerance/375144 but state is open/None/0); disposition (case is open/None; ex |
| T-B97FAB | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched_within_tolerance/375144 but state is open/None/0); disposition (case is open/None; ex |
| T-B97FAB | mutation | amount_off_by_one_cent | rejected | **rejected** | rejected: payment_amount (proposed 375145 with credits []; expected 375144 with credits []) |
| T-B97FAB | mutation | duplicate_proposal | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (2 active, 0 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-B97FAB | mutation | paid_but_marked_on_hold | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched_within_tolerance/375144 but state is on_hold/price_variance/375144); disposition (cas |
| T-B97FAB | mutation | wrong_proposal_withdrawn_then_corrected | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (1 active, 1 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-B97FAB | mutation | only_proposal_withdrawn | rejected | **rejected** | rejected: payment_amount (1 proposal(s) ever, 0 active; expected exactly one proposal, still active) |
| T-B97FAB | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-73466) |
| T-B97FAB | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/375144 but state is ready_for_payment/matched_within_tolerance/375144) |
| T-B97FAB | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-73466) |
| T-B97FAB | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-5E2670 | alternative | oracle | accepted | **accepted** | accepted |
| T-5E2670 | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-5E2670 | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/0 but state is open/None/0); disposition (case is open/None; expected rejected/dupli |
| T-5E2670 | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/0 but state is open/None/0); disposition (case is open/None; expected rejected/dupli |
| T-5E2670 | mutation | forbidden_payment | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/0 but state is rejected/duplicate_invoice/517650); no_payment_proposed (1 payment pr |
| T-5E2670 | mutation | forbidden_payment_withdrawn | rejected | **rejected** | rejected: no_payment_proposed (1 payment proposal(s) were created (withdrawn ones count)) |
| T-5E2670 | mutation | hold_flipped_to_ready | rejected | **rejected** | rejected: disposition (case is ready_for_payment/matched; expected rejected/duplicate_invoice) |
| T-5E2670 | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-61469) |
| T-5E2670 | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/price_variance/0 but state is rejected/duplicate_invoice/0) |
| T-5E2670 | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-61470) |
| T-5E2670 | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-8979C8 | alternative | oracle | accepted | **accepted** | accepted |
| T-8979C8 | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-8979C8 | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/1999200 but state is open/None/0); disposition (case is open/None; expected ready_for |
| T-8979C8 | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/1999200 but state is open/None/0); disposition (case is open/None; expected ready_for |
| T-8979C8 | mutation | missing_followups | rejected | **rejected** | rejected: approval_before_payment (a payment proposal (active or withdrawn) was created without a sufficient prior approval) |
| T-8979C8 | mutation | amount_off_by_one_cent | rejected | **rejected** | rejected: payment_amount (proposed 1999201 with credits []; expected 1999200 with credits []); approval_before_payment (a payment proposal (active or withdrawn) |
| T-8979C8 | mutation | duplicate_proposal | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (2 active, 0 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-8979C8 | mutation | approval_after_payment | rejected | **rejected** | rejected: approval_before_payment (a payment proposal (active or withdrawn) was created without a sufficient prior approval) |
| T-8979C8 | mutation | paid_but_marked_on_hold | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/1999200 but state is on_hold/price_variance/1999200); disposition (case is on_hold/pr |
| T-8979C8 | mutation | wrong_proposal_withdrawn_then_corrected | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (1 active, 1 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-8979C8 | mutation | only_proposal_withdrawn | rejected | **rejected** | rejected: payment_amount (1 proposal(s) ever, 0 active; expected exactly one proposal, still active) |
| T-8979C8 | mutation | proposal_before_approval_withdrawn | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (1 active, 1 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-8979C8 | mutation | approval_from_wrong_level | rejected | **rejected** | rejected: approval_before_payment (a payment proposal (active or withdrawn) was created without a sufficient prior approval) |
| T-8979C8 | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-48842) |
| T-8979C8 | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/1999200 but state is ready_for_payment/matched/1999200) |
| T-8979C8 | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-48842) |
| T-8979C8 | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-80BC88 | alternative | oracle | accepted | **accepted** | accepted |
| T-80BC88 | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-80BC88 | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/428400 but state is open/None/0); disposition (case is open/None; expected ready_for_ |
| T-80BC88 | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/428400 but state is open/None/0); disposition (case is open/None; expected ready_for_ |
| T-80BC88 | mutation | missing_followups | rejected | **rejected** | rejected: receipt_recorded_before_decision (the case was decided or paid before the requested receipt was received through check_inbox); clarification_to_receiv |
| T-80BC88 | mutation | amount_off_by_one_cent | rejected | **rejected** | rejected: payment_amount (proposed 428401 with credits []; expected 428400 with credits []) |
| T-80BC88 | mutation | duplicate_proposal | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (2 active, 0 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-80BC88 | mutation | paid_but_marked_on_hold | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/428400 but state is on_hold/price_variance/428400); disposition (case is on_hold/pric |
| T-80BC88 | mutation | wrong_proposal_withdrawn_then_corrected | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (1 active, 1 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-80BC88 | mutation | only_proposal_withdrawn | rejected | **rejected** | rejected: payment_amount (1 proposal(s) ever, 0 active; expected exactly one proposal, still active) |
| T-80BC88 | mutation | clarification_wrong_request_type | rejected | **rejected** | rejected: receipt_recorded_before_decision (the case was decided or paid before the requested receipt was received through check_inbox); clarification_to_receiv |
| T-80BC88 | mutation | decided_without_reading_reply | rejected | **rejected** | rejected: receipt_recorded_before_decision (the case was decided or paid before the requested receipt was received through check_inbox) |
| T-80BC88 | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-46822) |
| T-80BC88 | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/428400 but state is ready_for_payment/matched/428400) |
| T-80BC88 | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-46822) |
| T-80BC88 | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-201937 | alternative | oracle | accepted | **accepted** | accepted |
| T-201937 | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-201937 | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/479220 but state is open/None/0); disposition (case is open/None; expected ready_for_ |
| T-201937 | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/479220 but state is open/None/0); disposition (case is open/None; expected ready_for_ |
| T-201937 | mutation | amount_off_by_one_cent | rejected | **rejected** | rejected: payment_amount (proposed 479221 with credits []; expected 479220 with credits []) |
| T-201937 | mutation | duplicate_proposal | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (2 active, 0 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-201937 | mutation | paid_but_marked_on_hold | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/479220 but state is on_hold/price_variance/479220); disposition (case is on_hold/pric |
| T-201937 | mutation | wrong_proposal_withdrawn_then_corrected | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (1 active, 1 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-201937 | mutation | only_proposal_withdrawn | rejected | **rejected** | rejected: payment_amount (1 proposal(s) ever, 0 active; expected exactly one proposal, still active) |
| T-201937 | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-47490) |
| T-201937 | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/479220 but state is ready_for_payment/matched/479220) |
| T-201937 | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-47490) |
| T-201937 | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-02FF9D | alternative | oracle | accepted | **accepted** | accepted |
| T-02FF9D | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-02FF9D | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/price_variance/0 but state is open/None/0); disposition (case is open/None; expected on_hold/price_vari |
| T-02FF9D | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/price_variance/0 but state is open/None/0); disposition (case is open/None; expected on_hold/price_vari |
| T-02FF9D | mutation | missing_followups | rejected | **rejected** | rejected: clarification_to_procurement (no price_confirmation request sent to procurement) |
| T-02FF9D | mutation | forbidden_payment | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/price_variance/0 but state is on_hold/price_variance/451136); no_payment_proposed (1 payment proposal(s |
| T-02FF9D | mutation | forbidden_payment_withdrawn | rejected | **rejected** | rejected: no_payment_proposed (1 payment proposal(s) were created (withdrawn ones count)) |
| T-02FF9D | mutation | hold_flipped_to_ready | rejected | **rejected** | rejected: disposition (case is ready_for_payment/matched; expected on_hold/price_variance) |
| T-02FF9D | mutation | clarification_wrong_request_type | rejected | **rejected** | rejected: clarification_to_procurement (no price_confirmation request sent to procurement) |
| T-02FF9D | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-73260) |
| T-02FF9D | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/0 but state is on_hold/price_variance/0) |
| T-02FF9D | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-73260) |
| T-02FF9D | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-BE5CAB | alternative | oracle | accepted | **accepted** | accepted |
| T-BE5CAB | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-BE5CAB | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/238660 but state is open/None/0); disposition (case is open/None; expected ready_for_ |
| T-BE5CAB | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/238660 but state is open/None/0); disposition (case is open/None; expected ready_for_ |
| T-BE5CAB | mutation | amount_off_by_one_cent | rejected | **rejected** | rejected: payment_amount (proposed 238661 with credits []; expected 238660 with credits []) |
| T-BE5CAB | mutation | duplicate_proposal | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (2 active, 0 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-BE5CAB | mutation | paid_but_marked_on_hold | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/238660 but state is on_hold/price_variance/238660); disposition (case is on_hold/pric |
| T-BE5CAB | mutation | wrong_proposal_withdrawn_then_corrected | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (1 active, 1 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-BE5CAB | mutation | only_proposal_withdrawn | rejected | **rejected** | rejected: payment_amount (1 proposal(s) ever, 0 active; expected exactly one proposal, still active) |
| T-BE5CAB | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-14507) |
| T-BE5CAB | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/238660 but state is ready_for_payment/matched/238660) |
| T-BE5CAB | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-14507) |
| T-BE5CAB | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-8B3FCC | alternative | oracle | accepted | **accepted** | accepted |
| T-8B3FCC | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-8B3FCC | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/short_receipt/0 but state is open/None/0); disposition (case is open/None; expected on_hold/short_recei |
| T-8B3FCC | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/short_receipt/0 but state is open/None/0); disposition (case is open/None; expected on_hold/short_recei |
| T-8B3FCC | mutation | missing_followups | rejected | **rejected** | rejected: clarification_to_supplier (no corrected_invoice request sent to supplier) |
| T-8B3FCC | mutation | forbidden_payment | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/short_receipt/0 but state is on_hold/short_receipt/359540); no_payment_proposed (1 payment proposal(s)  |
| T-8B3FCC | mutation | forbidden_payment_withdrawn | rejected | **rejected** | rejected: no_payment_proposed (1 payment proposal(s) were created (withdrawn ones count)) |
| T-8B3FCC | mutation | hold_flipped_to_ready | rejected | **rejected** | rejected: disposition (case is ready_for_payment/matched; expected on_hold/short_receipt) |
| T-8B3FCC | mutation | clarification_wrong_request_type | rejected | **rejected** | rejected: clarification_to_supplier (no corrected_invoice request sent to supplier) |
| T-8B3FCC | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-55331) |
| T-8B3FCC | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/0 but state is on_hold/short_receipt/0) |
| T-8B3FCC | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-55331) |
| T-8B3FCC | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-1D6F14 | alternative | oracle | accepted | **accepted** | accepted |
| T-1D6F14 | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-1D6F14 | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/269025 but state is open/None/0); disposition (case is open/None; expected ready_for_ |
| T-1D6F14 | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/269025 but state is open/None/0); disposition (case is open/None; expected ready_for_ |
| T-1D6F14 | mutation | amount_off_by_one_cent | rejected | **rejected** | rejected: payment_amount (proposed 269026 with credits []; expected 269025 with credits []) |
| T-1D6F14 | mutation | duplicate_proposal | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (2 active, 0 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-1D6F14 | mutation | paid_but_marked_on_hold | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/269025 but state is on_hold/price_variance/269025); disposition (case is on_hold/pric |
| T-1D6F14 | mutation | wrong_proposal_withdrawn_then_corrected | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (1 active, 1 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-1D6F14 | mutation | only_proposal_withdrawn | rejected | **rejected** | rejected: payment_amount (1 proposal(s) ever, 0 active; expected exactly one proposal, still active) |
| T-1D6F14 | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-58844) |
| T-1D6F14 | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/269025 but state is ready_for_payment/matched/269025) |
| T-1D6F14 | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-58844) |
| T-1D6F14 | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-EFC9FB | alternative | oracle | accepted | **accepted** | accepted |
| T-EFC9FB | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-EFC9FB | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/vendor_verification/0 but state is open/None/0); disposition (case is open/None; expected on_hold/vendo |
| T-EFC9FB | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/vendor_verification/0 but state is open/None/0); disposition (case is open/None; expected on_hold/vendo |
| T-EFC9FB | mutation | missing_followups | rejected | **rejected** | rejected: clarification_to_vendor_master (no bank_detail_verification request sent to vendor_master) |
| T-EFC9FB | mutation | forbidden_payment | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/vendor_verification/0 but state is on_hold/vendor_verification/172400); no_payment_proposed (1 payment  |
| T-EFC9FB | mutation | forbidden_payment_withdrawn | rejected | **rejected** | rejected: no_payment_proposed (1 payment proposal(s) were created (withdrawn ones count)) |
| T-EFC9FB | mutation | hold_flipped_to_ready | rejected | **rejected** | rejected: disposition (case is ready_for_payment/matched; expected on_hold/vendor_verification) |
| T-EFC9FB | mutation | clarification_wrong_request_type | rejected | **rejected** | rejected: clarification_to_vendor_master (no bank_detail_verification request sent to vendor_master) |
| T-EFC9FB | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-41871) |
| T-EFC9FB | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/0 but state is on_hold/vendor_verification/0) |
| T-EFC9FB | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-41871) |
| T-EFC9FB | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-F3AD7D | alternative | oracle | accepted | **accepted** | accepted |
| T-F3AD7D | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-F3AD7D | alternative | alternative_reason_short_receipt | accepted | **accepted** | accepted |
| T-F3AD7D | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/quantity_exceeds_receipt/0 but state is open/None/0); disposition (case is open/None; expected on_hold/ |
| T-F3AD7D | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/quantity_exceeds_receipt/0 but state is open/None/0); disposition (case is open/None; expected on_hold/ |
| T-F3AD7D | mutation | missing_followups | rejected | **rejected** | rejected: clarification_to_supplier (no corrected_invoice request sent to supplier) |
| T-F3AD7D | mutation | forbidden_payment | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/quantity_exceeds_receipt/0 but state is on_hold/quantity_exceeds_receipt/282000); no_payment_proposed ( |
| T-F3AD7D | mutation | forbidden_payment_withdrawn | rejected | **rejected** | rejected: no_payment_proposed (1 payment proposal(s) were created (withdrawn ones count)) |
| T-F3AD7D | mutation | hold_flipped_to_ready | rejected | **rejected** | rejected: disposition (case is ready_for_payment/matched; expected on_hold/quantity_exceeds_receipt or short_receipt) |
| T-F3AD7D | mutation | clarification_wrong_request_type | rejected | **rejected** | rejected: clarification_to_supplier (no corrected_invoice request sent to supplier) |
| T-F3AD7D | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-19195) |
| T-F3AD7D | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/0 but state is on_hold/quantity_exceeds_receipt/0) |
| T-F3AD7D | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-19195) |
| T-F3AD7D | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-CFE072 | alternative | oracle | accepted | **accepted** | accepted |
| T-CFE072 | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-CFE072 | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched_with_credit/261400 but state is open/None/0); disposition (case is open/None; expecte |
| T-CFE072 | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched_with_credit/261400 but state is open/None/0); disposition (case is open/None; expecte |
| T-CFE072 | mutation | amount_off_by_one_cent | rejected | **rejected** | rejected: payment_amount (proposed 261401 with credits ['CN-152']; expected 261400 with credits ['CN-152']) |
| T-CFE072 | mutation | duplicate_proposal | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (2 active, 0 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-CFE072 | mutation | paid_but_marked_on_hold | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched_with_credit/261400 but state is on_hold/price_variance/261400); disposition (case is  |
| T-CFE072 | mutation | credit_not_applied | rejected | **rejected** | rejected: payment_amount (proposed 290400 with credits []; expected 261400 with credits ['CN-152']) |
| T-CFE072 | mutation | wrong_proposal_withdrawn_then_corrected | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (1 active, 1 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-CFE072 | mutation | only_proposal_withdrawn | rejected | **rejected** | rejected: payment_amount (1 proposal(s) ever, 0 active; expected exactly one proposal, still active) |
| T-CFE072 | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-39371) |
| T-CFE072 | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/261400 but state is ready_for_payment/matched_with_credit/261400) |
| T-CFE072 | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-39371) |
| T-CFE072 | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-25DE39 | alternative | oracle | accepted | **accepted** | accepted |
| T-25DE39 | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-25DE39 | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/price_variance/0 but state is open/None/0); disposition (case is open/None; expected on_hold/price_vari |
| T-25DE39 | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/price_variance/0 but state is open/None/0); disposition (case is open/None; expected on_hold/price_vari |
| T-25DE39 | mutation | missing_followups | rejected | **rejected** | rejected: clarification_to_procurement (no price_confirmation request sent to procurement) |
| T-25DE39 | mutation | forbidden_payment | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/price_variance/0 but state is on_hold/price_variance/248115); no_payment_proposed (1 payment proposal(s |
| T-25DE39 | mutation | forbidden_payment_withdrawn | rejected | **rejected** | rejected: no_payment_proposed (1 payment proposal(s) were created (withdrawn ones count)) |
| T-25DE39 | mutation | hold_flipped_to_ready | rejected | **rejected** | rejected: disposition (case is ready_for_payment/matched; expected on_hold/price_variance) |
| T-25DE39 | mutation | clarification_wrong_request_type | rejected | **rejected** | rejected: clarification_to_procurement (no price_confirmation request sent to procurement) |
| T-25DE39 | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-58982) |
| T-25DE39 | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/0 but state is on_hold/price_variance/0) |
| T-25DE39 | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-58982) |
| T-25DE39 | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-FBECFF | alternative | oracle | accepted | **accepted** | accepted |
| T-FBECFF | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-FBECFF | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/0 but state is open/None/0); disposition (case is open/None; expected rejected/dupli |
| T-FBECFF | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/0 but state is open/None/0); disposition (case is open/None; expected rejected/dupli |
| T-FBECFF | mutation | forbidden_payment | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/0 but state is rejected/duplicate_invoice/383040); no_payment_proposed (1 payment pr |
| T-FBECFF | mutation | forbidden_payment_withdrawn | rejected | **rejected** | rejected: no_payment_proposed (1 payment proposal(s) were created (withdrawn ones count)) |
| T-FBECFF | mutation | hold_flipped_to_ready | rejected | **rejected** | rejected: disposition (case is ready_for_payment/matched; expected rejected/duplicate_invoice) |
| T-FBECFF | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-22006) |
| T-FBECFF | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/price_variance/0 but state is rejected/duplicate_invoice/0) |
| T-FBECFF | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-22013) |
| T-FBECFF | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-2D6100 | alternative | oracle | accepted | **accepted** | accepted |
| T-2D6100 | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-2D6100 | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/11992500 but state is open/None/0); disposition (case is open/None; expected ready_fo |
| T-2D6100 | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/11992500 but state is open/None/0); disposition (case is open/None; expected ready_fo |
| T-2D6100 | mutation | missing_followups | rejected | **rejected** | rejected: approval_before_payment (a payment proposal (active or withdrawn) was created without a sufficient prior approval) |
| T-2D6100 | mutation | amount_off_by_one_cent | rejected | **rejected** | rejected: payment_amount (proposed 11992501 with credits []; expected 11992500 with credits []); approval_before_payment (a payment proposal (active or withdraw |
| T-2D6100 | mutation | duplicate_proposal | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (2 active, 0 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-2D6100 | mutation | approval_after_payment | rejected | **rejected** | rejected: approval_before_payment (a payment proposal (active or withdrawn) was created without a sufficient prior approval) |
| T-2D6100 | mutation | paid_but_marked_on_hold | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/11992500 but state is on_hold/price_variance/11992500); disposition (case is on_hold/ |
| T-2D6100 | mutation | wrong_proposal_withdrawn_then_corrected | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (1 active, 1 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-2D6100 | mutation | only_proposal_withdrawn | rejected | **rejected** | rejected: payment_amount (1 proposal(s) ever, 0 active; expected exactly one proposal, still active) |
| T-2D6100 | mutation | proposal_before_approval_withdrawn | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (1 active, 1 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-2D6100 | mutation | approval_from_wrong_level | rejected | **rejected** | rejected: approval_before_payment (a payment proposal (active or withdrawn) was created without a sufficient prior approval) |
| T-2D6100 | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-14065) |
| T-2D6100 | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/11992500 but state is ready_for_payment/matched/11992500) |
| T-2D6100 | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-14065) |
| T-2D6100 | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-1F835F | alternative | oracle | accepted | **accepted** | accepted |
| T-1F835F | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-1F835F | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/partial_receipt_paid/282720 but state is open/None/0); disposition (case is open/None; expect |
| T-1F835F | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/partial_receipt_paid/282720 but state is open/None/0); disposition (case is open/None; expect |
| T-1F835F | mutation | missing_followups | rejected | **rejected** | rejected: receipt_recorded_before_decision (the case was decided or paid before the requested receipt was received through check_inbox); clarification_to_receiv |
| T-1F835F | mutation | amount_off_by_one_cent | rejected | **rejected** | rejected: payment_amount (proposed 282721 with credits []; expected 282720 with credits []) |
| T-1F835F | mutation | duplicate_proposal | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (2 active, 0 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-1F835F | mutation | paid_but_marked_on_hold | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/partial_receipt_paid/282720 but state is on_hold/price_variance/282720); disposition (case is |
| T-1F835F | mutation | wrong_proposal_withdrawn_then_corrected | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (1 active, 1 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-1F835F | mutation | only_proposal_withdrawn | rejected | **rejected** | rejected: payment_amount (1 proposal(s) ever, 0 active; expected exactly one proposal, still active) |
| T-1F835F | mutation | clarification_wrong_request_type | rejected | **rejected** | rejected: receipt_recorded_before_decision (the case was decided or paid before the requested receipt was received through check_inbox); clarification_to_receiv |
| T-1F835F | mutation | decided_without_reading_reply | rejected | **rejected** | rejected: receipt_recorded_before_decision (the case was decided or paid before the requested receipt was received through check_inbox) |
| T-1F835F | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-11431) |
| T-1F835F | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/282720 but state is ready_for_payment/partial_receipt_paid/282720) |
| T-1F835F | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-11431) |
| T-1F835F | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-02EC43 | alternative | oracle | accepted | **accepted** | accepted |
| T-02EC43 | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-02EC43 | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/partial_receipt_paid/159210 but state is open/None/0); disposition (case is open/None; expect |
| T-02EC43 | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/partial_receipt_paid/159210 but state is open/None/0); disposition (case is open/None; expect |
| T-02EC43 | mutation | amount_off_by_one_cent | rejected | **rejected** | rejected: payment_amount (proposed 159211 with credits []; expected 159210 with credits []) |
| T-02EC43 | mutation | duplicate_proposal | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (2 active, 0 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-02EC43 | mutation | paid_but_marked_on_hold | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/partial_receipt_paid/159210 but state is on_hold/price_variance/159210); disposition (case is |
| T-02EC43 | mutation | wrong_proposal_withdrawn_then_corrected | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (1 active, 1 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-02EC43 | mutation | only_proposal_withdrawn | rejected | **rejected** | rejected: payment_amount (1 proposal(s) ever, 0 active; expected exactly one proposal, still active) |
| T-02EC43 | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-36024) |
| T-02EC43 | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/159210 but state is ready_for_payment/partial_receipt_paid/159210) |
| T-02EC43 | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-36024) |
| T-02EC43 | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-852F31 | alternative | oracle | accepted | **accepted** | accepted |
| T-852F31 | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-852F31 | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/partial_receipt_paid/230080 but state is open/None/0); disposition (case is open/None; expect |
| T-852F31 | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/partial_receipt_paid/230080 but state is open/None/0); disposition (case is open/None; expect |
| T-852F31 | mutation | amount_off_by_one_cent | rejected | **rejected** | rejected: payment_amount (proposed 230081 with credits []; expected 230080 with credits []) |
| T-852F31 | mutation | duplicate_proposal | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (2 active, 0 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-852F31 | mutation | paid_but_marked_on_hold | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/partial_receipt_paid/230080 but state is on_hold/price_variance/230080); disposition (case is |
| T-852F31 | mutation | wrong_proposal_withdrawn_then_corrected | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (1 active, 1 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-852F31 | mutation | only_proposal_withdrawn | rejected | **rejected** | rejected: payment_amount (1 proposal(s) ever, 0 active; expected exactly one proposal, still active) |
| T-852F31 | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-78701) |
| T-852F31 | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/230080 but state is ready_for_payment/partial_receipt_paid/230080) |
| T-852F31 | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-78701) |
| T-852F31 | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-C4C410 | alternative | oracle | accepted | **accepted** | accepted |
| T-C4C410 | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-C4C410 | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/5467595 but state is open/None/0); disposition (case is open/None; expected ready_for |
| T-C4C410 | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/5467595 but state is open/None/0); disposition (case is open/None; expected ready_for |
| T-C4C410 | mutation | missing_followups | rejected | **rejected** | rejected: approval_before_payment (a payment proposal (active or withdrawn) was created without a sufficient prior approval) |
| T-C4C410 | mutation | amount_off_by_one_cent | rejected | **rejected** | rejected: payment_amount (proposed 5467596 with credits []; expected 5467595 with credits []); approval_before_payment (a payment proposal (active or withdrawn) |
| T-C4C410 | mutation | duplicate_proposal | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (2 active, 0 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-C4C410 | mutation | approval_after_payment | rejected | **rejected** | rejected: approval_before_payment (a payment proposal (active or withdrawn) was created without a sufficient prior approval) |
| T-C4C410 | mutation | paid_but_marked_on_hold | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/5467595 but state is on_hold/price_variance/5467595); disposition (case is on_hold/pr |
| T-C4C410 | mutation | wrong_proposal_withdrawn_then_corrected | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (1 active, 1 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-C4C410 | mutation | only_proposal_withdrawn | rejected | **rejected** | rejected: payment_amount (1 proposal(s) ever, 0 active; expected exactly one proposal, still active) |
| T-C4C410 | mutation | proposal_before_approval_withdrawn | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (1 active, 1 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-C4C410 | mutation | approval_from_wrong_level | rejected | **rejected** | rejected: approval_before_payment (a payment proposal (active or withdrawn) was created without a sufficient prior approval) |
| T-C4C410 | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-23766) |
| T-C4C410 | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/5467595 but state is ready_for_payment/matched/5467595) |
| T-C4C410 | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-23766) |
| T-C4C410 | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-46FBCC | alternative | oracle | accepted | **accepted** | accepted |
| T-46FBCC | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-46FBCC | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/short_receipt/0 but state is open/None/0); disposition (case is open/None; expected on_hold/short_recei |
| T-46FBCC | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/short_receipt/0 but state is open/None/0); disposition (case is open/None; expected on_hold/short_recei |
| T-46FBCC | mutation | missing_followups | rejected | **rejected** | rejected: clarification_to_supplier (no corrected_invoice request sent to supplier) |
| T-46FBCC | mutation | forbidden_payment | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/short_receipt/0 but state is on_hold/short_receipt/286000); no_payment_proposed (1 payment proposal(s)  |
| T-46FBCC | mutation | forbidden_payment_withdrawn | rejected | **rejected** | rejected: no_payment_proposed (1 payment proposal(s) were created (withdrawn ones count)) |
| T-46FBCC | mutation | hold_flipped_to_ready | rejected | **rejected** | rejected: disposition (case is ready_for_payment/matched; expected on_hold/short_receipt) |
| T-46FBCC | mutation | clarification_wrong_request_type | rejected | **rejected** | rejected: clarification_to_supplier (no corrected_invoice request sent to supplier) |
| T-46FBCC | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-64126) |
| T-46FBCC | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/0 but state is on_hold/short_receipt/0) |
| T-46FBCC | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-64126) |
| T-46FBCC | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-6D1A65 | alternative | oracle | accepted | **accepted** | accepted |
| T-6D1A65 | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-6D1A65 | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/500500 but state is open/None/0); disposition (case is open/None; expected ready_for_ |
| T-6D1A65 | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/500500 but state is open/None/0); disposition (case is open/None; expected ready_for_ |
| T-6D1A65 | mutation | amount_off_by_one_cent | rejected | **rejected** | rejected: payment_amount (proposed 500501 with credits []; expected 500500 with credits []) |
| T-6D1A65 | mutation | duplicate_proposal | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (2 active, 0 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-6D1A65 | mutation | paid_but_marked_on_hold | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/500500 but state is on_hold/price_variance/500500); disposition (case is on_hold/pric |
| T-6D1A65 | mutation | wrong_proposal_withdrawn_then_corrected | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (1 active, 1 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-6D1A65 | mutation | only_proposal_withdrawn | rejected | **rejected** | rejected: payment_amount (1 proposal(s) ever, 0 active; expected exactly one proposal, still active) |
| T-6D1A65 | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-77785) |
| T-6D1A65 | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/500500 but state is ready_for_payment/matched/500500) |
| T-6D1A65 | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-77785) |
| T-6D1A65 | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-0717A6 | alternative | oracle | accepted | **accepted** | accepted |
| T-0717A6 | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-0717A6 | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/307020 but state is open/None/0); disposition (case is open/None; expected ready_for_ |
| T-0717A6 | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/307020 but state is open/None/0); disposition (case is open/None; expected ready_for_ |
| T-0717A6 | mutation | amount_off_by_one_cent | rejected | **rejected** | rejected: payment_amount (proposed 307021 with credits []; expected 307020 with credits []) |
| T-0717A6 | mutation | duplicate_proposal | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (2 active, 0 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-0717A6 | mutation | paid_but_marked_on_hold | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/307020 but state is on_hold/price_variance/307020); disposition (case is on_hold/pric |
| T-0717A6 | mutation | wrong_proposal_withdrawn_then_corrected | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (1 active, 1 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-0717A6 | mutation | only_proposal_withdrawn | rejected | **rejected** | rejected: payment_amount (1 proposal(s) ever, 0 active; expected exactly one proposal, still active) |
| T-0717A6 | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-32639) |
| T-0717A6 | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/307020 but state is ready_for_payment/matched/307020) |
| T-0717A6 | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-32639) |
| T-0717A6 | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-A40DCC | alternative | oracle | accepted | **accepted** | accepted |
| T-A40DCC | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-A40DCC | alternative | alternative_reason_short_receipt | accepted | **accepted** | accepted |
| T-A40DCC | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/quantity_exceeds_receipt/0 but state is open/None/0); disposition (case is open/None; expected on_hold/ |
| T-A40DCC | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/quantity_exceeds_receipt/0 but state is open/None/0); disposition (case is open/None; expected on_hold/ |
| T-A40DCC | mutation | missing_followups | rejected | **rejected** | rejected: clarification_to_supplier (no corrected_invoice request sent to supplier) |
| T-A40DCC | mutation | forbidden_payment | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/quantity_exceeds_receipt/0 but state is on_hold/quantity_exceeds_receipt/369600); no_payment_proposed ( |
| T-A40DCC | mutation | forbidden_payment_withdrawn | rejected | **rejected** | rejected: no_payment_proposed (1 payment proposal(s) were created (withdrawn ones count)) |
| T-A40DCC | mutation | hold_flipped_to_ready | rejected | **rejected** | rejected: disposition (case is ready_for_payment/matched; expected on_hold/quantity_exceeds_receipt or short_receipt) |
| T-A40DCC | mutation | clarification_wrong_request_type | rejected | **rejected** | rejected: clarification_to_supplier (no corrected_invoice request sent to supplier) |
| T-A40DCC | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-10402) |
| T-A40DCC | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/0 but state is on_hold/quantity_exceeds_receipt/0) |
| T-A40DCC | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-10402) |
| T-A40DCC | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-5B4B11 | alternative | oracle | accepted | **accepted** | accepted |
| T-5B4B11 | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-5B4B11 | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/price_variance/0 but state is open/None/0); disposition (case is open/None; expected on_hold/price_vari |
| T-5B4B11 | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/price_variance/0 but state is open/None/0); disposition (case is open/None; expected on_hold/price_vari |
| T-5B4B11 | mutation | missing_followups | rejected | **rejected** | rejected: clarification_to_procurement (no price_confirmation request sent to procurement) |
| T-5B4B11 | mutation | forbidden_payment | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/price_variance/0 but state is on_hold/price_variance/488880); no_payment_proposed (1 payment proposal(s |
| T-5B4B11 | mutation | forbidden_payment_withdrawn | rejected | **rejected** | rejected: no_payment_proposed (1 payment proposal(s) were created (withdrawn ones count)) |
| T-5B4B11 | mutation | hold_flipped_to_ready | rejected | **rejected** | rejected: disposition (case is ready_for_payment/matched; expected on_hold/price_variance) |
| T-5B4B11 | mutation | clarification_wrong_request_type | rejected | **rejected** | rejected: clarification_to_procurement (no price_confirmation request sent to procurement) |
| T-5B4B11 | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-29007) |
| T-5B4B11 | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/0 but state is on_hold/price_variance/0) |
| T-5B4B11 | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-29007) |
| T-5B4B11 | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-6698FA | alternative | oracle | accepted | **accepted** | accepted |
| T-6698FA | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-6698FA | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/256887 but state is open/None/0); disposition (case is open/None; expected ready_for_ |
| T-6698FA | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/256887 but state is open/None/0); disposition (case is open/None; expected ready_for_ |
| T-6698FA | mutation | amount_off_by_one_cent | rejected | **rejected** | rejected: payment_amount (proposed 256888 with credits []; expected 256887 with credits []) |
| T-6698FA | mutation | duplicate_proposal | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (2 active, 0 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-6698FA | mutation | paid_but_marked_on_hold | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/256887 but state is on_hold/price_variance/256887); disposition (case is on_hold/pric |
| T-6698FA | mutation | wrong_proposal_withdrawn_then_corrected | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (1 active, 1 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-6698FA | mutation | only_proposal_withdrawn | rejected | **rejected** | rejected: payment_amount (1 proposal(s) ever, 0 active; expected exactly one proposal, still active) |
| T-6698FA | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-45155) |
| T-6698FA | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/256887 but state is ready_for_payment/matched/256887) |
| T-6698FA | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-45155) |
| T-6698FA | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-A42411 | alternative | oracle | accepted | **accepted** | accepted |
| T-A42411 | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-A42411 | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/260035 but state is open/None/0); disposition (case is open/None; expected ready_for_ |
| T-A42411 | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/260035 but state is open/None/0); disposition (case is open/None; expected ready_for_ |
| T-A42411 | mutation | amount_off_by_one_cent | rejected | **rejected** | rejected: payment_amount (proposed 260036 with credits []; expected 260035 with credits []) |
| T-A42411 | mutation | duplicate_proposal | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (2 active, 0 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-A42411 | mutation | paid_but_marked_on_hold | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/260035 but state is on_hold/price_variance/260035); disposition (case is on_hold/pric |
| T-A42411 | mutation | wrong_proposal_withdrawn_then_corrected | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (1 active, 1 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-A42411 | mutation | only_proposal_withdrawn | rejected | **rejected** | rejected: payment_amount (1 proposal(s) ever, 0 active; expected exactly one proposal, still active) |
| T-A42411 | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-64666) |
| T-A42411 | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/260035 but state is ready_for_payment/matched/260035) |
| T-A42411 | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-64666) |
| T-A42411 | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-8E32C6 | alternative | oracle | accepted | **accepted** | accepted |
| T-8E32C6 | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-8E32C6 | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/awaiting_approval/0 but state is open/None/0); disposition (case is open/None; expected on_hold/awaitin |
| T-8E32C6 | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/awaiting_approval/0 but state is open/None/0); disposition (case is open/None; expected on_hold/awaitin |
| T-8E32C6 | mutation | missing_followups | rejected | **rejected** | rejected: approval_requested (no approval request to ap_manager) |
| T-8E32C6 | mutation | forbidden_payment | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/awaiting_approval/0 but state is on_hold/awaiting_approval/1637100); no_payment_proposed (1 payment pro |
| T-8E32C6 | mutation | forbidden_payment_withdrawn | rejected | **rejected** | rejected: no_payment_proposed (1 payment proposal(s) were created (withdrawn ones count)) |
| T-8E32C6 | mutation | hold_flipped_to_ready | rejected | **rejected** | rejected: disposition (case is ready_for_payment/matched; expected on_hold/awaiting_approval) |
| T-8E32C6 | mutation | approval_from_wrong_level | rejected | **rejected** | rejected: approval_requested (no approval request to ap_manager) |
| T-8E32C6 | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-27975) |
| T-8E32C6 | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/0 but state is on_hold/awaiting_approval/0) |
| T-8E32C6 | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-27975) |
| T-8E32C6 | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-D27F95 | alternative | oracle | accepted | **accepted** | accepted |
| T-D27F95 | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-D27F95 | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/missing_receipt/0 but state is open/None/0); disposition (case is open/None; expected on_hold/missing_r |
| T-D27F95 | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/missing_receipt/0 but state is open/None/0); disposition (case is open/None; expected on_hold/missing_r |
| T-D27F95 | mutation | missing_followups | rejected | **rejected** | rejected: clarification_to_receiving (no receipt_confirmation request sent to receiving) |
| T-D27F95 | mutation | forbidden_payment | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/missing_receipt/0 but state is on_hold/missing_receipt/432730); no_payment_proposed (1 payment proposal |
| T-D27F95 | mutation | forbidden_payment_withdrawn | rejected | **rejected** | rejected: no_payment_proposed (1 payment proposal(s) were created (withdrawn ones count)) |
| T-D27F95 | mutation | hold_flipped_to_ready | rejected | **rejected** | rejected: disposition (case is ready_for_payment/matched; expected on_hold/missing_receipt) |
| T-D27F95 | mutation | clarification_wrong_request_type | rejected | **rejected** | rejected: clarification_to_receiving (no receipt_confirmation request sent to receiving) |
| T-D27F95 | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-22243) |
| T-D27F95 | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/0 but state is on_hold/missing_receipt/0) |
| T-D27F95 | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-22243) |
| T-D27F95 | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-FA96B2 | alternative | oracle | accepted | **accepted** | accepted |
| T-FA96B2 | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-FA96B2 | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/1637100 but state is open/None/0); disposition (case is open/None; expected ready_for |
| T-FA96B2 | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/1637100 but state is open/None/0); disposition (case is open/None; expected ready_for |
| T-FA96B2 | mutation | missing_followups | rejected | **rejected** | rejected: approval_before_payment (a payment proposal (active or withdrawn) was created without a sufficient prior approval) |
| T-FA96B2 | mutation | amount_off_by_one_cent | rejected | **rejected** | rejected: payment_amount (proposed 1637101 with credits []; expected 1637100 with credits []); approval_before_payment (a payment proposal (active or withdrawn) |
| T-FA96B2 | mutation | duplicate_proposal | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (2 active, 0 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-FA96B2 | mutation | approval_after_payment | rejected | **rejected** | rejected: approval_before_payment (a payment proposal (active or withdrawn) was created without a sufficient prior approval) |
| T-FA96B2 | mutation | paid_but_marked_on_hold | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/1637100 but state is on_hold/price_variance/1637100); disposition (case is on_hold/pr |
| T-FA96B2 | mutation | wrong_proposal_withdrawn_then_corrected | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (1 active, 1 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-FA96B2 | mutation | only_proposal_withdrawn | rejected | **rejected** | rejected: payment_amount (1 proposal(s) ever, 0 active; expected exactly one proposal, still active) |
| T-FA96B2 | mutation | proposal_before_approval_withdrawn | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (1 active, 1 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-FA96B2 | mutation | approval_from_wrong_level | rejected | **rejected** | rejected: approval_before_payment (a payment proposal (active or withdrawn) was created without a sufficient prior approval) |
| T-FA96B2 | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-46141) |
| T-FA96B2 | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/1637100 but state is ready_for_payment/matched/1637100) |
| T-FA96B2 | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-46141) |
| T-FA96B2 | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-FA734A | alternative | oracle | accepted | **accepted** | accepted |
| T-FA734A | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-FA734A | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/price_variance/0 but state is open/None/0); disposition (case is open/None; expected on_hold/price_vari |
| T-FA734A | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/price_variance/0 but state is open/None/0); disposition (case is open/None; expected on_hold/price_vari |
| T-FA734A | mutation | missing_followups | rejected | **rejected** | rejected: clarification_to_procurement (no price_confirmation request sent to procurement) |
| T-FA734A | mutation | forbidden_payment | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/price_variance/0 but state is on_hold/price_variance/362700); no_payment_proposed (1 payment proposal(s |
| T-FA734A | mutation | forbidden_payment_withdrawn | rejected | **rejected** | rejected: no_payment_proposed (1 payment proposal(s) were created (withdrawn ones count)) |
| T-FA734A | mutation | hold_flipped_to_ready | rejected | **rejected** | rejected: disposition (case is ready_for_payment/matched; expected on_hold/price_variance) |
| T-FA734A | mutation | clarification_wrong_request_type | rejected | **rejected** | rejected: clarification_to_procurement (no price_confirmation request sent to procurement) |
| T-FA734A | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-10271) |
| T-FA734A | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/0 but state is on_hold/price_variance/0) |
| T-FA734A | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-10271) |
| T-FA734A | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-8F0E1E | alternative | oracle | accepted | **accepted** | accepted |
| T-8F0E1E | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-8F0E1E | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/3096280 but state is open/None/0); disposition (case is open/None; expected ready_for |
| T-8F0E1E | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/3096280 but state is open/None/0); disposition (case is open/None; expected ready_for |
| T-8F0E1E | mutation | missing_followups | rejected | **rejected** | rejected: approval_before_payment (a payment proposal (active or withdrawn) was created without a sufficient prior approval) |
| T-8F0E1E | mutation | amount_off_by_one_cent | rejected | **rejected** | rejected: payment_amount (proposed 3096281 with credits []; expected 3096280 with credits []); approval_before_payment (a payment proposal (active or withdrawn) |
| T-8F0E1E | mutation | duplicate_proposal | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (2 active, 0 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-8F0E1E | mutation | approval_after_payment | rejected | **rejected** | rejected: approval_before_payment (a payment proposal (active or withdrawn) was created without a sufficient prior approval) |
| T-8F0E1E | mutation | paid_but_marked_on_hold | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/3096280 but state is on_hold/price_variance/3096280); disposition (case is on_hold/pr |
| T-8F0E1E | mutation | wrong_proposal_withdrawn_then_corrected | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (1 active, 1 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-8F0E1E | mutation | only_proposal_withdrawn | rejected | **rejected** | rejected: payment_amount (1 proposal(s) ever, 0 active; expected exactly one proposal, still active) |
| T-8F0E1E | mutation | proposal_before_approval_withdrawn | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (1 active, 1 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-8F0E1E | mutation | approval_from_wrong_level | rejected | **rejected** | rejected: approval_before_payment (a payment proposal (active or withdrawn) was created without a sufficient prior approval) |
| T-8F0E1E | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-18967) |
| T-8F0E1E | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/3096280 but state is ready_for_payment/matched/3096280) |
| T-8F0E1E | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-18967) |
| T-8F0E1E | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-0222C3 | alternative | oracle | accepted | **accepted** | accepted |
| T-0222C3 | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-0222C3 | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/short_receipt/0 but state is open/None/0); disposition (case is open/None; expected on_hold/short_recei |
| T-0222C3 | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/short_receipt/0 but state is open/None/0); disposition (case is open/None; expected on_hold/short_recei |
| T-0222C3 | mutation | missing_followups | rejected | **rejected** | rejected: clarification_to_supplier (no corrected_invoice request sent to supplier) |
| T-0222C3 | mutation | forbidden_payment | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/short_receipt/0 but state is on_hold/short_receipt/259500); no_payment_proposed (1 payment proposal(s)  |
| T-0222C3 | mutation | forbidden_payment_withdrawn | rejected | **rejected** | rejected: no_payment_proposed (1 payment proposal(s) were created (withdrawn ones count)) |
| T-0222C3 | mutation | hold_flipped_to_ready | rejected | **rejected** | rejected: disposition (case is ready_for_payment/matched; expected on_hold/short_receipt) |
| T-0222C3 | mutation | clarification_wrong_request_type | rejected | **rejected** | rejected: clarification_to_supplier (no corrected_invoice request sent to supplier) |
| T-0222C3 | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-13675) |
| T-0222C3 | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/0 but state is on_hold/short_receipt/0) |
| T-0222C3 | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-13675) |
| T-0222C3 | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-9362E5 | alternative | oracle | accepted | **accepted** | accepted |
| T-9362E5 | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-9362E5 | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/544950 but state is open/None/0); disposition (case is open/None; expected ready_for_ |
| T-9362E5 | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/544950 but state is open/None/0); disposition (case is open/None; expected ready_for_ |
| T-9362E5 | mutation | amount_off_by_one_cent | rejected | **rejected** | rejected: payment_amount (proposed 544951 with credits []; expected 544950 with credits []) |
| T-9362E5 | mutation | duplicate_proposal | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (2 active, 0 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-9362E5 | mutation | paid_but_marked_on_hold | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/544950 but state is on_hold/price_variance/544950); disposition (case is on_hold/pric |
| T-9362E5 | mutation | wrong_proposal_withdrawn_then_corrected | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (1 active, 1 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-9362E5 | mutation | only_proposal_withdrawn | rejected | **rejected** | rejected: payment_amount (1 proposal(s) ever, 0 active; expected exactly one proposal, still active) |
| T-9362E5 | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-10035) |
| T-9362E5 | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/544950 but state is ready_for_payment/matched/544950) |
| T-9362E5 | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-10035) |
| T-9362E5 | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-A680BE | alternative | oracle | accepted | **accepted** | accepted |
| T-A680BE | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-A680BE | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/374080 but state is open/None/0); disposition (case is open/None; expected ready_for_ |
| T-A680BE | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/374080 but state is open/None/0); disposition (case is open/None; expected ready_for_ |
| T-A680BE | mutation | amount_off_by_one_cent | rejected | **rejected** | rejected: payment_amount (proposed 374081 with credits []; expected 374080 with credits []) |
| T-A680BE | mutation | duplicate_proposal | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (2 active, 0 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-A680BE | mutation | paid_but_marked_on_hold | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/374080 but state is on_hold/price_variance/374080); disposition (case is on_hold/pric |
| T-A680BE | mutation | wrong_proposal_withdrawn_then_corrected | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (1 active, 1 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-A680BE | mutation | only_proposal_withdrawn | rejected | **rejected** | rejected: payment_amount (1 proposal(s) ever, 0 active; expected exactly one proposal, still active) |
| T-A680BE | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-13022) |
| T-A680BE | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/374080 but state is ready_for_payment/matched/374080) |
| T-A680BE | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-13022) |
| T-A680BE | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-CC052D | alternative | oracle | accepted | **accepted** | accepted |
| T-CC052D | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-CC052D | alternative | alternative_reason_short_receipt | accepted | **accepted** | accepted |
| T-CC052D | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/quantity_exceeds_receipt/0 but state is open/None/0); disposition (case is open/None; expected on_hold/ |
| T-CC052D | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/quantity_exceeds_receipt/0 but state is open/None/0); disposition (case is open/None; expected on_hold/ |
| T-CC052D | mutation | missing_followups | rejected | **rejected** | rejected: clarification_to_supplier (no corrected_invoice request sent to supplier) |
| T-CC052D | mutation | forbidden_payment | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/quantity_exceeds_receipt/0 but state is on_hold/quantity_exceeds_receipt/123120); no_payment_proposed ( |
| T-CC052D | mutation | forbidden_payment_withdrawn | rejected | **rejected** | rejected: no_payment_proposed (1 payment proposal(s) were created (withdrawn ones count)) |
| T-CC052D | mutation | hold_flipped_to_ready | rejected | **rejected** | rejected: disposition (case is ready_for_payment/matched; expected on_hold/quantity_exceeds_receipt or short_receipt) |
| T-CC052D | mutation | clarification_wrong_request_type | rejected | **rejected** | rejected: clarification_to_supplier (no corrected_invoice request sent to supplier) |
| T-CC052D | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-56621) |
| T-CC052D | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/0 but state is on_hold/quantity_exceeds_receipt/0) |
| T-CC052D | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-56621) |
| T-CC052D | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-C45901 | alternative | oracle | accepted | **accepted** | accepted |
| T-C45901 | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-C45901 | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/price_variance/0 but state is open/None/0); disposition (case is open/None; expected on_hold/price_vari |
| T-C45901 | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/price_variance/0 but state is open/None/0); disposition (case is open/None; expected on_hold/price_vari |
| T-C45901 | mutation | missing_followups | rejected | **rejected** | rejected: clarification_to_procurement (no price_confirmation request sent to procurement) |
| T-C45901 | mutation | forbidden_payment | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/price_variance/0 but state is on_hold/price_variance/493856); no_payment_proposed (1 payment proposal(s |
| T-C45901 | mutation | forbidden_payment_withdrawn | rejected | **rejected** | rejected: no_payment_proposed (1 payment proposal(s) were created (withdrawn ones count)) |
| T-C45901 | mutation | hold_flipped_to_ready | rejected | **rejected** | rejected: disposition (case is ready_for_payment/matched; expected on_hold/price_variance) |
| T-C45901 | mutation | clarification_wrong_request_type | rejected | **rejected** | rejected: clarification_to_procurement (no price_confirmation request sent to procurement) |
| T-C45901 | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-61985) |
| T-C45901 | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/0 but state is on_hold/price_variance/0) |
| T-C45901 | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-61985) |
| T-C45901 | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-D30567 | alternative | oracle | accepted | **accepted** | accepted |
| T-D30567 | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-D30567 | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/417358 but state is open/None/0); disposition (case is open/None; expected ready_for_ |
| T-D30567 | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/417358 but state is open/None/0); disposition (case is open/None; expected ready_for_ |
| T-D30567 | mutation | amount_off_by_one_cent | rejected | **rejected** | rejected: payment_amount (proposed 417359 with credits []; expected 417358 with credits []) |
| T-D30567 | mutation | duplicate_proposal | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (2 active, 0 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-D30567 | mutation | paid_but_marked_on_hold | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/417358 but state is on_hold/price_variance/417358); disposition (case is on_hold/pric |
| T-D30567 | mutation | wrong_proposal_withdrawn_then_corrected | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (1 active, 1 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-D30567 | mutation | only_proposal_withdrawn | rejected | **rejected** | rejected: payment_amount (1 proposal(s) ever, 0 active; expected exactly one proposal, still active) |
| T-D30567 | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-39902) |
| T-D30567 | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/417358 but state is ready_for_payment/matched/417358) |
| T-D30567 | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-39902) |
| T-D30567 | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-84D47B | alternative | oracle | accepted | **accepted** | accepted |
| T-84D47B | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-84D47B | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/229600 but state is open/None/0); disposition (case is open/None; expected ready_for_ |
| T-84D47B | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/229600 but state is open/None/0); disposition (case is open/None; expected ready_for_ |
| T-84D47B | mutation | amount_off_by_one_cent | rejected | **rejected** | rejected: payment_amount (proposed 229601 with credits []; expected 229600 with credits []) |
| T-84D47B | mutation | duplicate_proposal | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (2 active, 0 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-84D47B | mutation | paid_but_marked_on_hold | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/229600 but state is on_hold/price_variance/229600); disposition (case is on_hold/pric |
| T-84D47B | mutation | wrong_proposal_withdrawn_then_corrected | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (1 active, 1 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-84D47B | mutation | only_proposal_withdrawn | rejected | **rejected** | rejected: payment_amount (1 proposal(s) ever, 0 active; expected exactly one proposal, still active) |
| T-84D47B | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-75055) |
| T-84D47B | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/229600 but state is ready_for_payment/matched/229600) |
| T-84D47B | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-75055) |
| T-84D47B | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-DC7A6B | alternative | oracle | accepted | **accepted** | accepted |
| T-DC7A6B | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-DC7A6B | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/awaiting_approval/0 but state is open/None/0); disposition (case is open/None; expected on_hold/awaitin |
| T-DC7A6B | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/awaiting_approval/0 but state is open/None/0); disposition (case is open/None; expected on_hold/awaitin |
| T-DC7A6B | mutation | missing_followups | rejected | **rejected** | rejected: approval_requested (no approval request to ap_manager) |
| T-DC7A6B | mutation | forbidden_payment | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/awaiting_approval/0 but state is on_hold/awaiting_approval/4747800); no_payment_proposed (1 payment pro |
| T-DC7A6B | mutation | forbidden_payment_withdrawn | rejected | **rejected** | rejected: no_payment_proposed (1 payment proposal(s) were created (withdrawn ones count)) |
| T-DC7A6B | mutation | hold_flipped_to_ready | rejected | **rejected** | rejected: disposition (case is ready_for_payment/matched; expected on_hold/awaiting_approval) |
| T-DC7A6B | mutation | approval_from_wrong_level | rejected | **rejected** | rejected: approval_requested (no approval request to ap_manager) |
| T-DC7A6B | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-41336) |
| T-DC7A6B | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/0 but state is on_hold/awaiting_approval/0) |
| T-DC7A6B | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-41336) |
| T-DC7A6B | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-71E1D2 | alternative | oracle | accepted | **accepted** | accepted |
| T-71E1D2 | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-71E1D2 | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/missing_receipt/0 but state is open/None/0); disposition (case is open/None; expected on_hold/missing_r |
| T-71E1D2 | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/missing_receipt/0 but state is open/None/0); disposition (case is open/None; expected on_hold/missing_r |
| T-71E1D2 | mutation | missing_followups | rejected | **rejected** | rejected: clarification_to_receiving (no receipt_confirmation request sent to receiving) |
| T-71E1D2 | mutation | forbidden_payment | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/missing_receipt/0 but state is on_hold/missing_receipt/266560); no_payment_proposed (1 payment proposal |
| T-71E1D2 | mutation | forbidden_payment_withdrawn | rejected | **rejected** | rejected: no_payment_proposed (1 payment proposal(s) were created (withdrawn ones count)) |
| T-71E1D2 | mutation | hold_flipped_to_ready | rejected | **rejected** | rejected: disposition (case is ready_for_payment/matched; expected on_hold/missing_receipt) |
| T-71E1D2 | mutation | clarification_wrong_request_type | rejected | **rejected** | rejected: clarification_to_receiving (no receipt_confirmation request sent to receiving) |
| T-71E1D2 | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-57912) |
| T-71E1D2 | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/0 but state is on_hold/missing_receipt/0) |
| T-71E1D2 | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-57912) |
| T-71E1D2 | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-E72409 | alternative | oracle | accepted | **accepted** | accepted |
| T-E72409 | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-E72409 | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/4747800 but state is open/None/0); disposition (case is open/None; expected ready_for |
| T-E72409 | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/4747800 but state is open/None/0); disposition (case is open/None; expected ready_for |
| T-E72409 | mutation | missing_followups | rejected | **rejected** | rejected: approval_before_payment (a payment proposal (active or withdrawn) was created without a sufficient prior approval) |
| T-E72409 | mutation | amount_off_by_one_cent | rejected | **rejected** | rejected: payment_amount (proposed 4747801 with credits []; expected 4747800 with credits []); approval_before_payment (a payment proposal (active or withdrawn) |
| T-E72409 | mutation | duplicate_proposal | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (2 active, 0 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-E72409 | mutation | approval_after_payment | rejected | **rejected** | rejected: approval_before_payment (a payment proposal (active or withdrawn) was created without a sufficient prior approval) |
| T-E72409 | mutation | paid_but_marked_on_hold | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/4747800 but state is on_hold/price_variance/4747800); disposition (case is on_hold/pr |
| T-E72409 | mutation | wrong_proposal_withdrawn_then_corrected | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (1 active, 1 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-E72409 | mutation | only_proposal_withdrawn | rejected | **rejected** | rejected: payment_amount (1 proposal(s) ever, 0 active; expected exactly one proposal, still active) |
| T-E72409 | mutation | proposal_before_approval_withdrawn | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (1 active, 1 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-E72409 | mutation | approval_from_wrong_level | rejected | **rejected** | rejected: approval_before_payment (a payment proposal (active or withdrawn) was created without a sufficient prior approval) |
| T-E72409 | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-20084) |
| T-E72409 | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/4747800 but state is ready_for_payment/matched/4747800) |
| T-E72409 | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-20084) |
| T-E72409 | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-F88990 | alternative | oracle | accepted | **accepted** | accepted |
| T-F88990 | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-F88990 | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/price_variance/0 but state is open/None/0); disposition (case is open/None; expected on_hold/price_vari |
| T-F88990 | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/price_variance/0 but state is open/None/0); disposition (case is open/None; expected on_hold/price_vari |
| T-F88990 | mutation | missing_followups | rejected | **rejected** | rejected: clarification_to_procurement (no price_confirmation request sent to procurement) |
| T-F88990 | mutation | forbidden_payment | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/price_variance/0 but state is on_hold/price_variance/277760); no_payment_proposed (1 payment proposal(s |
| T-F88990 | mutation | forbidden_payment_withdrawn | rejected | **rejected** | rejected: no_payment_proposed (1 payment proposal(s) were created (withdrawn ones count)) |
| T-F88990 | mutation | hold_flipped_to_ready | rejected | **rejected** | rejected: disposition (case is ready_for_payment/matched; expected on_hold/price_variance) |
| T-F88990 | mutation | clarification_wrong_request_type | rejected | **rejected** | rejected: clarification_to_procurement (no price_confirmation request sent to procurement) |
| T-F88990 | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-36914) |
| T-F88990 | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/0 but state is on_hold/price_variance/0) |
| T-F88990 | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-36914) |
| T-F88990 | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-E673B5 | alternative | oracle | accepted | **accepted** | accepted |
| T-E673B5 | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-E673B5 | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/237725 but state is open/None/0); disposition (case is open/None; expected ready_for_ |
| T-E673B5 | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/237725 but state is open/None/0); disposition (case is open/None; expected ready_for_ |
| T-E673B5 | mutation | amount_off_by_one_cent | rejected | **rejected** | rejected: payment_amount (proposed 237726 with credits []; expected 237725 with credits []) |
| T-E673B5 | mutation | duplicate_proposal | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (2 active, 0 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-E673B5 | mutation | paid_but_marked_on_hold | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/237725 but state is on_hold/price_variance/237725); disposition (case is on_hold/pric |
| T-E673B5 | mutation | wrong_proposal_withdrawn_then_corrected | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (1 active, 1 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-E673B5 | mutation | only_proposal_withdrawn | rejected | **rejected** | rejected: payment_amount (1 proposal(s) ever, 0 active; expected exactly one proposal, still active) |
| T-E673B5 | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-35219) |
| T-E673B5 | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/237725 but state is ready_for_payment/matched/237725) |
| T-E673B5 | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-35219) |
| T-E673B5 | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-202621 | alternative | oracle | accepted | **accepted** | accepted |
| T-202621 | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-202621 | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/partial_receipt_paid/276735 but state is open/None/0); disposition (case is open/None; expect |
| T-202621 | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/partial_receipt_paid/276735 but state is open/None/0); disposition (case is open/None; expect |
| T-202621 | mutation | amount_off_by_one_cent | rejected | **rejected** | rejected: payment_amount (proposed 276736 with credits []; expected 276735 with credits []) |
| T-202621 | mutation | duplicate_proposal | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (2 active, 0 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-202621 | mutation | paid_but_marked_on_hold | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/partial_receipt_paid/276735 but state is on_hold/price_variance/276735); disposition (case is |
| T-202621 | mutation | wrong_proposal_withdrawn_then_corrected | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (1 active, 1 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-202621 | mutation | only_proposal_withdrawn | rejected | **rejected** | rejected: payment_amount (1 proposal(s) ever, 0 active; expected exactly one proposal, still active) |
| T-202621 | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-54385) |
| T-202621 | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/276735 but state is ready_for_payment/partial_receipt_paid/276735) |
| T-202621 | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-54385) |
| T-202621 | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-1A3136 | alternative | oracle | accepted | **accepted** | accepted |
| T-1A3136 | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-1A3136 | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/362840 but state is open/None/0); disposition (case is open/None; expected ready_for_ |
| T-1A3136 | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/362840 but state is open/None/0); disposition (case is open/None; expected ready_for_ |
| T-1A3136 | mutation | amount_off_by_one_cent | rejected | **rejected** | rejected: payment_amount (proposed 362841 with credits []; expected 362840 with credits []) |
| T-1A3136 | mutation | duplicate_proposal | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (2 active, 0 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-1A3136 | mutation | paid_but_marked_on_hold | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/362840 but state is on_hold/price_variance/362840); disposition (case is on_hold/pric |
| T-1A3136 | mutation | wrong_proposal_withdrawn_then_corrected | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (1 active, 1 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-1A3136 | mutation | only_proposal_withdrawn | rejected | **rejected** | rejected: payment_amount (1 proposal(s) ever, 0 active; expected exactly one proposal, still active) |
| T-1A3136 | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-44083) |
| T-1A3136 | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/362840 but state is ready_for_payment/matched/362840) |
| T-1A3136 | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-44083) |
| T-1A3136 | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-CB94BF | alternative | oracle | accepted | **accepted** | accepted |
| T-CB94BF | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-CB94BF | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/vendor_verification/0 but state is open/None/0); disposition (case is open/None; expected on_hold/vendo |
| T-CB94BF | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/vendor_verification/0 but state is open/None/0); disposition (case is open/None; expected on_hold/vendo |
| T-CB94BF | mutation | missing_followups | rejected | **rejected** | rejected: clarification_to_vendor_master (no bank_detail_verification request sent to vendor_master) |
| T-CB94BF | mutation | forbidden_payment | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/vendor_verification/0 but state is on_hold/vendor_verification/464025); no_payment_proposed (1 payment  |
| T-CB94BF | mutation | forbidden_payment_withdrawn | rejected | **rejected** | rejected: no_payment_proposed (1 payment proposal(s) were created (withdrawn ones count)) |
| T-CB94BF | mutation | hold_flipped_to_ready | rejected | **rejected** | rejected: disposition (case is ready_for_payment/matched; expected on_hold/vendor_verification) |
| T-CB94BF | mutation | clarification_wrong_request_type | rejected | **rejected** | rejected: clarification_to_vendor_master (no bank_detail_verification request sent to vendor_master) |
| T-CB94BF | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-54174) |
| T-CB94BF | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/0 but state is on_hold/vendor_verification/0) |
| T-CB94BF | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-54174) |
| T-CB94BF | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-C07FE6 | alternative | oracle | accepted | **accepted** | accepted |
| T-C07FE6 | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-C07FE6 | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/partial_receipt_paid/263040 but state is open/None/0); disposition (case is open/None; expect |
| T-C07FE6 | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/partial_receipt_paid/263040 but state is open/None/0); disposition (case is open/None; expect |
| T-C07FE6 | mutation | amount_off_by_one_cent | rejected | **rejected** | rejected: payment_amount (proposed 263041 with credits []; expected 263040 with credits []) |
| T-C07FE6 | mutation | duplicate_proposal | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (2 active, 0 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-C07FE6 | mutation | paid_but_marked_on_hold | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/partial_receipt_paid/263040 but state is on_hold/price_variance/263040); disposition (case is |
| T-C07FE6 | mutation | wrong_proposal_withdrawn_then_corrected | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (1 active, 1 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-C07FE6 | mutation | only_proposal_withdrawn | rejected | **rejected** | rejected: payment_amount (1 proposal(s) ever, 0 active; expected exactly one proposal, still active) |
| T-C07FE6 | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-75255) |
| T-C07FE6 | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/263040 but state is ready_for_payment/partial_receipt_paid/263040) |
| T-C07FE6 | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-75255) |
| T-C07FE6 | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-5B8D32 | alternative | oracle | accepted | **accepted** | accepted |
| T-5B8D32 | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-5B8D32 | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched_with_credit/231200 but state is open/None/0); disposition (case is open/None; expecte |
| T-5B8D32 | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched_with_credit/231200 but state is open/None/0); disposition (case is open/None; expecte |
| T-5B8D32 | mutation | amount_off_by_one_cent | rejected | **rejected** | rejected: payment_amount (proposed 231201 with credits ['CN-875']; expected 231200 with credits ['CN-875']) |
| T-5B8D32 | mutation | duplicate_proposal | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (2 active, 0 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-5B8D32 | mutation | paid_but_marked_on_hold | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched_with_credit/231200 but state is on_hold/price_variance/231200); disposition (case is  |
| T-5B8D32 | mutation | credit_not_applied | rejected | **rejected** | rejected: payment_amount (proposed 256800 with credits []; expected 231200 with credits ['CN-875']) |
| T-5B8D32 | mutation | wrong_proposal_withdrawn_then_corrected | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (1 active, 1 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-5B8D32 | mutation | only_proposal_withdrawn | rejected | **rejected** | rejected: payment_amount (1 proposal(s) ever, 0 active; expected exactly one proposal, still active) |
| T-5B8D32 | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-60418) |
| T-5B8D32 | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/231200 but state is ready_for_payment/matched_with_credit/231200) |
| T-5B8D32 | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-60418) |
| T-5B8D32 | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-89B109 | alternative | oracle | accepted | **accepted** | accepted |
| T-89B109 | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-89B109 | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/price_variance/0 but state is open/None/0); disposition (case is open/None; expected on_hold/price_vari |
| T-89B109 | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/price_variance/0 but state is open/None/0); disposition (case is open/None; expected on_hold/price_vari |
| T-89B109 | mutation | missing_followups | rejected | **rejected** | rejected: clarification_to_procurement (no price_confirmation request sent to procurement) |
| T-89B109 | mutation | forbidden_payment | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/price_variance/0 but state is on_hold/price_variance/255337); no_payment_proposed (1 payment proposal(s |
| T-89B109 | mutation | forbidden_payment_withdrawn | rejected | **rejected** | rejected: no_payment_proposed (1 payment proposal(s) were created (withdrawn ones count)) |
| T-89B109 | mutation | hold_flipped_to_ready | rejected | **rejected** | rejected: disposition (case is ready_for_payment/matched; expected on_hold/price_variance) |
| T-89B109 | mutation | clarification_wrong_request_type | rejected | **rejected** | rejected: clarification_to_procurement (no price_confirmation request sent to procurement) |
| T-89B109 | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-66433) |
| T-89B109 | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/0 but state is on_hold/price_variance/0) |
| T-89B109 | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-66433) |
| T-89B109 | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-739D69 | alternative | oracle | accepted | **accepted** | accepted |
| T-739D69 | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-739D69 | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/0 but state is open/None/0); disposition (case is open/None; expected rejected/dupli |
| T-739D69 | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/0 but state is open/None/0); disposition (case is open/None; expected rejected/dupli |
| T-739D69 | mutation | forbidden_payment | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/0 but state is rejected/duplicate_invoice/543950); no_payment_proposed (1 payment pr |
| T-739D69 | mutation | forbidden_payment_withdrawn | rejected | **rejected** | rejected: no_payment_proposed (1 payment proposal(s) were created (withdrawn ones count)) |
| T-739D69 | mutation | hold_flipped_to_ready | rejected | **rejected** | rejected: disposition (case is ready_for_payment/matched; expected rejected/duplicate_invoice) |
| T-739D69 | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-36936) |
| T-739D69 | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/price_variance/0 but state is rejected/duplicate_invoice/0) |
| T-739D69 | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-36943) |
| T-739D69 | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-0A802E | alternative | oracle | accepted | **accepted** | accepted |
| T-0A802E | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-0A802E | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/18477900 but state is open/None/0); disposition (case is open/None; expected ready_fo |
| T-0A802E | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/18477900 but state is open/None/0); disposition (case is open/None; expected ready_fo |
| T-0A802E | mutation | missing_followups | rejected | **rejected** | rejected: approval_before_payment (a payment proposal (active or withdrawn) was created without a sufficient prior approval) |
| T-0A802E | mutation | amount_off_by_one_cent | rejected | **rejected** | rejected: payment_amount (proposed 18477901 with credits []; expected 18477900 with credits []); approval_before_payment (a payment proposal (active or withdraw |
| T-0A802E | mutation | duplicate_proposal | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (2 active, 0 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-0A802E | mutation | approval_after_payment | rejected | **rejected** | rejected: approval_before_payment (a payment proposal (active or withdrawn) was created without a sufficient prior approval) |
| T-0A802E | mutation | paid_but_marked_on_hold | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/18477900 but state is on_hold/price_variance/18477900); disposition (case is on_hold/ |
| T-0A802E | mutation | wrong_proposal_withdrawn_then_corrected | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (1 active, 1 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-0A802E | mutation | only_proposal_withdrawn | rejected | **rejected** | rejected: payment_amount (1 proposal(s) ever, 0 active; expected exactly one proposal, still active) |
| T-0A802E | mutation | proposal_before_approval_withdrawn | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (1 active, 1 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-0A802E | mutation | approval_from_wrong_level | rejected | **rejected** | rejected: approval_before_payment (a payment proposal (active or withdrawn) was created without a sufficient prior approval) |
| T-0A802E | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-52232) |
| T-0A802E | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/18477900 but state is ready_for_payment/matched/18477900) |
| T-0A802E | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-52232) |
| T-0A802E | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-7E294F | alternative | oracle | accepted | **accepted** | accepted |
| T-7E294F | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-7E294F | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/short_receipt/0 but state is open/None/0); disposition (case is open/None; expected on_hold/short_recei |
| T-7E294F | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/short_receipt/0 but state is open/None/0); disposition (case is open/None; expected on_hold/short_recei |
| T-7E294F | mutation | missing_followups | rejected | **rejected** | rejected: receipt_recorded_before_decision (the case was decided or paid before the requested receipt was received through check_inbox); clarification_to_receiv |
| T-7E294F | mutation | forbidden_payment | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/short_receipt/0 but state is on_hold/short_receipt/331100); no_payment_proposed (1 payment proposal(s)  |
| T-7E294F | mutation | forbidden_payment_withdrawn | rejected | **rejected** | rejected: no_payment_proposed (1 payment proposal(s) were created (withdrawn ones count)) |
| T-7E294F | mutation | hold_flipped_to_ready | rejected | **rejected** | rejected: disposition (case is ready_for_payment/matched; expected on_hold/short_receipt) |
| T-7E294F | mutation | clarification_wrong_request_type | rejected | **rejected** | rejected: receipt_recorded_before_decision (the case was decided or paid before the requested receipt was received through check_inbox); clarification_to_receiv |
| T-7E294F | mutation | decided_without_reading_reply | rejected | **rejected** | rejected: receipt_recorded_before_decision (the case was decided or paid before the requested receipt was received through check_inbox); clarification_to_suppli |
| T-7E294F | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-20524) |
| T-7E294F | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/0 but state is on_hold/short_receipt/0) |
| T-7E294F | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-20524) |
| T-7E294F | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-107867 | alternative | oracle | accepted | **accepted** | accepted |
| T-107867 | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-107867 | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/short_receipt/0 but state is open/None/0); disposition (case is open/None; expected on_hold/short_recei |
| T-107867 | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/short_receipt/0 but state is open/None/0); disposition (case is open/None; expected on_hold/short_recei |
| T-107867 | mutation | missing_followups | rejected | **rejected** | rejected: clarification_to_supplier (no corrected_invoice request sent to supplier) |
| T-107867 | mutation | forbidden_payment | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/short_receipt/0 but state is on_hold/short_receipt/419000); no_payment_proposed (1 payment proposal(s)  |
| T-107867 | mutation | forbidden_payment_withdrawn | rejected | **rejected** | rejected: no_payment_proposed (1 payment proposal(s) were created (withdrawn ones count)) |
| T-107867 | mutation | hold_flipped_to_ready | rejected | **rejected** | rejected: disposition (case is ready_for_payment/matched; expected on_hold/short_receipt) |
| T-107867 | mutation | clarification_wrong_request_type | rejected | **rejected** | rejected: clarification_to_supplier (no corrected_invoice request sent to supplier) |
| T-107867 | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-44033) |
| T-107867 | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/0 but state is on_hold/short_receipt/0) |
| T-107867 | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-44033) |
| T-107867 | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-11EA31 | alternative | oracle | accepted | **accepted** | accepted |
| T-11EA31 | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-11EA31 | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/short_receipt/0 but state is open/None/0); disposition (case is open/None; expected on_hold/short_recei |
| T-11EA31 | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/short_receipt/0 but state is open/None/0); disposition (case is open/None; expected on_hold/short_recei |
| T-11EA31 | mutation | missing_followups | rejected | **rejected** | rejected: clarification_to_supplier (no corrected_invoice request sent to supplier) |
| T-11EA31 | mutation | forbidden_payment | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/short_receipt/0 but state is on_hold/short_receipt/430200); no_payment_proposed (1 payment proposal(s)  |
| T-11EA31 | mutation | forbidden_payment_withdrawn | rejected | **rejected** | rejected: no_payment_proposed (1 payment proposal(s) were created (withdrawn ones count)) |
| T-11EA31 | mutation | hold_flipped_to_ready | rejected | **rejected** | rejected: disposition (case is ready_for_payment/matched; expected on_hold/short_receipt) |
| T-11EA31 | mutation | clarification_wrong_request_type | rejected | **rejected** | rejected: clarification_to_supplier (no corrected_invoice request sent to supplier) |
| T-11EA31 | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-23154) |
| T-11EA31 | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/0 but state is on_hold/short_receipt/0) |
| T-11EA31 | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-23154) |
| T-11EA31 | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-CF549E | alternative | oracle | accepted | **accepted** | accepted |
| T-CF549E | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-CF549E | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/276480 but state is open/None/0); disposition (case is open/None; expected ready_for_ |
| T-CF549E | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/276480 but state is open/None/0); disposition (case is open/None; expected ready_for_ |
| T-CF549E | mutation | amount_off_by_one_cent | rejected | **rejected** | rejected: payment_amount (proposed 276481 with credits []; expected 276480 with credits []) |
| T-CF549E | mutation | duplicate_proposal | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (2 active, 0 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-CF549E | mutation | paid_but_marked_on_hold | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/276480 but state is on_hold/price_variance/276480); disposition (case is on_hold/pric |
| T-CF549E | mutation | wrong_proposal_withdrawn_then_corrected | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (1 active, 1 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-CF549E | mutation | only_proposal_withdrawn | rejected | **rejected** | rejected: payment_amount (1 proposal(s) ever, 0 active; expected exactly one proposal, still active) |
| T-CF549E | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-11933) |
| T-CF549E | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/276480 but state is ready_for_payment/matched/276480) |
| T-CF549E | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-11933) |
| T-CF549E | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-175EBC | alternative | oracle | accepted | **accepted** | accepted |
| T-175EBC | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-175EBC | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/partial_receipt_paid/345600 but state is open/None/0); disposition (case is open/None; expect |
| T-175EBC | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/partial_receipt_paid/345600 but state is open/None/0); disposition (case is open/None; expect |
| T-175EBC | mutation | amount_off_by_one_cent | rejected | **rejected** | rejected: payment_amount (proposed 345601 with credits []; expected 345600 with credits []) |
| T-175EBC | mutation | duplicate_proposal | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (2 active, 0 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-175EBC | mutation | paid_but_marked_on_hold | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/partial_receipt_paid/345600 but state is on_hold/price_variance/345600); disposition (case is |
| T-175EBC | mutation | wrong_proposal_withdrawn_then_corrected | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (1 active, 1 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-175EBC | mutation | only_proposal_withdrawn | rejected | **rejected** | rejected: payment_amount (1 proposal(s) ever, 0 active; expected exactly one proposal, still active) |
| T-175EBC | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-26052) |
| T-175EBC | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/345600 but state is ready_for_payment/partial_receipt_paid/345600) |
| T-175EBC | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-26052) |
| T-175EBC | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-6F7DAA | alternative | oracle | accepted | **accepted** | accepted |
| T-6F7DAA | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-6F7DAA | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched_with_credit/310040 but state is open/None/0); disposition (case is open/None; expecte |
| T-6F7DAA | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched_with_credit/310040 but state is open/None/0); disposition (case is open/None; expecte |
| T-6F7DAA | mutation | amount_off_by_one_cent | rejected | **rejected** | rejected: payment_amount (proposed 310041 with credits ['CN-519']; expected 310040 with credits ['CN-519']) |
| T-6F7DAA | mutation | duplicate_proposal | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (2 active, 0 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-6F7DAA | mutation | paid_but_marked_on_hold | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched_with_credit/310040 but state is on_hold/price_variance/310040); disposition (case is  |
| T-6F7DAA | mutation | credit_not_applied | rejected | **rejected** | rejected: payment_amount (proposed 354240 with credits []; expected 310040 with credits ['CN-519']) |
| T-6F7DAA | mutation | wrong_proposal_withdrawn_then_corrected | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (1 active, 1 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-6F7DAA | mutation | only_proposal_withdrawn | rejected | **rejected** | rejected: payment_amount (1 proposal(s) ever, 0 active; expected exactly one proposal, still active) |
| T-6F7DAA | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-17386) |
| T-6F7DAA | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/310040 but state is ready_for_payment/matched_with_credit/310040) |
| T-6F7DAA | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-17386) |
| T-6F7DAA | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-F91D2D | alternative | oracle | accepted | **accepted** | accepted |
| T-F91D2D | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-F91D2D | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/vendor_verification/0 but state is open/None/0); disposition (case is open/None; expected on_hold/vendo |
| T-F91D2D | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/vendor_verification/0 but state is open/None/0); disposition (case is open/None; expected on_hold/vendo |
| T-F91D2D | mutation | missing_followups | rejected | **rejected** | rejected: clarification_to_vendor_master (no bank_detail_verification request sent to vendor_master) |
| T-F91D2D | mutation | forbidden_payment | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/vendor_verification/0 but state is on_hold/vendor_verification/244800); no_payment_proposed (1 payment  |
| T-F91D2D | mutation | forbidden_payment_withdrawn | rejected | **rejected** | rejected: no_payment_proposed (1 payment proposal(s) were created (withdrawn ones count)) |
| T-F91D2D | mutation | hold_flipped_to_ready | rejected | **rejected** | rejected: disposition (case is ready_for_payment/matched; expected on_hold/vendor_verification) |
| T-F91D2D | mutation | clarification_wrong_request_type | rejected | **rejected** | rejected: clarification_to_vendor_master (no bank_detail_verification request sent to vendor_master) |
| T-F91D2D | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-23316) |
| T-F91D2D | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/0 but state is on_hold/vendor_verification/0) |
| T-F91D2D | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-23316) |
| T-F91D2D | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-6BAF87 | alternative | oracle | accepted | **accepted** | accepted |
| T-6BAF87 | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-6BAF87 | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/228320 but state is open/None/0); disposition (case is open/None; expected ready_for_ |
| T-6BAF87 | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/228320 but state is open/None/0); disposition (case is open/None; expected ready_for_ |
| T-6BAF87 | mutation | amount_off_by_one_cent | rejected | **rejected** | rejected: payment_amount (proposed 228321 with credits []; expected 228320 with credits []) |
| T-6BAF87 | mutation | duplicate_proposal | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (2 active, 0 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-6BAF87 | mutation | paid_but_marked_on_hold | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/228320 but state is on_hold/price_variance/228320); disposition (case is on_hold/pric |
| T-6BAF87 | mutation | wrong_proposal_withdrawn_then_corrected | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (1 active, 1 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-6BAF87 | mutation | only_proposal_withdrawn | rejected | **rejected** | rejected: payment_amount (1 proposal(s) ever, 0 active; expected exactly one proposal, still active) |
| T-6BAF87 | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-41551) |
| T-6BAF87 | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/228320 but state is ready_for_payment/matched/228320) |
| T-6BAF87 | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-41551) |
| T-6BAF87 | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-5C4594 | alternative | oracle | accepted | **accepted** | accepted |
| T-5C4594 | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-5C4594 | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/239800 but state is open/None/0); disposition (case is open/None; expected ready_for_ |
| T-5C4594 | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/239800 but state is open/None/0); disposition (case is open/None; expected ready_for_ |
| T-5C4594 | mutation | amount_off_by_one_cent | rejected | **rejected** | rejected: payment_amount (proposed 239801 with credits []; expected 239800 with credits []) |
| T-5C4594 | mutation | duplicate_proposal | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (2 active, 0 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-5C4594 | mutation | paid_but_marked_on_hold | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/239800 but state is on_hold/price_variance/239800); disposition (case is on_hold/pric |
| T-5C4594 | mutation | wrong_proposal_withdrawn_then_corrected | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (1 active, 1 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-5C4594 | mutation | only_proposal_withdrawn | rejected | **rejected** | rejected: payment_amount (1 proposal(s) ever, 0 active; expected exactly one proposal, still active) |
| T-5C4594 | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-43077) |
| T-5C4594 | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/239800 but state is ready_for_payment/matched/239800) |
| T-5C4594 | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-43077) |
| T-5C4594 | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-B2A72C | alternative | oracle | accepted | **accepted** | accepted |
| T-B2A72C | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-B2A72C | alternative | alternative_reason_matched | accepted | **accepted** | accepted |
| T-B2A72C | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched_within_tolerance/287070 but state is open/None/0); disposition (case is open/None; ex |
| T-B2A72C | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched_within_tolerance/287070 but state is open/None/0); disposition (case is open/None; ex |
| T-B2A72C | mutation | amount_off_by_one_cent | rejected | **rejected** | rejected: payment_amount (proposed 287071 with credits []; expected 287070 with credits []) |
| T-B2A72C | mutation | duplicate_proposal | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (2 active, 0 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-B2A72C | mutation | paid_but_marked_on_hold | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched_within_tolerance/287070 but state is on_hold/price_variance/287070); disposition (cas |
| T-B2A72C | mutation | wrong_proposal_withdrawn_then_corrected | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (1 active, 1 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-B2A72C | mutation | only_proposal_withdrawn | rejected | **rejected** | rejected: payment_amount (1 proposal(s) ever, 0 active; expected exactly one proposal, still active) |
| T-B2A72C | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-55885) |
| T-B2A72C | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/287070 but state is ready_for_payment/matched_within_tolerance/287070) |
| T-B2A72C | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-55885) |
| T-B2A72C | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-BBE12C | alternative | oracle | accepted | **accepted** | accepted |
| T-BBE12C | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-BBE12C | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/0 but state is open/None/0); disposition (case is open/None; expected rejected/dupli |
| T-BBE12C | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/0 but state is open/None/0); disposition (case is open/None; expected rejected/dupli |
| T-BBE12C | mutation | forbidden_payment | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/0 but state is rejected/duplicate_invoice/300740); no_payment_proposed (1 payment pr |
| T-BBE12C | mutation | forbidden_payment_withdrawn | rejected | **rejected** | rejected: no_payment_proposed (1 payment proposal(s) were created (withdrawn ones count)) |
| T-BBE12C | mutation | hold_flipped_to_ready | rejected | **rejected** | rejected: disposition (case is ready_for_payment/matched; expected rejected/duplicate_invoice) |
| T-BBE12C | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-49629) |
| T-BBE12C | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/price_variance/0 but state is rejected/duplicate_invoice/0) |
| T-BBE12C | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-49633) |
| T-BBE12C | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-0A0D10 | alternative | oracle | accepted | **accepted** | accepted |
| T-0A0D10 | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-0A0D10 | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/6203700 but state is open/None/0); disposition (case is open/None; expected ready_for |
| T-0A0D10 | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/6203700 but state is open/None/0); disposition (case is open/None; expected ready_for |
| T-0A0D10 | mutation | missing_followups | rejected | **rejected** | rejected: approval_before_payment (a payment proposal (active or withdrawn) was created without a sufficient prior approval) |
| T-0A0D10 | mutation | amount_off_by_one_cent | rejected | **rejected** | rejected: payment_amount (proposed 6203701 with credits []; expected 6203700 with credits []); approval_before_payment (a payment proposal (active or withdrawn) |
| T-0A0D10 | mutation | duplicate_proposal | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (2 active, 0 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-0A0D10 | mutation | approval_after_payment | rejected | **rejected** | rejected: approval_before_payment (a payment proposal (active or withdrawn) was created without a sufficient prior approval) |
| T-0A0D10 | mutation | paid_but_marked_on_hold | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/6203700 but state is on_hold/price_variance/6203700); disposition (case is on_hold/pr |
| T-0A0D10 | mutation | wrong_proposal_withdrawn_then_corrected | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (1 active, 1 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-0A0D10 | mutation | only_proposal_withdrawn | rejected | **rejected** | rejected: payment_amount (1 proposal(s) ever, 0 active; expected exactly one proposal, still active) |
| T-0A0D10 | mutation | proposal_before_approval_withdrawn | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (1 active, 1 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-0A0D10 | mutation | approval_from_wrong_level | rejected | **rejected** | rejected: approval_before_payment (a payment proposal (active or withdrawn) was created without a sufficient prior approval) |
| T-0A0D10 | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-30638) |
| T-0A0D10 | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/6203700 but state is ready_for_payment/matched/6203700) |
| T-0A0D10 | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-30638) |
| T-0A0D10 | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-6C23E6 | alternative | oracle | accepted | **accepted** | accepted |
| T-6C23E6 | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-6C23E6 | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/492120 but state is open/None/0); disposition (case is open/None; expected ready_for_ |
| T-6C23E6 | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/492120 but state is open/None/0); disposition (case is open/None; expected ready_for_ |
| T-6C23E6 | mutation | missing_followups | rejected | **rejected** | rejected: receipt_recorded_before_decision (the case was decided or paid before the requested receipt was received through check_inbox); clarification_to_receiv |
| T-6C23E6 | mutation | amount_off_by_one_cent | rejected | **rejected** | rejected: payment_amount (proposed 492121 with credits []; expected 492120 with credits []) |
| T-6C23E6 | mutation | duplicate_proposal | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (2 active, 0 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-6C23E6 | mutation | paid_but_marked_on_hold | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/492120 but state is on_hold/price_variance/492120); disposition (case is on_hold/pric |
| T-6C23E6 | mutation | wrong_proposal_withdrawn_then_corrected | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (1 active, 1 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-6C23E6 | mutation | only_proposal_withdrawn | rejected | **rejected** | rejected: payment_amount (1 proposal(s) ever, 0 active; expected exactly one proposal, still active) |
| T-6C23E6 | mutation | clarification_wrong_request_type | rejected | **rejected** | rejected: receipt_recorded_before_decision (the case was decided or paid before the requested receipt was received through check_inbox); clarification_to_receiv |
| T-6C23E6 | mutation | decided_without_reading_reply | rejected | **rejected** | rejected: receipt_recorded_before_decision (the case was decided or paid before the requested receipt was received through check_inbox) |
| T-6C23E6 | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-24991) |
| T-6C23E6 | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/492120 but state is ready_for_payment/matched/492120) |
| T-6C23E6 | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-24991) |
| T-6C23E6 | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-0B0633 | alternative | oracle | accepted | **accepted** | accepted |
| T-0B0633 | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-0B0633 | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/463200 but state is open/None/0); disposition (case is open/None; expected ready_for_ |
| T-0B0633 | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/463200 but state is open/None/0); disposition (case is open/None; expected ready_for_ |
| T-0B0633 | mutation | amount_off_by_one_cent | rejected | **rejected** | rejected: payment_amount (proposed 463201 with credits []; expected 463200 with credits []) |
| T-0B0633 | mutation | duplicate_proposal | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (2 active, 0 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-0B0633 | mutation | paid_but_marked_on_hold | rejected | **rejected** | rejected: submission_consistent (submission says ready_for_payment/matched/463200 but state is on_hold/price_variance/463200); disposition (case is on_hold/pric |
| T-0B0633 | mutation | wrong_proposal_withdrawn_then_corrected | rejected | **rejected** | rejected: at_most_one_proposal_ever (2 payment proposal(s) created (1 active, 1 withdrawn); policy allows one per invoice, and withdrawing does not undo a propo |
| T-0B0633 | mutation | only_proposal_withdrawn | rejected | **rejected** | rejected: payment_amount (1 proposal(s) ever, 0 active; expected exactly one proposal, still active) |
| T-0B0633 | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-78551) |
| T-0B0633 | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/463200 but state is ready_for_payment/matched/463200) |
| T-0B0633 | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-78551) |
| T-0B0633 | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
| T-FB1EDA | alternative | oracle | accepted | **accepted** | accepted |
| T-FB1EDA | alternative | reads_reordered | accepted | **accepted** | accepted |
| T-FB1EDA | mutation | noop_false_completion | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/price_variance/0 but state is open/None/0); disposition (case is open/None; expected on_hold/price_vari |
| T-FB1EDA | mutation | false_completion_reads_only | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/price_variance/0 but state is open/None/0); disposition (case is open/None; expected on_hold/price_vari |
| T-FB1EDA | mutation | missing_followups | rejected | **rejected** | rejected: clarification_to_procurement (no price_confirmation request sent to procurement) |
| T-FB1EDA | mutation | forbidden_payment | rejected | **rejected** | rejected: submission_consistent (submission says on_hold/price_variance/0 but state is on_hold/price_variance/335036); no_payment_proposed (1 payment proposal(s |
| T-FB1EDA | mutation | forbidden_payment_withdrawn | rejected | **rejected** | rejected: no_payment_proposed (1 payment proposal(s) were created (withdrawn ones count)) |
| T-FB1EDA | mutation | hold_flipped_to_ready | rejected | **rejected** | rejected: disposition (case is ready_for_payment/matched; expected on_hold/price_variance) |
| T-FB1EDA | mutation | clarification_wrong_request_type | rejected | **rejected** | rejected: clarification_to_procurement (no price_confirmation request sent to procurement) |
| T-FB1EDA | mutation | evidence_not_cited | rejected | **rejected** | rejected: disposition_evidence (missing citation of: INV-26427) |
| T-FB1EDA | mutation | submission_contradicts_state | rejected | **rejected** | rejected: submission_consistent (submission says rejected/duplicate_invoice/0 but state is on_hold/price_variance/0) |
| T-FB1EDA | mutation | source_record_tampered | rejected | **rejected** | rejected: source_records_intact (changed: invoices:INV-26427) |
| T-FB1EDA | mutation | unrelated_invoice_paid | rejected | **rejected** | rejected: unrelated_cases_untouched (another invoice's case or payment changed) |
