"""The complete starting state of one task: a company's records, policy, events, and faults."""

from __future__ import annotations

from typing import Literal

from pydantic import model_validator

from invoiceops.domain.records import (
    Company,
    CreditNote,
    Document,
    GoodsReceipt,
    Invoice,
    PaymentRecord,
    PolicyVersion,
    PurchaseOrder,
    Record,
    RecordId,
    Role,
    Vendor,
)

AGENT_ROLE_ID = "ap_assistant"


class ClarificationTrigger(Record):
    """Fires once a clarification about ``invoice_id`` was sent to one of ``recipient_roles``."""

    kind: Literal["clarification"] = "clarification"
    invoice_id: RecordId
    recipient_roles: tuple[RecordId, ...]


class EventEffects(Record):
    """Records that become visible when an event is released."""

    documents: tuple[Document, ...] = ()
    receipts: tuple[GoodsReceipt, ...] = ()


class ScriptedEvent(Record):
    id: RecordId
    trigger: ClarificationTrigger
    from_role: RecordId
    message: str
    effects: EventEffects = EventEffects()


class Fault(Record):
    """A deterministic infrastructure fault injected into one tool call.

    ``lost_response``: the call's write is applied, but the agent receives a ``retryable`` error
    as if the response were lost in transit.
    """

    tool: Literal["propose_payment"]
    on_call: int = 1
    mode: Literal["lost_response"] = "lost_response"


class World(Record):
    world_id: RecordId
    company: Company
    roles: tuple[Role, ...]
    policies: tuple[PolicyVersion, ...]
    vendors: tuple[Vendor, ...]
    purchase_orders: tuple[PurchaseOrder, ...]
    receipts: tuple[GoodsReceipt, ...] = ()
    invoices: tuple[Invoice, ...]
    credit_notes: tuple[CreditNote, ...] = ()
    payments: tuple[PaymentRecord, ...] = ()
    documents: tuple[Document, ...]
    queue: tuple[RecordId, ...]
    events: tuple[ScriptedEvent, ...] = ()
    faults: tuple[Fault, ...] = ()

    @model_validator(mode="after")
    def _check_integrity(self) -> World:
        problems = integrity_problems(self)
        if problems:
            raise ValueError("world integrity check failed: " + "; ".join(problems))
        return self

    def all_record_ids(self) -> set[str]:
        """Every id an agent could legitimately cite at reset time."""
        ids: set[str] = {self.company.id}
        for group in (
            self.roles,
            self.policies,
            self.vendors,
            self.receipts,
            self.invoices,
            self.credit_notes,
            self.payments,
            self.documents,
        ):
            ids.update(item.id for item in group)
        ids.update(po.id for po in self.purchase_orders)
        return ids


def integrity_problems(world: World) -> list[str]:
    """Referential and consistency checks; an empty list means the world is consistent."""
    problems: list[str] = []
    as_of = world.company.as_of

    def dupes(kind: str, ids: list[str]) -> None:
        seen: set[str] = set()
        for item_id in ids:
            if item_id in seen:
                problems.append(f"duplicate {kind} id {item_id}")
            seen.add(item_id)

    dupes("role", [r.id for r in world.roles])
    dupes("vendor", [v.id for v in world.vendors])
    dupes("receipt", [r.id for r in world.receipts])
    dupes("invoice", [i.id for i in world.invoices])
    dupes("credit note", [c.id for c in world.credit_notes])
    dupes("payment", [p.id for p in world.payments])
    dupes("document", [d.id for d in world.documents])
    dupes("policy", [p.id for p in world.policies])
    dupes("purchase order revision", [f"{p.id}@{p.revision}" for p in world.purchase_orders])
    all_ids = [
        world.company.id,
        *(r.id for r in world.roles),
        *(v.id for v in world.vendors),
        *{p.id for p in world.purchase_orders},
        *(r.id for r in world.receipts),
        *(i.id for i in world.invoices),
        *(c.id for c in world.credit_notes),
        *(p.id for p in world.payments),
        *(d.id for d in world.documents),
        *(p.id for p in world.policies),
    ]
    for event in world.events:
        all_ids.extend(d.id for d in event.effects.documents)
        all_ids.extend(r.id for r in event.effects.receipts)
    dupes("record", all_ids)

    role_ids = {r.id for r in world.roles}
    if AGENT_ROLE_ID not in role_ids:
        problems.append(f"missing agent role {AGENT_ROLE_ID}")
    vendor_ids = {v.id for v in world.vendors}
    doc_ids = {d.id for d in world.documents}
    invoices = {i.id: i for i in world.invoices}
    po_lines: dict[str, set[int]] = {}
    for po in world.purchase_orders:
        if po.vendor_id not in vendor_ids:
            problems.append(f"PO {po.id} references unknown vendor {po.vendor_id}")
        po_lines.setdefault(po.id, set()).update(line.line_no for line in po.lines)
        if po.approved_on > as_of:
            problems.append(f"PO {po.id} rev {po.revision} approved after as-of date")

    receipts = list(world.receipts) + [r for e in world.events for r in e.effects.receipts]
    for receipt in receipts:
        if receipt.po_id not in po_lines:
            problems.append(f"receipt {receipt.id} references unknown PO {receipt.po_id}")
            continue
        for rline in receipt.lines:
            if rline.po_line_no not in po_lines[receipt.po_id]:
                problems.append(
                    f"receipt {receipt.id} references unknown PO line {rline.po_line_no}"
                )
    for receipt in world.receipts:
        if receipt.received_on > as_of:
            problems.append(f"receipt {receipt.id} dated after as-of date")

    for inv in world.invoices:
        if inv.vendor_id not in vendor_ids:
            problems.append(f"invoice {inv.id} references unknown vendor {inv.vendor_id}")
        if inv.po_id not in po_lines:
            problems.append(f"invoice {inv.id} references unknown PO {inv.po_id}")
        else:
            for iline in inv.lines:
                if iline.po_line_no not in po_lines[inv.po_id]:
                    problems.append(
                        f"invoice {inv.id} references unknown PO line {iline.po_line_no}"
                    )
        if inv.invoice_date > inv.received_on or inv.received_on > as_of:
            problems.append(f"invoice {inv.id} has inconsistent dates")
        for att in inv.attachment_ids:
            if att not in doc_ids:
                problems.append(f"invoice {inv.id} references unknown attachment {att}")

    payment_ids = {p.id for p in world.payments}
    for credit in world.credit_notes:
        if credit.vendor_id not in vendor_ids:
            problems.append(f"credit note {credit.id} references unknown vendor")
        if credit.invoice_id not in invoices:
            problems.append(
                f"credit note {credit.id} references unknown invoice {credit.invoice_id}"
            )
        if credit.applied_to_payment_id and credit.applied_to_payment_id not in payment_ids:
            problems.append(f"credit note {credit.id} references unknown payment")
    for payment in world.payments:
        if payment.invoice_id not in invoices:
            problems.append(f"payment {payment.id} references unknown invoice {payment.invoice_id}")
        if payment.vendor_id not in vendor_ids:
            problems.append(f"payment {payment.id} references unknown vendor")

    for policy in world.policies:
        if policy.document_id not in doc_ids:
            problems.append(f"policy {policy.id} references unknown document {policy.document_id}")
    if not any(_policy_effective(p, as_of) for p in world.policies):
        problems.append("no policy version is effective on the as-of date")

    if not world.queue:
        problems.append("queue is empty")
    paid_invoices = {p.invoice_id for p in world.payments}
    for invoice_id in world.queue:
        if invoice_id not in invoices:
            problems.append(f"queue references unknown invoice {invoice_id}")
        if invoice_id in paid_invoices:
            problems.append(f"queued invoice {invoice_id} already has a payment")

    for event in world.events:
        if event.from_role not in role_ids:
            problems.append(f"event {event.id} from unknown role {event.from_role}")
        if event.trigger.invoice_id not in invoices:
            problems.append(f"event {event.id} triggers on unknown invoice")
        for role_id in event.trigger.recipient_roles:
            if role_id not in role_ids:
                problems.append(f"event {event.id} triggers on unknown role {role_id}")
    return problems


def _policy_effective(policy: PolicyVersion, on: str) -> bool:
    return policy.effective_from <= on and (policy.effective_to is None or on < policy.effective_to)


def effective_policy(world: World, on: str | None = None) -> PolicyVersion:
    """The policy version in force on ``on`` (default: the company's as-of date)."""
    day = on or world.company.as_of
    matches = [p for p in world.policies if _policy_effective(p, day)]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one effective policy on {day}, found {len(matches)}")
    return matches[0]
