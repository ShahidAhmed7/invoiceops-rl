"""Deterministic responses from simulated colleagues and suppliers.

Nothing here can produce a favourable fact on its own: an approval decision exists only after
the agent requested it, and a scripted reply is released only after the agent sent the
clarification (right recipient, right request type) that triggers it. Repeated
``check_inbox`` calls never release anything twice.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable
from typing import Any

from invoiceops.domain.money import format_minor
from invoiceops.domain.records import Role
from invoiceops.domain.world import World
from invoiceops.state.store import Store


def release_due_events(
    store: Store, conn: sqlite3.Connection, world: World, step: int, new_id: Callable[[str], str]
) -> None:
    roles = {r.id: r for r in world.roles}
    currency = world.company.currency

    approvers = sorted(
        (r for r in world.roles if r.can_approve), key=lambda r: r.approval_limit_minor
    )
    pending = store.work_rows("approval_requests", "WHERE status = 'pending'")
    for req in pending:
        role = roles[req["approver_role"]]
        decision, note = _decide(req, role, approvers, world, currency)
        event_id = new_id("APE")
        conn.execute(
            "INSERT INTO approval_events VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                event_id,
                req["id"],
                req["invoice_id"],
                role.id,
                decision,
                req["amount_minor"],
                step,
                note,
            ),
        )
        conn.execute("UPDATE approval_requests SET status = ? WHERE id = ?", (decision, req["id"]))
        _post(conn, step, role.id, "approval_decision", note, [req["id"], event_id])

    released = {row["event_id"] for row in store.work_rows("released_events")}
    clarifications = store.work_rows("clarifications")
    for event in world.events:
        if event.id in released:
            continue
        triggered = any(
            c["invoice_id"] == event.trigger.invoice_id
            and c["recipient_role"] in event.trigger.recipient_roles
            and c["request_type"] in event.trigger.request_types
            for c in clarifications
        )
        if not triggered:
            continue
        record_ids: list[str] = []
        for doc in event.effects.documents:
            store.insert_source("documents", doc)
            record_ids.append(doc.id)
        for receipt in event.effects.receipts:
            store.insert_source("receipts", receipt)
            record_ids.append(receipt.id)
        conn.execute("INSERT INTO released_events VALUES (?, ?)", (event.id, step))
        _post(conn, step, event.from_role, "reply", event.message, record_ids)


def _decide(
    req: dict[str, Any], role: Role, approvers: list[Role], world: World, currency: str
) -> tuple[str, str]:
    """Each approver acts only at their own level of the delegation of authority: the lowest
    approver whose limit covers the amount. Scripted overrides model a justified refusal."""
    amount = format_minor(req["amount_minor"], currency)
    if req["amount_minor"] > role.approval_limit_minor:
        limit = format_minor(role.approval_limit_minor, currency)
        return "declined", (
            f"Declined: {amount} exceeds my approval limit of {limit}. "
            "Route this to the approver whose limit covers it."
        )
    level = next(r for r in approvers if r.approval_limit_minor >= req["amount_minor"])
    if level.id != role.id:
        return "declined", (
            f"Declined: {amount} is within the authority of {level.name} (`{level.id}`). "
            "Route this request to them; I approve only payments at my level."
        )
    for override in world.approval_overrides:
        if override.invoice_id == req["invoice_id"] and override.approver_role == role.id:
            return "declined", f"Declined: {override.note}"
    return "approved", f"Approved payment of {amount} for invoice {req['invoice_id']}."


def _post(
    conn: sqlite3.Connection,
    step: int,
    from_role: str,
    kind: str,
    message: str,
    record_ids: list[str],
) -> None:
    conn.execute(
        "INSERT INTO inbox (step, from_role, kind, message, record_ids) VALUES (?, ?, ?, ?, ?)",
        (step, from_role, kind, message, json.dumps(record_ids)),
    )
