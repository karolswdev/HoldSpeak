"""Append-only repository for ``ledger_entries``.

There is no ``update`` and no ``delete`` here on purpose. The only
write path is ``append``. Corrections are made by appending reversing
entries through ``ledger.reversal``. Money is stored as integer
``amount_minor``; positive on debit rows, negative on credit rows, so
a balanced group sums to zero.
"""
from __future__ import annotations

import sqlite3
import time
from contextlib import contextmanager

SCHEMA = """
CREATE TABLE IF NOT EXISTS ledger_entries (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id     TEXT    NOT NULL,
    account      TEXT    NOT NULL,
    side         TEXT    NOT NULL CHECK (side IN ('debit', 'credit')),
    amount_minor INTEGER NOT NULL,
    created_at   REAL    NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_entries_group ON ledger_entries(group_id);
CREATE INDEX IF NOT EXISTS ix_entries_account ON ledger_entries(account);
"""


class EntriesRepo:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn
        self.conn.executescript(SCHEMA)

    @contextmanager
    def transaction(self):
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            yield
            self.conn.execute("COMMIT")
        except Exception:
            self.conn.execute("ROLLBACK")
            raise

    def append(self, group_id: str, account: str, side: str, amount_minor: int) -> int:
        """Append one entry. The only write path into the ledger."""
        if not isinstance(amount_minor, int):
            raise TypeError("amount_minor must be an integer (minor units)")
        cur = self.conn.execute(
            "INSERT INTO ledger_entries (group_id, account, side, amount_minor, created_at)"
            " VALUES (?, ?, ?, ?, ?)",
            (group_id, account, side, amount_minor, time.time()),
        )
        return int(cur.lastrowid)

    def rows_for_group(self, group_id: str) -> list[dict]:
        rows = self.conn.execute(
            "SELECT id, group_id, account, side, amount_minor, created_at"
            " FROM ledger_entries WHERE group_id = ? ORDER BY id",
            (group_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def balance_of(self, account: str) -> int:
        row = self.conn.execute(
            "SELECT COALESCE(SUM(amount_minor), 0) AS bal"
            " FROM ledger_entries WHERE account = ?",
            (account,),
        ).fetchone()
        return int(row["bal"])

    def total_balance(self) -> int:
        """Sum the entire ledger. Must always be 0 if balanced."""
        row = self.conn.execute(
            "SELECT COALESCE(SUM(amount_minor), 0) AS bal FROM ledger_entries"
        ).fetchone()
        return int(row["bal"])
