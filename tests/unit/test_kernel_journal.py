"""Journal allocation remains atomic across independently constructed stores."""
from __future__ import annotations

import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from itertools import count

import pytest

from holdspeak.db import Database
from holdspeak.kernel.journal import JournalStore


def test_last_receipt_for_ref_uses_latest_admitted_operation_with_receipt(tmp_path) -> None:
    db = Database(tmp_path / "journal.db")
    timestamps = count(100)
    store = JournalStore(db._connection, clock=lambda: next(timestamps))
    try:
        store.append("operation.admitted", "op-old", refs=("egress:slack",))
        store.append("operation.receipt", "op-old")
        store.append("operation.admitted", "op-no-receipt", refs=("egress:slack",))
        store.append("operation.admitted", "op-new", refs=("egress:slack",))
        store.append("operation.receipt", "op-new")
        store.append("operation.admitted", "op-substring", refs=("egress:slack-other",))
        store.append("operation.receipt", "op-substring")

        assert store.last_receipt_for_ref("egress:slack") == "104.0"
        assert store.last_receipt_for_ref("egress:missing") is None
    finally:
        db.close()


def test_independent_stores_allocate_one_contiguous_hash_chain(tmp_path) -> None:
    db = Database(tmp_path / "journal.db")
    entering = threading.Barrier(2)
    unprotected_reads = threading.Barrier(2)

    class Cursor:
        def __init__(self, cursor):
            self.cursor = cursor

        def fetchone(self):
            row = self.cursor.fetchone()
            unprotected_reads.wait(timeout=5)
            return row

    class Connection:
        def __init__(self, conn):
            self.conn = conn

        def execute(self, sql, *args):
            cursor = self.conn.execute(sql, *args)
            if sql.startswith("SELECT stream_sequence") and not self.conn.in_transaction:
                # Force the old, unlocked readers to choose the same head.
                # Never wait at this boundary while holding a write lock.
                return Cursor(cursor)
            return cursor

    @contextmanager
    def overlapping_connections():
        with db._connection() as conn:
            entering.wait(timeout=5)
            yield Connection(conn)

    stores = [JournalStore(overlapping_connections) for _ in range(2)]
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [
                pool.submit(store.append, "operation.claimed", f"op-{index}")
                for index, store in enumerate(stores)
            ]
            records = [future.result(timeout=10) for future in futures]
        assert sorted(record["stream_sequence"] for record in records) == [1, 2]
        reader = JournalStore(db._connection)
        assert reader.verify()["records"] == 2
        events = reader.events(0, {})["events"]
        assert {event["operation_id"] for event in events} == {"op-0", "op-1"}
        assert events[1]["previous_sha256"] == events[0]["record_sha256"]
    finally:
        db.close()


@pytest.mark.parametrize("fault", ["clock", "insert"])
def test_failed_append_releases_its_lock_and_rolls_back(tmp_path, monkeypatch, fault) -> None:
    import holdspeak.kernel.journal_txn as journal_txn

    db = Database(tmp_path / "journal.db")
    store = JournalStore(db._connection)
    try:
        with monkeypatch.context() as patch:
            if fault == "clock":
                def broken_clock():
                    raise RuntimeError("clock failed")

                patch.setattr(store, "_clock", broken_clock)
                error = RuntimeError
            else:
                # A duplicate event id forces an actual SQLite INSERT error.
                store.append("operation.claimed", "op-first")
                existing_id = store.events(0, {})["events"][0]["event_id"]

                class RepeatedId:
                    hex = existing_id.removeprefix("evt_")

                patch.setattr(journal_txn.uuid, "uuid4", RepeatedId)
                error = sqlite3.IntegrityError
            before = store.events(0, {})["events"]
            with pytest.raises(error):
                store.append("operation.claimed", "op-failed")
        # Check before trying another append so a broken lock fails promptly.
        assert not store._append_lock.locked()
        assert store.events(0, {})["events"] == before
        result = store.append("operation.claimed", "op-after")
        assert result["stream_sequence"] == len(before) + 1
        assert store.verify()["records"] == len(before) + 1
    finally:
        db.close()
