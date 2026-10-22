"""Deterministic responses from simulated colleagues and suppliers.

Nothing here can produce a favourable fact on its own: an approval decision exists only after
the agent requested it, and a scripted reply is released only after the agent sent the
clarification that triggers it. Repeated ``check_inbox`` calls never release anything twice.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable

from invoiceops.domain.money import format_minor
from invoiceops.domain.world import World
from invoiceops.state.store import Store


def release_due_events(
    store: Store, conn: sqlite3.Connection, world: World, step: int, new_id: Callable[[str], str]
) -> None:
    roles = {r.id: r for r in world.roles}
    currency = world.company.currency

    pending = store.work_rows("approval_requests", "WHERE status = 'pending'")
    for req in pending:
        role = roles[req["approver_role"]]
        approved = req["amount_minor"] <= role.approval_limit_minor
        decision = "approved" if approved else "declined"
        amount = format_minor(req["amount_minor"], currency)
        if approved:
            note = f"Approved payment of {amount} for invoice {req['invoice_id']}."
        else:
            limit = format_minor(role.approval_limit_minor, currency)
            note = (
                f"Declined: {amount} exceeds my approval limit of {limit}. "
                "Route this to an approver with a higher limit."
            )
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
