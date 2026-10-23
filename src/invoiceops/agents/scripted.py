"""Simple fixed policies used to expose scoring shortcuts. All of them should score badly."""

from __future__ import annotations

import random
from collections.abc import Callable
from typing import Any

from invoiceops.episode import Episode
from invoiceops.tools.spec import TOOLS


def _target(ep: Episode) -> dict[str, Any]:
    obs = ep.step("list_queue", {})
    queue: list[dict[str, Any]] = obs["result"]
    return queue[0]


def noop(ep: Episode) -> None:
    """Claims the invoice is ready for payment without doing anything."""
    item = _target(ep)
    ep.step(
        "submit_case",
        {
            "invoice_id": item["invoice_id"],
            "status": "ready_for_payment",
            "reason_code": "matched",
            "amount_proposed_minor": item["total_minor"],
            "evidence_ids": [item["invoice_id"]],
            "summary": "Checked and approved for payment.",
        },
    )


def always_hold(ep: Episode) -> None:
    """Puts every invoice on hold and asks the supplier for a corrected invoice."""
    item = _target(ep)
    inv = ep.step("get_invoice", {"invoice_id": item["invoice_id"]})["result"]
    evidence = [inv["id"], inv["po_id"]]
    ep.step(
        "create_clarification",
        {
            "invoice_id": inv["id"],
            "recipient_role": "supplier",
            "request_type": "corrected_invoice",
            "evidence_ids": evidence,
            "idempotency_key": "hold-1",
        },
    )
    ep.step(
        "set_disposition",
        {
            "invoice_id": inv["id"],
            "status": "on_hold",
            "reason_code": "short_receipt",
            "evidence_ids": evidence,
            "expected_version": inv["ap_case"]["version"],
        },
    )
    ep.step(
        "submit_case",
        {
            "invoice_id": inv["id"],
            "status": "on_hold",
            "reason_code": "short_receipt",
            "amount_proposed_minor": 0,
            "evidence_ids": evidence,
            "summary": "On hold.",
        },
    )


def always_pay(ep: Episode) -> None:
    """Proposes the full invoiced amount for every invoice."""
    item = _target(ep)
    inv = ep.step("get_invoice", {"invoice_id": item["invoice_id"]})["result"]
    evidence = [inv["id"], inv["po_id"]]
    ep.step(
        "set_disposition",
        {
            "invoice_id": inv["id"],
            "status": "ready_for_payment",
            "reason_code": "matched",
            "evidence_ids": evidence,
            "expected_version": inv["ap_case"]["version"],
        },
    )
    ep.step(
        "propose_payment",
        {
            "invoice_id": inv["id"],
            "amount_minor": inv["total_minor"],
            "credit_note_ids": [],
            "evidence_ids": evidence,
            "idempotency_key": "pay-1",
        },
    )
    ep.step(
        "submit_case",
        {
            "invoice_id": inv["id"],
            "status": "ready_for_payment",
            "reason_code": "matched",
            "amount_proposed_minor": inv["total_minor"],
            "evidence_ids": evidence,
            "summary": "Paid.",
        },
    )


def make_random(seed: int, steps: int = 15) -> Callable[[Episode], None]:
    """Seeded random tool calls with plausible arguments, then a random submission."""

    def policy(ep: Episode) -> None:
        rng = random.Random(seed)
        item = _target(ep)
        inv = ep.step("get_invoice", {"invoice_id": item["invoice_id"]})["result"]
        ids = [inv["id"], inv["po_id"], inv["vendor_id"], *inv["attachment_ids"]]
        statuses = {
            "ready_for_payment": ["matched", "matched_within_tolerance", "partial_receipt_paid"],
            "on_hold": [
                "short_receipt",
                "price_variance",
                "missing_receipt",
                "vendor_verification",
            ],
            "rejected": ["duplicate_invoice"],
        }
        roles = [r.id for r in ep.world.roles if r.id != "ap_assistant"]
        names = [t.name for t in TOOLS if t.name != "submit_case"]
        for n in range(steps):
            name = rng.choice(names)
            status = rng.choice(list(statuses))
            args: dict[str, Any] = {
                "list_queue": {},
                "check_inbox": {},
                "search_records": {"collection": rng.choice(["invoices", "documents", "receipts"])},
                "get_invoice": {"invoice_id": inv["id"]},
                "get_purchase_order": {"po_id": inv["po_id"]},
                "get_receipts": {"po_id": inv["po_id"]},
                "get_vendor": {"vendor_id": inv["vendor_id"]},
                "get_document": {"document_id": rng.choice(ids)},
                "get_history": {"vendor_id": inv["vendor_id"]},
                "set_disposition": {
                    "invoice_id": inv["id"],
                    "status": status,
                    "reason_code": rng.choice(statuses[status]),
                    "evidence_ids": [rng.choice(ids)],
                    "expected_version": rng.randrange(1, 4),
                },
                "create_clarification": {
                    "invoice_id": inv["id"],
                    "recipient_role": rng.choice(roles),
                    "request_type": rng.choice(
                        ["corrected_invoice", "price_confirmation", "receipt_confirmation"]
                    ),
                    "evidence_ids": [inv["id"]],
                    "idempotency_key": f"r{n}",
                },
                "request_approval": {
                    "invoice_id": inv["id"],
                    "approver_role": rng.choice(roles),
                    "amount_minor": inv["total_minor"],
                    "evidence_ids": [inv["id"]],
                    "idempotency_key": f"r{n}",
                },
                "propose_payment": {
                    "invoice_id": inv["id"],
                    "amount_minor": inv["total_minor"],
                    "credit_note_ids": [],
                    "evidence_ids": [inv["id"]],
                    "idempotency_key": f"r{n}",
                },
                "withdraw_payment_proposal": {"proposal_id": "PRP-001", "reason": "random"},
            }[name]
            ep.step(name, args)
            if ep.done:
                return
        status = rng.choice(list(statuses))
        ep.step(
            "submit_case",
            {
                "invoice_id": inv["id"],
                "status": status,
                "reason_code": rng.choice(statuses[status]),
                "amount_proposed_minor": rng.choice([0, inv["total_minor"]]),
                "evidence_ids": [inv["id"]],
                "summary": "Done.",
            },
        )

    return policy


SCRIPTED: dict[str, Callable[[Episode], None]] = {
    "noop": noop,
    "always_hold": always_hold,
    "always_pay": always_pay,
    "random": make_random(0),
}
