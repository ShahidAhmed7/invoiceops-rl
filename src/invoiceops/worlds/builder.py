"""Deterministic construction of a task's world.

A ``ScenarioBuilder`` starts from one fictional company, adds the company's standing records
(roles, policy, vendors, and unrelated "background" purchasing activity so that searching is
meaningful), and lets a task family add the records that make up its scenario. All randomness
comes from one seeded generator, so the same seed always produces byte-identical worlds.
"""

from __future__ import annotations

import hashlib
import random
from collections.abc import Sequence
from datetime import date, timedelta

from invoiceops.domain.money import line_total
from invoiceops.domain.records import (
    Company,
    CreditNote,
    Document,
    GoodsReceipt,
    Invoice,
    InvoiceLine,
    PaymentRecord,
    PolicyParams,
    PolicyVersion,
    POLine,
    PurchaseOrder,
    ReceiptLine,
    RequestType,
    Role,
    Vendor,
)
from invoiceops.domain.world import (
    AGENT_ROLE_ID,
    ApprovalOverride,
    ClarificationTrigger,
    EventEffects,
    Fault,
    ScriptedEvent,
    World,
)
from invoiceops.worlds.companies import CompanySpec, ItemSpec, VendorSpec
from invoiceops.worlds.policy_text import policy_title, render_policy


def stable_seed(*parts: str | int) -> int:
    digest = hashlib.sha256("|".join(str(p) for p in parts).encode()).hexdigest()
    return int(digest[:16], 16)


def shift(day: str, days: int) -> str:
    return (date.fromisoformat(day) + timedelta(days=days)).isoformat()


class ScenarioBuilder:
    def __init__(self, spec: CompanySpec, seed: int) -> None:
        self.spec = spec
        self.rng = random.Random(seed)
        self.as_of = spec.as_of
        self._counters: dict[str, int] = {
            "PO": self.rng.randrange(1000, 8000),
            "GRN": self.rng.randrange(10, 900),
            "INV": self.rng.randrange(10000, 80000),
            "CN": self.rng.randrange(100, 900),
            "PAY": self.rng.randrange(20000, 90000),
            "DOC": self.rng.randrange(100, 900),
            "MSG": self.rng.randrange(100, 900),
        }
        self.roles = self._roles()
        self.vendors: dict[str, Vendor] = {}
        self.purchase_orders: list[PurchaseOrder] = []
        self.receipts: list[GoodsReceipt] = []
        self.invoices: list[Invoice] = []
        self.credit_notes: list[CreditNote] = []
        self.payments: list[PaymentRecord] = []
        self.documents: list[Document] = []
        self.policies: list[PolicyVersion] = []
        self.events: list[ScriptedEvent] = []
        self.faults: list[Fault] = []
        self.approval_overrides: list[ApprovalOverride] = []
        self._reserved_ids: set[str] = set()
        for vendor_spec in spec.vendors:
            self.vendors[vendor_spec.key] = self._vendor(vendor_spec)

    # -- identifiers -------------------------------------------------------------------------

    def next_id(self, kind: str) -> str:
        while True:
            self._counters[kind] += self.rng.randrange(1, 9)
            candidate = f"{kind}-{self._counters[kind]}"
            if candidate not in self._reserved_ids:
                return candidate

    def reserve_ids(self, *ids: str) -> None:
        """Keep fixed identifiers (used by hand-specified scenarios) from being generated."""
        self._reserved_ids.update(ids)

    # -- standing records --------------------------------------------------------------------

    def _roles(self) -> tuple[Role, ...]:
        s = self.spec
        return (
            Role(
                id=AGENT_ROLE_ID,
                name="AP Assistant",
                kind="internal",
                can_approve=False,
                description="You: investigates invoices and records AP decisions.",
            ),
            Role(
                id="ap_manager",
                name="AP Manager",
                kind="internal",
                can_approve=True,
                approval_limit_minor=s.manager_limit_minor,
                description="Approves payments within their limit.",
            ),
            Role(
                id="controller",
                name="Financial Controller",
                kind="internal",
                can_approve=True,
                approval_limit_minor=s.controller_limit_minor,
                description="Approves payments within their limit.",
            ),
            Role(
                id="cfo",
                name="Chief Financial Officer",
                kind="internal",
                can_approve=True,
                approval_limit_minor=s.cfo_limit_minor,
                description="Approves payments within their limit.",
            ),
            Role(
                id="procurement",
                name="Procurement",
                kind="internal",
                can_approve=False,
                description="Owns purchase orders and agreed prices; contact about price "
                "variances.",
            ),
            Role(
                id="receiving",
                name="Receiving",
                kind="internal",
                can_approve=False,
                description="Owns goods receipts; contact about missing receipts.",
            ),
            Role(
                id="vendor_master",
                name="Vendor Master Data Team",
                kind="internal",
                can_approve=False,
                description="Owns supplier records and bank details; contact about bank-detail "
                "changes or unverified suppliers.",
            ),
            Role(
                id="supplier",
                name="Supplier contact on file",
                kind="external",
                can_approve=False,
                description="The supplier's contact from the supplier master record; contact for "
                "corrected invoices.",
            ),
        )

    def _vendor(self, vs: VendorSpec, verified: bool = True) -> Vendor:
        return Vendor(
            id=f"VEN-{self.spec.id_prefix}{vs.key.upper()}{self.rng.randrange(10, 99)}",
            legal_name=vs.legal_name,
            tax_id=f"TX-{self.rng.randrange(10, 99)}-{self.rng.randrange(1_000_000, 9_999_999)}",
            remit_account=self.new_account(),
            verified=verified,
            contact_email=f"accounts@{vs.email_domain}",
        )

    def new_account(self) -> str:
        bank = self.rng.choice(("Harbor Mutual Bank", "Cinder Trust", "Lowfield Savings Bank"))
        return f"{bank} ****{self.rng.randrange(1000, 9999)}"

    def replace_vendor(self, key: str, **changes: object) -> Vendor:
        vendor = self.vendors[key].model_copy(update=changes)
        self.vendors[key] = Vendor.model_validate(vendor.model_dump())
        return self.vendors[key]

    def add_policy_version(
        self,
        version: int,
        effective_from: str,
        effective_to: str | None,
        params: PolicyParams | None = None,
    ) -> PolicyVersion:
        params = params or self.default_params()
        doc_id = self.next_id("DOC")
        text = render_policy(
            self.spec.name, version, effective_from, effective_to, params, self.roles
        )
        self.documents.append(
            Document(
                id=doc_id,
                kind="policy",
                title=policy_title(self.spec.name, version, effective_from),
                body=text,
                source="Finance Policy Office",
                received_on=effective_from,
            )
        )
        policy = PolicyVersion(
            id=f"POL-AP-{version}",
            version=version,
            effective_from=effective_from,
            effective_to=effective_to,
            params=params,
            document_id=doc_id,
        )
        self.policies.append(policy)
        return policy

    def default_params(self) -> PolicyParams:
        s = self.spec
        return PolicyParams(
            price_tolerance_bps=s.price_tolerance_bps,
            price_tolerance_cap_minor=s.price_tolerance_cap_minor,
            partial_invoice_rule=s.partial_invoice_rule,
            self_approval_limit_minor=s.self_approval_limit_minor,
        )

    # -- purchasing records ------------------------------------------------------------------

    def item(self, index: int) -> ItemSpec:
        return self.spec.items[index % len(self.spec.items)]

    def po(
        self,
        vendor_key: str,
        lines: Sequence[tuple[ItemSpec, int, int]],
        approved_on: str,
        po_id: str | None = None,
        revision: int = 1,
        department: str | None = None,
    ) -> PurchaseOrder:
        """``lines`` are (item, quantity, unit price in minor units)."""
        record = PurchaseOrder(
            id=po_id or self.next_id("PO"),
            revision=revision,
            vendor_id=self.vendors[vendor_key].id,
            department=department or self.rng.choice(self.spec.departments),
            approved_on=approved_on,
            lines=tuple(
                POLine(
                    line_no=n,
                    sku=item.sku,
                    description=item.description,
                    quantity=qty,
                    unit_price_minor=price,
                )
                for n, (item, qty, price) in enumerate(lines, start=1)
            ),
        )
        self.purchase_orders.append(record)
        return record

    def receipt(
        self,
        po: PurchaseOrder,
        quantities: dict[int, int],
        received_on: str,
        receipt_id: str | None = None,
    ) -> GoodsReceipt:
        record = self.make_receipt(po, quantities, received_on, receipt_id)
        self.receipts.append(record)
        return record

    def make_receipt(
        self,
        po: PurchaseOrder,
        quantities: dict[int, int],
        received_on: str,
        receipt_id: str | None = None,
    ) -> GoodsReceipt:
        return GoodsReceipt(
            id=receipt_id or self.next_id("GRN"),
            po_id=po.id,
            received_on=received_on,
            lines=tuple(
                ReceiptLine(po_line_no=n, quantity=q)
                for n, q in sorted(quantities.items())
                if q > 0
            ),
        )

    def invoice(
        self,
        po: PurchaseOrder,
        quantities: dict[int, int],
        invoice_date: str,
        received_on: str | None = None,
        prices: dict[int, int] | None = None,
        vendor_invoice_number: str | None = None,
        remit_account: str | None = None,
        invoice_id: str | None = None,
        attachment_ids: tuple[str, ...] = (),
    ) -> Invoice:
        prices = prices or {}
        by_no = {line.line_no: line for line in po.lines}
        lines = tuple(
            InvoiceLine(
                po_line_no=n,
                description=by_no[n].description,
                quantity=q,
                unit_price_minor=prices.get(n, by_no[n].unit_price_minor),
            )
            for n, q in sorted(quantities.items())
        )
        vendor = next(v for v in self.vendors.values() if v.id == po.vendor_id)
        record = Invoice(
            id=invoice_id or self.next_id("INV"),
            vendor_id=vendor.id,
            vendor_invoice_number=vendor_invoice_number or self.vendor_invoice_number(vendor),
            po_id=po.id,
            invoice_date=invoice_date,
            received_on=received_on or shift(invoice_date, 2),
            remit_account=remit_account or vendor.remit_account,
            currency="USD",
            lines=lines,
            total_minor=sum(line_total(line.quantity, line.unit_price_minor) for line in lines),
            attachment_ids=attachment_ids,
        )
        self.invoices.append(record)
        return record

    def vendor_invoice_number(self, vendor: Vendor) -> str:
        initials = "".join(word[0] for word in vendor.legal_name.split()[:2]).upper()
        return f"{initials}-{self.rng.randrange(1000, 99999)}"

    def pay(
        self,
        invoice: Invoice,
        paid_on: str,
        amount_minor: int | None = None,
        credit_note_ids: tuple[str, ...] = (),
    ) -> PaymentRecord:
        record = PaymentRecord(
            id=self.next_id("PAY"),
            invoice_id=invoice.id,
            vendor_id=invoice.vendor_id,
            amount_minor=amount_minor if amount_minor is not None else invoice.total_minor,
            status="paid",
            paid_on=paid_on,
            credit_note_ids=credit_note_ids,
        )
        self.payments.append(record)
        return record

    def credit_note(
        self,
        invoice: Invoice,
        amount_minor: int,
        issued_on: str,
        applied_to: PaymentRecord | None = None,
    ) -> CreditNote:
        record = CreditNote(
            id=self.next_id("CN"),
            vendor_id=invoice.vendor_id,
            invoice_id=invoice.id,
            amount_minor=amount_minor,
            issued_on=issued_on,
            status="applied" if applied_to else "open",
            applied_to_payment_id=applied_to.id if applied_to else None,
        )
        self.credit_notes.append(record)
        return record

    def document(
        self, kind: str, title: str, body: str, source: str, received_on: str, prefix: str = "MSG"
    ) -> Document:
        record = self.make_document(kind, title, body, source, received_on, prefix)
        self.documents.append(record)
        return record

    def make_document(
        self, kind: str, title: str, body: str, source: str, received_on: str, prefix: str = "MSG"
    ) -> Document:
        return Document.model_validate(
            {
                "id": self.next_id(prefix),
                "kind": kind,
                "title": title,
                "body": body,
                "source": source,
                "received_on": received_on,
            }
        )

    def event(
        self,
        invoice: Invoice,
        recipient_roles: tuple[str, ...],
        from_role: str,
        message: str,
        request_types: tuple[RequestType, ...],
        documents: tuple[Document, ...] = (),
        receipts: tuple[GoodsReceipt, ...] = (),
    ) -> ScriptedEvent:
        record = ScriptedEvent(
            id=f"EV-{len(self.events) + 1}",
            trigger=ClarificationTrigger(
                invoice_id=invoice.id, recipient_roles=recipient_roles, request_types=request_types
            ),
            from_role=from_role,
            message=message,
            effects=EventEffects(documents=documents, receipts=receipts),
        )
        self.events.append(record)
        return record

    # -- background activity -----------------------------------------------------------------

    def add_background(self, count: int = 3) -> None:
        """Unrelated, fully settled purchasing activity with other vendors (search noise)."""
        keys = list(self.vendors)
        for n in range(count):
            vendor_key = keys[(n + 1) % len(keys)]
            item = self.item(self.rng.randrange(0, len(self.spec.items)))
            qty = self.rng.randrange(5, 60)
            approved = shift(self.as_of, -self.rng.randrange(60, 120))
            po = self.po(vendor_key, [(item, qty, item.unit_price_minor)], approved)
            received = shift(approved, self.rng.randrange(5, 15))
            self.receipt(po, {1: qty}, received)
            inv = self.invoice(po, {1: qty}, shift(received, 1))
            self.pay(inv, shift(inv.received_on, self.rng.randrange(10, 25)))

    # -- assembly ----------------------------------------------------------------------------

    def build(self, queue: Sequence[str], world_id: str) -> World:
        if not self.policies:
            self.add_policy_version(1, shift(self.as_of, -400), None)
        return World(
            world_id=world_id,
            company=Company(
                id=f"CO-{self.spec.id_prefix}",
                name=self.spec.name,
                currency="USD",
                as_of=self.as_of,
            ),
            roles=self.roles,
            policies=tuple(self.policies),
            vendors=tuple(self.vendors.values()),
            purchase_orders=tuple(self.purchase_orders),
            receipts=tuple(self.receipts),
            invoices=tuple(self.invoices),
            credit_notes=tuple(self.credit_notes),
            payments=tuple(self.payments),
            documents=tuple(self.documents),
            queue=tuple(queue),
            events=tuple(self.events),
            faults=tuple(self.faults),
            approval_overrides=tuple(self.approval_overrides),
        )
