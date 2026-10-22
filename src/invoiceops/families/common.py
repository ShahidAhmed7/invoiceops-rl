"""Shared helpers for building task scenarios and their expected outcomes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from invoiceops.domain.money import apply_bps, line_total
from invoiceops.domain.records import (
    CaseStatus,
    GoodsReceipt,
    Invoice,
    PartialInvoiceRule,
    PolicyParams,
    PurchaseOrder,
    ReasonCode,
)
from invoiceops.tasks.model import (
    CiteGroups,
    ClarificationRequirement,
    Outcome,
    PaymentExpectation,
)
from invoiceops.worlds.builder import ScenarioBuilder, shift

Difficulty = Literal["introductory", "intermediate", "advanced"]


@dataclass
class Scenario:
    invoice: Invoice
    outcomes: list[Outcome]
    rationale: str
    difficulty: Difficulty
    hint: str = ""
    extra: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Dates:
    approved: str
    received: str
    invoiced: str


def standard_dates(b: ScenarioBuilder) -> Dates:
    approved = shift(b.as_of, -b.rng.randrange(40, 55))
    received = shift(approved, b.rng.randrange(8, 15))
    invoiced = shift(received, b.rng.randrange(1, 4))
    return Dates(approved=approved, received=received, invoiced=invoiced)


def quantity_for(
    b: ScenarioBuilder, unit_price_minor: int, low: int = 150_000, high: int = 550_000
) -> int:
    """A quantity whose line value falls between ``low`` and ``high`` minor units."""
    target = b.rng.randrange(low, high)
    return max(2, target // unit_price_minor)


def tolerance_limit(params: PolicyParams, po_value_minor: int) -> int:
    return min(
        apply_bps(po_value_minor, params.price_tolerance_bps), params.price_tolerance_cap_minor
    )


def needs_approval(params: PolicyParams, amount_minor: int) -> bool:
    return amount_minor > params.self_approval_limit_minor


def pay(
    params: PolicyParams,
    invoice: Invoice,
    amount_minor: int,
    reasons: tuple[ReasonCode, ...],
    credit_note_ids: tuple[str, ...] = (),
    clarifications: tuple[ClarificationRequirement, ...] = (),
    label: str = "pay",
) -> Outcome:
    return Outcome(
        label=label,
        status=CaseStatus.READY_FOR_PAYMENT,
        reason_codes=reasons,
        payment=PaymentExpectation(amount_minor=amount_minor, credit_note_ids=credit_note_ids),
        clarifications=clarifications,
        approval_required=needs_approval(params, amount_minor),
        evidence=((invoice.id,),),
    )


def hold(
    invoice: Invoice,
    reasons: tuple[ReasonCode, ...],
    clarifications: tuple[ClarificationRequirement, ...],
    evidence: CiteGroups | None = None,
    label: str = "hold",
) -> Outcome:
    return Outcome(
        label=label,
        status=CaseStatus.ON_HOLD,
        reason_codes=reasons,
        payment=None,
        clarifications=clarifications,
        evidence=evidence if evidence is not None else ((invoice.id,),),
    )


def ask(roles: tuple[str, ...] | str, *cite: tuple[str, ...]) -> ClarificationRequirement:
    return ClarificationRequirement(
        recipient_roles=(roles,) if isinstance(roles, str) else roles, cite=tuple(cite)
    )


def quantity_outcome(
    params: PolicyParams,
    invoice: Invoice,
    po: PurchaseOrder,
    available: dict[int, int],
    cite: tuple[str, ...],
    prior_billing: bool,
    extra_clarifications: tuple[ClarificationRequirement, ...] = (),
) -> Outcome:
    """Expected outcome when an invoice bills more than is available (policy section 4)."""
    reasons = (
        (ReasonCode.QUANTITY_EXCEEDS_RECEIPT, ReasonCode.SHORT_RECEIPT)
        if prior_billing
        else (ReasonCode.SHORT_RECEIPT,)
    )
    if params.partial_invoice_rule is PartialInvoiceRule.REQUIRE_CORRECTED_INVOICE:
        return hold(
            invoice,
            reasons,
            (*extra_clarifications, ask("supplier", (invoice.id,), cite)),
            label="hold for corrected invoice",
        )
    amount = sum(
        line_total(min(line.quantity, available.get(line.po_line_no, 0)), line.unit_price_minor)
        for line in invoice.lines
    )
    return pay(
        params,
        invoice,
        amount,
        (ReasonCode.PARTIAL_RECEIPT_PAID,),
        clarifications=extra_clarifications,
        label="pay received portion",
    )


def received_by_line(receipts: list[GoodsReceipt]) -> dict[int, int]:
    totals: dict[int, int] = {}
    for receipt in receipts:
        for line in receipt.lines:
            totals[line.po_line_no] = totals.get(line.po_line_no, 0) + line.quantity
    return totals
