"""Per-episode SQLite state.

Each episode owns a private in-memory database. Source records are stored as canonical JSON
in tables protected by triggers: any ``UPDATE`` or ``DELETE`` on them aborts, so even a bug in
a tool handler cannot alter the authoritative records. New source records (a receipt that
arrives later, a supplier message) can only be inserted by the event engine.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from invoiceops.domain.records import Record
from invoiceops.domain.world import World

SOURCE_TABLES: tuple[str, ...] = (
    "company",
    "roles",
    "policies",
    "vendors",
    "purchase_orders",
    "receipts",
    "invoices",
    "credit_notes",
    "payments",
    "documents",
)

WORK_TABLES: tuple[str, ...] = (
    "cases",
    "case_history",
    "clarifications",
    "approval_requests",
    "approval_events",
    "proposals",
    "submission",
    "released_events",
    "inbox",
)

_SOURCE_DDL = """
CREATE TABLE {name} (
    id TEXT NOT NULL,
    revision INTEGER NOT NULL DEFAULT 1,
    data TEXT NOT NULL,
    PRIMARY KEY (id, revision)
);
CREATE TRIGGER {name}_no_update BEFORE UPDATE ON {name}
BEGIN SELECT RAISE(ABORT, 'source records are immutable'); END;
CREATE TRIGGER {name}_no_delete BEFORE DELETE ON {name}
BEGIN SELECT RAISE(ABORT, 'source records are immutable'); END;
"""

_WORK_DDL = """
CREATE TABLE cases (
    invoice_id TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    reason_code TEXT,
    evidence_ids TEXT NOT NULL,
    note TEXT NOT NULL,
    version INTEGER NOT NULL,
    updated_step INTEGER NOT NULL
);
CREATE TABLE case_history (
    seq INTEGER PRIMARY KEY,
    invoice_id TEXT NOT NULL,
    status TEXT NOT NULL,
    reason_code TEXT,
    evidence_ids TEXT NOT NULL,
    note TEXT NOT NULL,
    version INTEGER NOT NULL,
    step INTEGER NOT NULL
);
CREATE TABLE clarifications (
    id TEXT PRIMARY KEY,
    invoice_id TEXT NOT NULL,
    recipient_role TEXT NOT NULL,
    question TEXT NOT NULL,
    evidence_ids TEXT NOT NULL,
    idempotency_key TEXT NOT NULL UNIQUE,
    step INTEGER NOT NULL
);
CREATE TABLE approval_requests (
    id TEXT PRIMARY KEY,
    invoice_id TEXT NOT NULL,
    approver_role TEXT NOT NULL,
    amount_minor INTEGER NOT NULL,
    evidence_ids TEXT NOT NULL,
    idempotency_key TEXT NOT NULL UNIQUE,
    step INTEGER NOT NULL,
    status TEXT NOT NULL
);
CREATE TABLE approval_events (
    id TEXT PRIMARY KEY,
    request_id TEXT NOT NULL,
    invoice_id TEXT NOT NULL,
    actor_role TEXT NOT NULL,
    decision TEXT NOT NULL,
    amount_minor INTEGER NOT NULL,
    step INTEGER NOT NULL,
    note TEXT NOT NULL
);
CREATE TABLE proposals (
    id TEXT PRIMARY KEY,
    invoice_id TEXT NOT NULL,
    amount_minor INTEGER NOT NULL,
    credit_note_ids TEXT NOT NULL,
    evidence_ids TEXT NOT NULL,
    idempotency_key TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL,
    created_step INTEGER NOT NULL,
    withdrawn_step INTEGER,
    withdraw_reason TEXT
);
CREATE TABLE submission (
    invoice_id TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    reason_code TEXT,
    amount_proposed_minor INTEGER NOT NULL,
    evidence_ids TEXT NOT NULL,
    summary TEXT NOT NULL,
    step INTEGER NOT NULL
);
CREATE TABLE released_events (
    event_id TEXT PRIMARY KEY,
    step INTEGER NOT NULL
);
CREATE TABLE inbox (
    seq INTEGER PRIMARY KEY,
    step INTEGER NOT NULL,
    from_role TEXT NOT NULL,
    kind TEXT NOT NULL,
    message TEXT NOT NULL,
    record_ids TEXT NOT NULL
);
"""

_ORDER_BY = {
    "cases": "invoice_id",
    "case_history": "seq",
    "clarifications": "id",
    "approval_requests": "id",
    "approval_events": "id",
    "proposals": "id",
    "submission": "invoice_id",
    "released_events": "event_id",
    "inbox": "seq",
}


def canonical_json(value: Any) -> str:
    """Deterministic JSON: sorted keys, no whitespace, UTF-8 preserved."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class Store:
    """One episode's database."""

    def __init__(self) -> None:
        # One episode is driven by one session at a time, but servers may call it from
        # different worker threads; ``Episode`` serialises access with a lock.
        self.conn = sqlite3.connect(":memory:", isolation_level=None, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        for name in SOURCE_TABLES:
            self.conn.executescript(_SOURCE_DDL.format(name=name))
        self.conn.executescript(_WORK_DDL)

    def close(self) -> None:
        self.conn.close()

    # -- loading ---------------------------------------------------------------------------

    def load_world(self, world: World) -> None:
        with self.transaction():
            self.insert_source("company", world.company)
            for table, records in (
                ("roles", world.roles),
                ("policies", world.policies),
                ("vendors", world.vendors),
                ("receipts", world.receipts),
                ("invoices", world.invoices),
                ("credit_notes", world.credit_notes),
                ("payments", world.payments),
                ("documents", world.documents),
            ):
                for record in records:
                    self.insert_source(table, record)
            for po in world.purchase_orders:
                self.insert_source("purchase_orders", po, revision=po.revision)

    def insert_source(self, table: str, record: Record, revision: int = 1) -> None:
        if table not in SOURCE_TABLES:
            raise ValueError(f"{table} is not a source table")
        data = canonical_json(record.model_dump(mode="json"))
        record_id = getattr(record, "id")  # noqa: B009 - every source record has an id
        self.conn.execute(
            f"INSERT INTO {table} (id, revision, data) VALUES (?, ?, ?)",
            (record_id, revision, data),
        )

    # -- reading ---------------------------------------------------------------------------

    def source_rows(self, table: str) -> list[dict[str, Any]]:
        if table not in SOURCE_TABLES:
            raise ValueError(f"{table} is not a source table")
        rows = self.conn.execute(f"SELECT data FROM {table} ORDER BY id, revision").fetchall()
        return [json.loads(row["data"]) for row in rows]

    def source_get(self, table: str, record_id: str) -> dict[str, Any] | None:
        """The latest revision of one source record, or ``None``."""
        row = self.conn.execute(
            f"SELECT data FROM {table} WHERE id = ? ORDER BY revision DESC LIMIT 1", (record_id,)
        ).fetchone()
        return None if row is None else dict(json.loads(row["data"]))

    def source_revisions(self, table: str, record_id: str) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            f"SELECT data FROM {table} WHERE id = ? ORDER BY revision", (record_id,)
        ).fetchall()
        return [json.loads(row["data"]) for row in rows]

    def record_exists(self, record_id: str) -> bool:
        for table in SOURCE_TABLES:
            if self.conn.execute(f"SELECT 1 FROM {table} WHERE id = ?", (record_id,)).fetchone():
                return True
        for table, column in (
            ("clarifications", "id"),
            ("approval_requests", "id"),
            ("approval_events", "id"),
            ("proposals", "id"),
        ):
            query = f"SELECT 1 FROM {table} WHERE {column} = ?"
            if self.conn.execute(query, (record_id,)).fetchone():
                return True
        return False

    def work_rows(
        self, table: str, where: str = "", params: tuple[Any, ...] = ()
    ) -> list[dict[str, Any]]:
        if table not in WORK_TABLES:
            raise ValueError(f"{table} is not a work table")
        sql = f"SELECT * FROM {table} {where} ORDER BY {_ORDER_BY[table]}"
        return [dict(row) for row in self.conn.execute(sql, params).fetchall()]

    def count(self, table: str) -> int:
        row = self.conn.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()
        return int(row["n"])

    # -- writing ---------------------------------------------------------------------------

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """All-or-nothing write block."""
        self.conn.execute("BEGIN")
        try:
            yield self.conn
        except BaseException:
            self.conn.execute("ROLLBACK")
            raise
        else:
            self.conn.execute("COMMIT")

    # -- snapshots -------------------------------------------------------------------------

    def snapshot(self) -> dict[str, list[dict[str, Any]]]:
        """Canonical copy of every table, suitable for hashing and for the verifier."""
        snap: dict[str, list[dict[str, Any]]] = {}
        for table in SOURCE_TABLES:
            rows = self.conn.execute(
                f"SELECT id, revision, data FROM {table} ORDER BY id, revision"
            ).fetchall()
            snap[table] = [
                {"id": r["id"], "revision": r["revision"], "data": json.loads(r["data"])}
                for r in rows
            ]
        for table in WORK_TABLES:
            snap[table] = self.work_rows(table)
        return snap

    def state_hash(self, tables: tuple[str, ...] | None = None) -> str:
        snap = self.snapshot()
        selected = {name: snap[name] for name in (tables or tuple(snap))}
        return sha256_hex(canonical_json(selected))


def snapshot_hash(snapshot: dict[str, list[dict[str, Any]]], tables: tuple[str, ...]) -> str:
    """Hash a subset of an exported snapshot (same result as ``Store.state_hash``)."""
    return sha256_hex(canonical_json({name: snapshot[name] for name in tables}))
