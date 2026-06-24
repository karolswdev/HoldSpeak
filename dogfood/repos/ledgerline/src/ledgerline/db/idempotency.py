"""The ``idempotency_keys`` store.

Maps a client-supplied ``Idempotency-Key`` to the result of its first
successful charge. ``lock`` serializes concurrent attempts for the
same key so two retries cannot both miss-then-post — the bug behind
LL-118. The UNIQUE constraint on ``key`` is the backstop if the lock
is ever bypassed.
"""
from __future__ import annotations

import sqlite3
import threading
import time
from contextlib import contextmanager

SCHEMA = """
CREATE TABLE IF NOT EXISTS idempotency_keys (
    key          TEXT    PRIMARY KEY,
    group_id     TEXT    NOT NULL,
    amount_minor INTEGER NOT NULL,
    created_at   REAL    NOT NULL
);
"""


class IdempotencyStore:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn
        self.conn.executescript(SCHEMA)
        self._locks: dict[str, threading.Lock] = {}
        self._guard = threading.Lock()

    @contextmanager
    def lock(self, key: str):
        with self._guard:
            lk = self._locks.setdefault(key, threading.Lock())
        lk.acquire()
        try:
            yield
        finally:
            lk.release()

    def get(self, key: str) -> dict | None:
        row = self.conn.execute(
            "SELECT key, group_id, amount_minor, created_at"
            " FROM idempotency_keys WHERE key = ?",
            (key,),
        ).fetchone()
        return dict(row) if row else None

    def record(self, key: str, *, group_id: str, amount_minor: int) -> None:
        # INSERT OR IGNORE + UNIQUE key is the last line of defense
        # against a double-post if two writers ever reach here.
        self.conn.execute(
            "INSERT OR IGNORE INTO idempotency_keys"
            " (key, group_id, amount_minor, created_at) VALUES (?, ?, ?, ?)",
            (key, group_id, amount_minor, time.time()),
        )
