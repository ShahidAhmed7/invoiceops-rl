"""Oracle solver: a rule-based agent that applies the written AP policy through the tools.

It is privileged in exactly one way: it reads the effective policy *parameters* from the world
instead of parsing the policy text. Everything else (invoices, receipts, history, inbox) it
learns through the same tools any agent uses. It does not read the private task, so its
decisions are an independent derivation of each family's expected outcome.

It is not an agent baseline; it proves that every task is solvable through the tools.
"""

from __future__ import annotations

from typing import Any

from invoiceops.domain.money import apply_bps
from invoiceops.domain.records import PartialInvoiceRule
from invoiceops.domain.world import effective_policy
from invoiceops.episode import Episode

# Policy sections 3, 4, 5 and 9 name one request type per recipient.
REQUEST_FOR = {
    "supplier": "corrected_invoice",
    "procurement": "price_confirmation",
    "receiving": "receipt_confirmation",
    "vendor_master": "bank_detail_verification",
}


class OracleError(RuntimeError):
    pass


def _call(ep: Episode, tool: str, **args: Any) -> Any:
    obs = ep.step(tool, args)
    if not obs["ok"]:
        raise OracleError(f"{tool} failed: {obs['error']}")
    return obs["result"]


def _version(ep: Episode, invoice_id: str) -> int:
    return int(_call(ep, "get_invoice", invoice_id=invoice_id)["ap_case"]["version"])


def solve(ep: Episode) -> None:
    queue = _call(ep, "list_queue")
    if len(queue) != 1:
        raise OracleError("oracle expects exactly one queued invoice")
    _Solver(ep, queue[0]["invoice_id"]).run()


class _Solver:
    def __init__(self, ep: Episode, invoice_id: str) -> None:
        self.ep = ep
        self.inv_id = invoice_id
        self.params = effective_policy(ep.world).params
        self.roles = ep.world.roles
        self._keys = 0

    def key(self, prefix: str) -> str:
        self._keys += 1
        return f"oracle-{prefix}-{self._keys}"

    def hold(self, reason: str, evidence: list[str], ask_role: str | None, cite: list[str]) -> None:
        if ask_role:
            _call(
                self.ep,
                "create_clarification",
                invoice_id=self.inv_id,
                recipient_role=ask_role,
                request_type=REQUEST_FOR[ask_role],
                evidence_ids=cite,
                idempotency_key=self.key("clr"),
            )
        self.dispose("on_hold", reason, evidence)

    def dispose(self, status: str, reason: str, evidence: list[str]) -> None:
        _call(
            self.ep,
            "set_disposition",
            invoice_id=self.inv_id,
            status=status,
            reason_code=reason,
            evidence_ids=evidence,
            expected_version=_version(self.ep, self.inv_id),
        )

    def submit(self, status: str, reason: str, amount: int, evidence: list[str]) -> None:
        _call(
            self.ep,
            "submit_case",
            invoice_id=self.inv_id,
            status=status,
            reason_code=reason,
            amount_proposed_minor=amount,
            evidence_ids=evidence,
            summary=f"{self.inv_id}: {status} ({reason}); proposed {amount} cents.",
        )

    def run(self) -> None:
        ep = self.ep
        inv = _call(ep, "get_invoice", invoice_id=self.inv_id)
        vendor = _call(ep, "get_vendor", vendor_id=inv["vendor_id"])
        base = [self.inv_id]

        # Section 9: bank details.
        if inv["remit_account"] != vendor["remit_account"] or not vendor["verified"]:
            cite = [self.inv_id, vendor["id"], *inv["attachment_ids"]]
            self.hold("vendor_verification", base, "vendor_master", cite)
            self.submit("on_hold", "vendor_verification", 0, base)
            return

        # Section 6: duplicates.
        history = _call(ep, "get_history", vendor_id=inv["vendor_id"])
        settled = {
            p["invoice_id"] for p in history["payments"] if p["status"] in ("paid", "scheduled")
        }
        for other in history["invoices"]:
            if other["invoice_id"] == self.inv_id:
                continue
            same_number = other["vendor_invoice_number"] == inv["vendor_invoice_number"]
            same_triplet = (
                other["po_id"] == inv["po_id"]
                and other["total_minor"] == inv["total_minor"]
                and other["invoice_date"] == inv["invoice_date"]
            )
            if same_number or same_triplet:
                evidence = [self.inv_id, other["invoice_id"]]
                self.dispose("rejected", "duplicate_invoice", evidence)
                self.submit("rejected", "duplicate_invoice", 0, evidence)
                return

        po = _call(ep, "get_purchase_order", po_id=inv["po_id"])
        po_lines = {line["line_no"]: line for line in po["lines"]}
        receipts = _call(ep, "get_receipts", po_id=po["id"])["receipts"]
        asked_receiving = False

        # Section 5: missing receipts (ask once, then use the reply).
        if not self._covers(inv, receipts):
            cite = [self.inv_id, po["id"]]
            self.hold("missing_receipt", base, "receiving", cite)
            asked_receiving = True
            _call(ep, "check_inbox")
            receipts = _call(ep, "get_receipts", po_id=po["id"])["receipts"]
            if not self._covers(inv, receipts):
                self.submit("on_hold", "missing_receipt", 0, base)
                return

        # Sections 2 and 4: quantities still available to bill.
        received: dict[int, int] = {}
        for receipt in receipts:
            for line in receipt["lines"]:
                received[line["po_line_no"]] = (
                    received.get(line["po_line_no"], 0) + line["quantity"]
                )
        billed: dict[int, int] = {}
        for other in history["invoices"]:
            if other["invoice_id"] == self.inv_id or other["po_id"] != po["id"]:
                continue
            if other["invoice_id"] not in settled:
                continue
            for line in other["lines"]:
                billed[line["po_line_no"]] = billed.get(line["po_line_no"], 0) + line["quantity"]
        available = {n: received.get(n, 0) - billed.get(n, 0) for n in po_lines}
        pay_qty = {ln["po_line_no"]: ln["quantity"] for ln in inv["lines"]}
        short_lines = [n for n, q in pay_qty.items() if q > available.get(n, 0)]
        reason = "matched"
        if short_lines:
            prior = any(billed.get(n, 0) > 0 for n in short_lines)
            hold_reason = "quantity_exceeds_receipt" if prior else "short_receipt"
            if self.params.partial_invoice_rule is PartialInvoiceRule.REQUIRE_CORRECTED_INVOICE:
                cite = [self.inv_id, *(r["id"] for r in receipts), po["id"]]
                self.hold(hold_reason, base, "supplier", cite)
                self.submit("on_hold", hold_reason, 0, base)
                return
            pay_qty = {n: min(q, max(0, available.get(n, 0))) for n, q in pay_qty.items()}
            reason = "partial_receipt_paid"

        # Section 3: price check.
        variance = sum(
            (ln["unit_price_minor"] - po_lines[ln["po_line_no"]]["unit_price_minor"])
            * ln["quantity"]
            for ln in inv["lines"]
        )
        po_value = sum(
            po_lines[ln["po_line_no"]]["unit_price_minor"] * ln["quantity"] for ln in inv["lines"]
        )
        limit = min(
            apply_bps(po_value, self.params.price_tolerance_bps),
            self.params.price_tolerance_cap_minor,
        )
        if variance > limit:
            self.hold("price_variance", base, "procurement", [self.inv_id, po["id"]])
            self.submit("on_hold", "price_variance", 0, base)
            return
        if variance > 0 and reason == "matched":
            reason = "matched_within_tolerance"

        amount = sum(ln["unit_price_minor"] * pay_qty[ln["po_line_no"]] for ln in inv["lines"])

        # Section 7: credit notes.
        credits = [
            c
            for c in history["credit_notes"]
            if c["invoice_id"] == self.inv_id and c["status"] == "open"
        ]
        if credits:
            amount -= sum(c["amount_minor"] for c in credits)
            if reason == "matched":
                reason = "matched_with_credit"

        # Section 8: approval.
        if amount > self.params.self_approval_limit_minor:
            approver = min(
                (r for r in self.roles if r.can_approve and r.approval_limit_minor >= amount),
                key=lambda r: r.approval_limit_minor,
            )
            _call(
                ep,
                "request_approval",
                invoice_id=self.inv_id,
                approver_role=approver.id,
                amount_minor=amount,
                evidence_ids=base,
                idempotency_key=self.key("apr"),
            )
            inbox = _call(ep, "check_inbox")
            decisions = [m for m in inbox["messages"] if m["kind"] == "approval_decision"]
            if not decisions:
                raise OracleError("no approval decision arrived")
            if not decisions[-1]["message"].startswith("Approved"):
                # Section 8: the right approver declined, so the invoice stays on hold.
                self.dispose("on_hold", "awaiting_approval", base)
                self.submit("on_hold", "awaiting_approval", 0, base)
                return

        self.dispose("ready_for_payment", reason, base)
        key = self.key("pay")
        args = {
            "invoice_id": self.inv_id,
            "amount_minor": amount,
            "credit_note_ids": [c["id"] for c in credits],
            "evidence_ids": base,
            "idempotency_key": key,
        }
        obs = ep.step("propose_payment", args)
        if not obs["ok"] and obs["error"]["code"] == "retryable":
            obs = ep.step("propose_payment", args)
        if not obs["ok"]:
            raise OracleError(f"propose_payment failed: {obs['error']}")
        _ = asked_receiving
        self.submit("ready_for_payment", reason, amount, base)

    @staticmethod
    def _covers(inv: dict[str, Any], receipts: list[dict[str, Any]]) -> bool:
        lines = {line["po_line_no"] for r in receipts for line in r["lines"]}
        return all(ln["po_line_no"] in lines for ln in inv["lines"])
