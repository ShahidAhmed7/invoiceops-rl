"""The tools as typed, documented Python methods.

TRL (``environment_factory``) and FastMCP (OpenEnv's ``MCPEnvironment``) both build a tool's
JSON schema from a function's type hints and Google-style docstring. This mixin defines that
surface once; every method forwards to ``Episode.step`` and returns the observation as a JSON
string. A test checks that these signatures match ``invoiceops.tools.spec``.
"""

from __future__ import annotations

import json
from typing import Any


class ToolMethods:
    """Mixin: subclasses implement ``_dispatch(tool, arguments) -> dict``."""

    def _dispatch(self, tool: str, arguments: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    def _run(self, tool: str, **arguments: Any) -> str:
        clean = {k: v for k, v in arguments.items() if v is not None}
        return json.dumps(self._dispatch(tool, clean), ensure_ascii=False)

    def list_queue(self) -> str:
        """List the invoices assigned to you, with their case status and version.

        Returns:
            JSON with the queued invoices.
        """
        return self._run("list_queue")

    def search_records(self, collection: str, query: str = "", cursor: str | None = None) -> str:
        """Search records of one kind. Results are sorted by id, 10 per page.

        Args:
            collection: One of invoices, purchase_orders, receipts, vendors, documents, credit_notes, payments.
            query: Case-insensitive text to match against ids, names, titles and numbers. Empty returns everything.
            cursor: The next_cursor value from a previous page, to get the next page.

        Returns:
            JSON with matching record summaries and next_cursor.
        """
        return self._run("search_records", collection=collection, query=query, cursor=cursor)

    def get_invoice(self, invoice_id: str) -> str:
        """Read an invoice: header, lines, bank account on the invoice, attachments, and (for invoices in your queue) the AP case status and version.

        Args:
            invoice_id: AP system invoice id, e.g. INV-12345.

        Returns:
            JSON with the invoice.
        """
        return self._run("get_invoice", invoice_id=invoice_id)

    def get_purchase_order(self, po_id: str, revision: int | None = None) -> str:
        """Read a purchase order (latest revision unless one is given) and the list of its revisions.

        Args:
            po_id: Purchase order id.
            revision: Specific revision number; omit for the latest revision.

        Returns:
            JSON with the purchase order.
        """
        return self._run("get_purchase_order", po_id=po_id, revision=revision)

    def get_receipts(self, po_id: str) -> str:
        """Read all goods receipts recorded against a purchase order.

        Args:
            po_id: Purchase order id.

        Returns:
            JSON with the receipts.
        """
        return self._run("get_receipts", po_id=po_id)

    def get_vendor(self, vendor_id: str) -> str:
        """Read a supplier master record, including the bank account on file and whether the supplier is verified.

        Args:
            vendor_id: Supplier id from the supplier master.

        Returns:
            JSON with the supplier record.
        """
        return self._run("get_vendor", vendor_id=vendor_id)

    def get_document(self, document_id: str) -> str:
        """Read a document: a policy, supplier message, attachment, or internal memo.

        Args:
            document_id: Document id.

        Returns:
            JSON with the document.
        """
        return self._run("get_document", document_id=document_id)

    def get_history(self, vendor_id: str, po_id: str | None = None) -> str:
        """A supplier's invoices (with quantities billed and payment status), past payments, and credit notes, optionally limited to one PO.

        Args:
            vendor_id: Supplier id.
            po_id: Optional PO id to narrow the history.

        Returns:
            JSON with invoices, payments and credit notes.
        """
        return self._run("get_history", vendor_id=vendor_id, po_id=po_id)

    def set_disposition(
        self,
        invoice_id: str,
        status: str,
        reason_code: str,
        evidence_ids: list[str],
        expected_version: int,
        note: str = "",
    ) -> str:
        """Record the decision on an invoice case. Fails with stale_version if expected_version is not the current version.

        Args:
            invoice_id: Invoice in your queue.
            status: ready_for_payment, on_hold, or rejected.
            reason_code: For ready_for_payment: matched, matched_within_tolerance, matched_with_credit, partial_receipt_paid. For on_hold: short_receipt, price_variance, missing_receipt, quantity_exceeds_receipt, vendor_verification, awaiting_approval. For rejected: duplicate_invoice.
            evidence_ids: Ids of records supporting the decision.
            expected_version: The case version you last read.
            note: Optional short note.

        Returns:
            JSON with the updated case.
        """
        return self._run(
            "set_disposition",
            invoice_id=invoice_id,
            status=status,
            reason_code=reason_code,
            evidence_ids=evidence_ids,
            expected_version=expected_version,
            note=note,
        )

    def create_clarification(
        self,
        invoice_id: str,
        recipient_role: str,
        request_type: str,
        evidence_ids: list[str],
        idempotency_key: str,
    ) -> str:
        """Send a structured request to a role (supplier, procurement, receiving, vendor_master). The recipient acts on the request type; replies, if any, arrive through check_inbox.

        Args:
            invoice_id: Invoice the request is about.
            recipient_role: Role id to ask, e.g. supplier, procurement, receiving, vendor_master.
            request_type: What you are asking for: corrected_invoice (supplier issues a corrected invoice), price_confirmation (procurement confirms the price or amends the PO), receipt_confirmation (receiving confirms and records the goods receipt), bank_detail_verification (vendor master verifies the supplier's bank details).
            evidence_ids: The invoice and the records showing the problem.
            idempotency_key: Unique key for this request; reuse it only when retrying.

        Returns:
            JSON with the clarification id and the message sent.
        """
        return self._run(
            "create_clarification",
            invoice_id=invoice_id,
            recipient_role=recipient_role,
            request_type=request_type,
            evidence_ids=evidence_ids,
            idempotency_key=idempotency_key,
        )

    def request_approval(
        self,
        invoice_id: str,
        approver_role: str,
        amount_minor: int,
        evidence_ids: list[str],
        idempotency_key: str,
    ) -> str:
        """Ask an approver to approve a payment amount. The decision arrives through check_inbox. You cannot approve payments yourself.

        Args:
            invoice_id: Invoice to be paid.
            approver_role: Role id of the approver.
            amount_minor: Payment amount to approve, in cents.
            evidence_ids: Records supporting the payment.
            idempotency_key: Unique key for this request; reuse it only when retrying.

        Returns:
            JSON with the approval request id.
        """
        return self._run(
            "request_approval",
            invoice_id=invoice_id,
            approver_role=approver_role,
            amount_minor=amount_minor,
            evidence_ids=evidence_ids,
            idempotency_key=idempotency_key,
        )

    def check_inbox(self) -> str:
        """Receive new replies and approval decisions addressed to you.

        Returns:
            JSON with new messages.
        """
        return self._run("check_inbox")

    def propose_payment(
        self,
        invoice_id: str,
        amount_minor: int,
        evidence_ids: list[str],
        idempotency_key: str,
        credit_note_ids: list[str] | None = None,
    ) -> str:
        """Propose a payment for the next payment run. Moves no money. Retrying with the same idempotency key never creates a second proposal.

        Args:
            invoice_id: Invoice to pay.
            amount_minor: Amount to pay, in cents, after any credit notes.
            evidence_ids: Records supporting the payment.
            idempotency_key: Unique key for this proposal; reuse it only when retrying.
            credit_note_ids: Credit notes deducted, if any.

        Returns:
            JSON with the proposal id.
        """
        return self._run(
            "propose_payment",
            invoice_id=invoice_id,
            amount_minor=amount_minor,
            credit_note_ids=credit_note_ids or [],
            evidence_ids=evidence_ids,
            idempotency_key=idempotency_key,
        )

    def withdraw_payment_proposal(self, proposal_id: str, reason: str) -> str:
        """Withdraw an active payment proposal. The proposal stays in the history.

        Args:
            proposal_id: Payment proposal id.
            reason: Why it is withdrawn.

        Returns:
            JSON with the proposal status.
        """
        return self._run("withdraw_payment_proposal", proposal_id=proposal_id, reason=reason)

    def submit_case(
        self,
        invoice_id: str,
        status: str,
        reason_code: str,
        amount_proposed_minor: int,
        evidence_ids: list[str],
        summary: str,
    ) -> str:
        """Close your work on the invoice and end the task. State what is now true in the system.

        Args:
            invoice_id: Invoice whose case you are closing.
            status: Final case status: ready_for_payment, on_hold, or rejected.
            reason_code: Final reason code.
            amount_proposed_minor: Total of active payment proposals for this invoice, in cents (0 if none).
            evidence_ids: Key records behind the decision.
            summary: Short summary of what you did.

        Returns:
            JSON confirming the submission.
        """
        return self._run(
            "submit_case",
            invoice_id=invoice_id,
            status=status,
            reason_code=reason_code,
            amount_proposed_minor=amount_proposed_minor,
            evidence_ids=evidence_ids,
            summary=summary,
        )


TOOL_METHOD_NAMES: tuple[str, ...] = tuple(
    name
    for name in vars(ToolMethods)
    if not name.startswith("_") and callable(vars(ToolMethods)[name])
)
