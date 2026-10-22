"""Source records of a fictional company, and the closed vocabularies the agent works with.

Source records are immutable from the agent's point of view. Amounts and quantities are
strict ``int`` fields (floats and numeric strings are rejected) and dates are ISO
``YYYY-MM-DD`` strings, which compare correctly as plain strings.
"""

from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictInt,
    model_validator,
)

from invoiceops.domain.money import line_total


def _check_iso_date(value: str) -> str:
    if len(value) != 10 or date.fromisoformat(value).isoformat() != value:
        raise ValueError(f"expected an ISO date YYYY-MM-DD, got {value!r}")
    return value


IsoDate = Annotated[str, AfterValidator(_check_iso_date)]
RecordId = Annotated[str, Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")]
Minor = Annotated[StrictInt, Field(ge=0)]
PositiveQty = Annotated[StrictInt, Field(gt=0)]


class Record(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class CaseStatus(StrEnum):
    OPEN = "open"
    READY_FOR_PAYMENT = "ready_for_payment"
    ON_HOLD = "on_hold"
    REJECTED = "rejected"


class ReasonCode(StrEnum):
    MATCHED = "matched"
    MATCHED_WITHIN_TOLERANCE = "matched_within_tolerance"
    MATCHED_WITH_CREDIT = "matched_with_credit"
    PARTIAL_RECEIPT_PAID = "partial_receipt_paid"
    SHORT_RECEIPT = "short_receipt"
    PRICE_VARIANCE = "price_variance"
    MISSING_RECEIPT = "missing_receipt"
    QUANTITY_EXCEEDS_RECEIPT = "quantity_exceeds_receipt"
    VENDOR_VERIFICATION = "vendor_verification"
    AWAITING_APPROVAL = "awaiting_approval"
    DUPLICATE_INVOICE = "duplicate_invoice"


ALLOWED_REASONS: dict[CaseStatus, frozenset[ReasonCode]] = {
    CaseStatus.READY_FOR_PAYMENT: frozenset(
        {
            ReasonCode.MATCHED,
            ReasonCode.MATCHED_WITHIN_TOLERANCE,
            ReasonCode.MATCHED_WITH_CREDIT,
            ReasonCode.PARTIAL_RECEIPT_PAID,
        }
    ),
    CaseStatus.ON_HOLD: frozenset(
        {
            ReasonCode.SHORT_RECEIPT,
            ReasonCode.PRICE_VARIANCE,
            ReasonCode.MISSING_RECEIPT,
            ReasonCode.QUANTITY_EXCEEDS_RECEIPT,
            ReasonCode.VENDOR_VERIFICATION,
            ReasonCode.AWAITING_APPROVAL,
        }
    ),
    CaseStatus.REJECTED: frozenset({ReasonCode.DUPLICATE_INVOICE}),
}


class PartialInvoiceRule(StrEnum):
    REQUIRE_CORRECTED_INVOICE = "require_corrected_invoice"
    PAY_RECEIVED_PORTION = "pay_received_portion"


class Company(Record):
    id: RecordId
    name: str
    currency: Literal["USD"]
    as_of: IsoDate


class Role(Record):
    """An internal or external party the agent can address."""

    id: RecordId
    name: str
    kind: Literal["internal", "external"]
    can_approve: StrictBool
    approval_limit_minor: Minor = 0
    description: str


class PolicyParams(Record):
    price_tolerance_bps: Annotated[StrictInt, Field(ge=0, le=2_000)]
    price_tolerance_cap_minor: Minor
    partial_invoice_rule: PartialInvoiceRule
    self_approval_limit_minor: Minor
    """Payments up to this amount need no approval; larger payments need an approver."""


class PolicyVersion(Record):
    id: RecordId
    version: Annotated[StrictInt, Field(ge=1)]
    effective_from: IsoDate
    effective_to: IsoDate | None = None
    params: PolicyParams
    document_id: RecordId


class Vendor(Record):
    id: RecordId
    legal_name: str
    tax_id: str
    remit_account: str
    verified: StrictBool
    contact_email: str


class POLine(Record):
    line_no: Annotated[StrictInt, Field(ge=1)]
    sku: str
    description: str
    quantity: PositiveQty
    unit_price_minor: Minor


class PurchaseOrder(Record):
    id: RecordId
    revision: Annotated[StrictInt, Field(ge=1)]
    vendor_id: RecordId
    department: str
    approved_on: IsoDate
    lines: tuple[POLine, ...]

    @model_validator(mode="after")
    def _unique_lines(self) -> PurchaseOrder:
        numbers = [line.line_no for line in self.lines]
        if not numbers or len(set(numbers)) != len(numbers):
            raise ValueError(f"purchase order {self.id} needs unique, non-empty line numbers")
        return self

    @property
    def total_minor(self) -> int:
        return sum(line_total(line.quantity, line.unit_price_minor) for line in self.lines)


class ReceiptLine(Record):
    po_line_no: Annotated[StrictInt, Field(ge=1)]
    quantity: PositiveQty


class GoodsReceipt(Record):
    id: RecordId
    po_id: RecordId
    received_on: IsoDate
    lines: tuple[ReceiptLine, ...]


class InvoiceLine(Record):
    po_line_no: Annotated[StrictInt, Field(ge=1)]
    description: str
    quantity: PositiveQty
    unit_price_minor: Minor


class Invoice(Record):
    id: RecordId
    vendor_id: RecordId
    vendor_invoice_number: str
    po_id: RecordId
    invoice_date: IsoDate
    received_on: IsoDate
    remit_account: str
    currency: Literal["USD"]
    lines: tuple[InvoiceLine, ...]
    total_minor: Minor
    attachment_ids: tuple[RecordId, ...] = ()

    @model_validator(mode="after")
    def _total_matches_lines(self) -> Invoice:
        expected = sum(line_total(line.quantity, line.unit_price_minor) for line in self.lines)
        if not self.lines or expected != self.total_minor:
            raise ValueError(
                f"invoice {self.id} total {self.total_minor} does not equal its lines ({expected})"
            )
        return self


class CreditNote(Record):
    id: RecordId
    vendor_id: RecordId
    invoice_id: RecordId
    amount_minor: Annotated[StrictInt, Field(gt=0)]
    issued_on: IsoDate
    status: Literal["open", "applied"]
    applied_to_payment_id: RecordId | None = None

    @model_validator(mode="after")
    def _applied_has_payment(self) -> CreditNote:
        if (self.status == "applied") != (self.applied_to_payment_id is not None):
            raise ValueError(f"credit note {self.id}: applied status and payment link disagree")
        return self


class PaymentRecord(Record):
    """A payment made or scheduled before the episode started."""

    id: RecordId
    invoice_id: RecordId
    vendor_id: RecordId
    amount_minor: Annotated[StrictInt, Field(gt=0)]
    status: Literal["paid", "scheduled"]
    paid_on: IsoDate
    credit_note_ids: tuple[RecordId, ...] = ()


class Document(Record):
    id: RecordId
    kind: Literal["policy", "supplier_message", "attachment", "internal_memo"]
    title: str
    body: str
    source: str
    received_on: IsoDate
