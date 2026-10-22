"""Agent-facing tool definitions: argument models, descriptions, and JSON schemas.

These definitions are the single source for every adapter (TRL, OpenEnv, the OpenAI-style
runner, and the human play CLI), so every kind of agent sees exactly the same tools.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt

from invoiceops.domain.records import ALLOWED_REASONS

Collection = Literal[
    "invoices", "purchase_orders", "receipts", "vendors", "documents", "credit_notes", "payments"
]
StatusArg = Literal["ready_for_payment", "on_hold", "rejected"]
ReasonArg = Literal[
    "matched",
    "matched_within_tolerance",
    "matched_with_credit",
    "partial_receipt_paid",
    "short_receipt",
    "price_variance",
    "missing_receipt",
    "quantity_exceeds_receipt",
    "vendor_verification",
    "awaiting_approval",
    "duplicate_invoice",
]
IdList = Annotated[list[Annotated[str, Field(min_length=1, max_length=64)]], Field(max_length=20)]
Key = Annotated[str, Field(min_length=1, max_length=64)]


class Args(BaseModel):
    model_config = ConfigDict(extra="forbid")


class NoArgs(Args):
    pass


class SearchArgs(Args):
    collection: Collection = Field(description="Which kind of record to search.")
    query: str = Field(
        default="",
        max_length=200,
        description="Case-insensitive text to match against record ids, names, titles and "
        "numbers. Empty returns everything in the collection.",
    )
    cursor: str | None = Field(
        default=None, description="Value of next_cursor from a previous page."
    )


class InvoiceIdArgs(Args):
    invoice_id: str = Field(description="AP system invoice id, e.g. INV-12345.")


class PurchaseOrderArgs(Args):
    po_id: str = Field(description="Purchase order id.")
    revision: StrictInt | None = Field(
        default=None, description="Specific revision number; omit for the latest revision."
    )


class PoIdArgs(Args):
    po_id: str = Field(description="Purchase order id.")


class VendorIdArgs(Args):
    vendor_id: str = Field(description="Supplier id from the supplier master.")


class DocumentIdArgs(Args):
    document_id: str = Field(description="Document id (policy, message, attachment, memo).")


class HistoryArgs(Args):
    vendor_id: str = Field(description="Supplier id.")
    po_id: str | None = Field(default=None, description="Optional PO id to narrow the history.")


class DispositionArgs(Args):
    invoice_id: str = Field(description="Invoice in your queue.")
    status: StatusArg = Field(description="New case status.")
    reason_code: ReasonArg = Field(description="Reason code allowed for that status (see policy).")
    evidence_ids: IdList = Field(
        min_length=1, description="Ids of records supporting the decision."
    )
    expected_version: StrictInt = Field(
        description="The case version you last read (optimistic lock)."
    )
    note: str = Field(default="", max_length=1000, description="Optional short note.")


class ClarificationArgs(Args):
    invoice_id: str = Field(description="Invoice the question is about.")
    recipient_role: str = Field(
        description="Role id to ask, e.g. supplier, procurement, receiving."
    )
    question: str = Field(
        min_length=1, max_length=2000, description="What you need them to do or confirm."
    )
    evidence_ids: IdList = Field(
        min_length=1, description="The invoice and the records showing the problem."
    )
    idempotency_key: Key = Field(
        description="Unique key for this request; reuse it only when retrying."
    )


class ApprovalArgs(Args):
    invoice_id: str = Field(description="Invoice to be paid.")
    approver_role: str = Field(description="Role id of the approver.")
    amount_minor: StrictInt = Field(gt=0, description="Payment amount to approve, in cents.")
    evidence_ids: IdList = Field(min_length=1, description="Records supporting the payment.")
    idempotency_key: Key = Field(
        description="Unique key for this request; reuse it only when retrying."
    )


class ProposePaymentArgs(Args):
    invoice_id: str = Field(description="Invoice to pay.")
    amount_minor: StrictInt = Field(
        gt=0, description="Amount to pay, in cents, after any credit notes."
    )
    credit_note_ids: IdList = Field(
        default_factory=list, description="Credit notes deducted, if any."
    )
    evidence_ids: IdList = Field(min_length=1, description="Records supporting the payment.")
    idempotency_key: Key = Field(
        description="Unique key for this proposal; reuse it only when retrying."
    )


class WithdrawArgs(Args):
    proposal_id: str = Field(description="Payment proposal id.")
    reason: str = Field(min_length=1, max_length=500, description="Why it is withdrawn.")


class SubmitArgs(Args):
    invoice_id: str = Field(description="Invoice whose case you are closing.")
    status: StatusArg = Field(description="Final case status.")
    reason_code: ReasonArg = Field(description="Final reason code.")
    amount_proposed_minor: StrictInt = Field(
        ge=0,
        description="Total of active payment proposals for this invoice, in cents (0 if none).",
    )
    evidence_ids: IdList = Field(min_length=1, description="Key records behind the decision.")
    summary: str = Field(
        min_length=1, max_length=2000, description="Short summary of what you did."
    )


class ToolSpec(BaseModel):
    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    name: str
    description: str
    args: type[Args]
    writes: bool


_REASONS = "; ".join(
    f"{status.value}: " + ", ".join(sorted(code.value for code in codes))
    for status, codes in ALLOWED_REASONS.items()
)

TOOLS: tuple[ToolSpec, ...] = (
    ToolSpec(
        name="list_queue",
        description="List the invoices assigned to you, with their case status and version.",
        args=NoArgs,
        writes=False,
    ),
    ToolSpec(
        name="search_records",
        description="Search records of one kind. Results are sorted by id, 10 per page.",
        args=SearchArgs,
        writes=False,
    ),
    ToolSpec(
        name="get_invoice",
        description="Read an invoice: header, lines, bank account on the invoice, attachments, "
        "and (for invoices in your queue) the AP case status and version.",
        args=InvoiceIdArgs,
        writes=False,
    ),
    ToolSpec(
        name="get_purchase_order",
        description="Read a purchase order (latest revision unless one is given) and the list "
        "of its revisions.",
        args=PurchaseOrderArgs,
        writes=False,
    ),
    ToolSpec(
        name="get_receipts",
        description="Read all goods receipts recorded against a purchase order.",
        args=PoIdArgs,
        writes=False,
    ),
    ToolSpec(
        name="get_vendor",
        description="Read a supplier master record, including the bank account on file and "
        "whether the supplier is verified.",
        args=VendorIdArgs,
        writes=False,
    ),
    ToolSpec(
        name="get_document",
        description="Read a document: a policy, supplier message, attachment, or internal memo.",
        args=DocumentIdArgs,
        writes=False,
    ),
    ToolSpec(
        name="get_history",
        description="A supplier's invoices (with quantities billed and payment status), past "
        "payments, and credit notes, optionally limited to one PO.",
        args=HistoryArgs,
        writes=False,
    ),
    ToolSpec(
        name="set_disposition",
        description="Record the decision on an invoice case. Allowed status and reason codes: "
        + _REASONS
        + ". Fails with stale_version if expected_version is not the current version.",
        args=DispositionArgs,
        writes=True,
    ),
    ToolSpec(
        name="create_clarification",
        description="Send a question to a role (supplier, procurement, receiving, vendor_master, "
        "...). Replies, if any, arrive through check_inbox.",
        args=ClarificationArgs,
        writes=True,
    ),
    ToolSpec(
        name="request_approval",
        description="Ask an approver to approve a payment amount. The decision arrives through "
        "check_inbox. You cannot approve payments yourself.",
        args=ApprovalArgs,
        writes=True,
    ),
    ToolSpec(
        name="check_inbox",
        description="Receive new replies and approval decisions addressed to you.",
        args=NoArgs,
        writes=True,
    ),
    ToolSpec(
        name="propose_payment",
        description="Propose a payment for the next payment run. Moves no money. Retrying with "
        "the same idempotency key never creates a second proposal.",
        args=ProposePaymentArgs,
        writes=True,
    ),
    ToolSpec(
        name="withdraw_payment_proposal",
        description="Withdraw an active payment proposal. The proposal stays in the history.",
        args=WithdrawArgs,
        writes=True,
    ),
    ToolSpec(
        name="submit_case",
        description="Close your work on the invoice and end the task. State what is now true "
        "in the system.",
        args=SubmitArgs,
        writes=True,
    ),
)

TOOLS_BY_NAME: dict[str, ToolSpec] = {tool.name: tool for tool in TOOLS}


def _strip_titles(node: Any) -> Any:
    if isinstance(node, dict):
        return {k: _strip_titles(v) for k, v in node.items() if k != "title"}
    if isinstance(node, list):
        return [_strip_titles(v) for v in node]
    return node


def parameters_schema(tool: ToolSpec) -> dict[str, Any]:
    schema = _strip_titles(tool.args.model_json_schema())
    schema.setdefault("properties", {})
    schema["additionalProperties"] = False
    return dict(schema)


def openai_tools() -> list[dict[str, Any]]:
    """Tool definitions in the OpenAI chat-completions format (also used by vLLM)."""
    return [
        {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": parameters_schema(tool),
            },
        }
        for tool in TOOLS
    ]
