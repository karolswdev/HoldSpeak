"""SQLite repositories — the system of record.

The database runs in WAL mode with a single writer. Two tables
matter: ``ledger_entries`` (append-only, owned by
``entries.EntriesRepo``) and ``idempotency_keys`` (owned by
``idempotency.IdempotencyStore``).
"""
import sqlite3


def connect(path: str = "ledgerline.db") -> sqlite3.Connection:
    conn = sqlite3.connect(path, isolation_level=None, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn
