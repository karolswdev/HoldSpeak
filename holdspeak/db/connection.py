"""Connection factory for HoldSpeak's SQLite persistence layer (HS-117-12).

Extracted from ``Database`` so the connection protocol (WAL pragmas, row factory,
commit/rollback) lives in one place. The ``Database`` container delegates to
:func:`make_connection_factory`.
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


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


def make_connection_factory(db_path: Path):
    """Return a zero-arg callable that produces a connection context manager.

    This is the callable stored as ``self._connection`` on every repository:
    ``with self._connection() as conn: ...``.
    """

    @contextmanager
    def _factory() -> Iterator[sqlite3.Connection]:
        with connection(db_path) as conn:
            yield conn

    return _factory
