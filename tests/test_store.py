from __future__ import annotations

import sqlite3

import pytest

from invoiceops.episode import Episode
from invoiceops.state.store import SOURCE_TABLES

from .conftest import by_family


def test_source_tables_reject_update_and_delete() -> None:
    ep = Episode(by_family("F05", 1).public.world)
    populated = [t for t in SOURCE_TABLES if ep.store.count(t) > 0]
    assert len(populated) >= 9  # triggers fire per row, so test tables that have rows
    for table in populated:
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            ep.store.conn.execute(f"UPDATE {table} SET data = '{{}}'")
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            ep.store.conn.execute(f"DELETE FROM {table}")


def test_reset_is_deterministic() -> None:
    world = by_family("F05").public.world
    assert Episode(world).store.state_hash() == Episode(world).store.state_hash()


def test_failed_transaction_rolls_back() -> None:
    ep = Episode(by_family("F01").public.world)
    before = ep.store.state_hash()
    with pytest.raises(RuntimeError), ep.store.transaction() as conn:
        conn.execute("UPDATE cases SET status = 'on_hold'")
        raise RuntimeError("boom")
    assert ep.store.state_hash() == before
