"""Connection factory for HoldSpeak's SQLite persistence layer (HS-117-12).

Extracted from ``Database`` so the connection protocol (WAL pragmas, row factory,
commit/rollback) lives in one place. The ``Database`` container delegates to
:func:`make_connection_factory`.
"""
from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional


@contextmanager
def connection(db_path: Path) -> Iterator[sqlite3.Connection]:
    """Context manager for a single database connection.

    Creates the parent directory if needed, sets ``row_factory`` to
    :class:`sqlite3.Row`, enables foreign keys, and commits on clean exit /
    rolls back on exception.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _open(db_path: Path) -> sqlite3.Connection:
    """Open one connection with the protocol :func:`connection` applies."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


class ConnectionCache:
    """One reusable connection per (cache instance, thread) — HS-131-09.

    A fresh SQLite connection's *first* statement has to parse HoldSpeak's
    356-object schema (~0.9ms), so an admission that opens two dozen
    short-lived connections pays ~26ms of pure schema parsing. This cache keeps
    one warm connection per thread so that cost is paid once.

    Scope is deliberately **per instance**, never global or per-process: each
    :class:`~holdspeak.db.core.Database` owns exactly one cache, so a new
    ``Database`` over the same file (a restart, or the next test) shares no
    connection and therefore no uncommitted state or stale file handle.

    Transaction semantics are unchanged from :func:`connection`: the context
    manager commits on clean exit and rolls back on exception. Re-entrancy is
    preserved too — if this thread's cached connection is already checked out
    (a nested ``with self._connection()``), the nested call gets its own fresh
    short-lived connection, exactly as before the cache existed.
    """

    #: Cap on cached connections; keyed by thread id, so this bounds the leak
    #: from short-lived worker threads that die without a checkin.
    max_entries = 8

    def __init__(self, db_path: Path):
        self._db_path = db_path
        self._lock = threading.Lock()
        self._idle: dict[int, sqlite3.Connection] = {}
        self._busy: set[int] = set()
        self._closed = False

    # -- checkout / checkin ------------------------------------------------
    def _checkout(self) -> Optional[sqlite3.Connection]:
        """Claim this thread's cached connection, or None if unavailable."""
        tid = threading.get_ident()
        with self._lock:
            if self._closed or tid in self._busy:
                return None  # nested call (or closed cache): caller opens fresh
            conn = self._idle.get(tid)
            if conn is None:
                self._evict_locked(keep=tid)
                if len(self._idle) >= self.max_entries:
                    # Every entry is BUSY, so nothing can be evicted. The cap is
                    # a cap: this thread opens a fresh short-lived connection
                    # instead of growing the cache without bound.
                    return None
                conn = _open(self._db_path)
                self._idle[tid] = conn
            self._busy.add(tid)
            return conn

    def _checkin(self, *, discard: bool) -> None:
        tid = threading.get_ident()
        conn: Optional[sqlite3.Connection] = None
        with self._lock:
            self._busy.discard(tid)
            if discard:
                conn = self._idle.pop(tid, None)
        if conn is not None:
            _close_quietly(conn)

    def _evict_locked(self, *, keep: int) -> None:
        """Drop idle entries until there is room for one more. Lock held."""
        if len(self._idle) < self.max_entries:
            return
        for tid in list(self._idle):
            if tid == keep or tid in self._busy:
                continue
            _close_quietly(self._idle.pop(tid))
            if len(self._idle) < self.max_entries:
                return

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        """Yield a connection with :func:`connection`'s exact semantics."""
        conn = self._checkout()
        if conn is None:
            with connection(self._db_path) as fresh:
                yield fresh
            return
        try:
            yield conn
            conn.commit()
        except BaseException:
            broken = False
            try:
                conn.rollback()
            except Exception:
                broken = True  # unusable connection: do not hand it out again
            self._checkin(discard=broken)
            raise
        else:
            self._checkin(discard=False)

    def close(self) -> None:
        """Close every cached connection; further checkouts open fresh ones."""
        with self._lock:
            self._closed = True
            conns = list(self._idle.values())
            self._idle.clear()
        for conn in conns:
            _close_quietly(conn)


def _close_quietly(conn: sqlite3.Connection) -> None:
    # A connection created on another (possibly dead) thread refuses close()
    # here; dropping the reference lets CPython's deallocator finish the job.
    try:
        conn.close()
    except Exception:
        pass


def make_connection_factory(db_path: Path, cache: Optional[ConnectionCache] = None):
    """Return a zero-arg callable that produces a connection context manager.

    This is the callable stored as ``self._connection`` on every repository:
    ``with self._connection() as conn: ...``. When ``cache`` is given the
    factory reuses that cache's warm per-thread connection; without one it
    opens a short-lived connection per call.
    """
    if cache is not None:
        return cache.connection

    @contextmanager
    def _factory() -> Iterator[sqlite3.Connection]:
        with connection(db_path) as conn:
            yield conn

    return _factory
