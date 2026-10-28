"""Retention for ``pipeline_events``: old READ receipts go, WRITE receipts stay.

PERF-HUB 2026-10-28: every public service call writes one pipeline event, and
nothing pruned them. On the owner's desk the table held 1.39 M rows (2.2 GB of
a 2.36 GB database); 93 % were read receipts (``list_meetings``, ``board``,
``proposal_needs`` ...). A read receipt older than the retention window is
deleted; a write receipt is kept forever (the Room's receipts ARE its writes).

The read set is defined here, in ONE place: a method is a read when its name is
in :data:`READ_METHOD_NAMES` or starts with one of
:data:`READ_METHOD_PREFIXES`. Every other method is a write and is kept.

Deletes run in batches of :data:`BATCH_SIZE` rows by rowid, each batch its own
short transaction, in a daemon thread (never on the hub's event loop): once
shortly after the hub is up, then once a day.

``HOLDSPEAK_EVENT_RETENTION_DAYS`` sets the window (default 14); ``0`` keeps
everything.
"""

from __future__ import annotations

import logging
import os
import sqlite3
import threading
import time
from typing import Any, Callable, Optional

log = logging.getLogger(__name__)

#: Exact method names that only read.
READ_METHOD_NAMES: frozenset[str] = frozenset({
    "room", "board", "status", "needs_you", "proposal_needs",
    "people_store_state", "pull", "process_pending", "refresh_due_watches",
    "standing_pages", "list", "is_stale",
})

#: Name prefixes that only read (``list_meetings``, ``get_project``,
#: ``search_notes``, ``preview_send`` ...).
READ_METHOD_PREFIXES: tuple[str, ...] = ("list_", "get_", "search", "preview")

DEFAULT_RETENTION_DAYS = 14
BATCH_SIZE = 5000
#: First prune waits this long after the hub is up, so boot stays quick.
FIRST_RUN_DELAY_S = 60.0
INTERVAL_S = 24 * 3600.0

_thread: Optional[threading.Thread] = None
_thread_lock = threading.Lock()


def is_read_method(method: str) -> bool:
    """True when a pipeline event of ``method`` is a read receipt."""
    from holdspeak.services.project_service import ROOM_WRITE_METHODS

    if method in ROOM_WRITE_METHODS:
        return False
    return method in READ_METHOD_NAMES or method.startswith(READ_METHOD_PREFIXES)


def retention_days() -> int:
    """The window from ``HOLDSPEAK_EVENT_RETENTION_DAYS`` (default 14; 0 = keep all)."""
    raw = os.environ.get("HOLDSPEAK_EVENT_RETENTION_DAYS", "").strip()
    if not raw:
        return DEFAULT_RETENTION_DAYS
    try:
        return max(0, int(raw))
    except ValueError:
        log.warning("HOLDSPEAK_EVENT_RETENTION_DAYS=%r is not a number; using %d",
                    raw, DEFAULT_RETENTION_DAYS)
        return DEFAULT_RETENTION_DAYS


def prune_read_events(
    connection: Callable[..., Any],
    *,
    days: Optional[int] = None,
    now: Optional[float] = None,
    batch_size: int = BATCH_SIZE,
    pause_s: float = 0.0,
) -> int:
    """Delete read receipts older than ``days``; return how many rows went.

    ``connection`` is a ``Database._connection``-style context manager factory
    (commit on clean exit). Each batch reads ``batch_size`` rows by rowid,
    keeps the writes and deletes the reads, in its own transaction.
    """
    window = retention_days() if days is None else days
    if window <= 0:
        return 0
    cutoff = (time.time() if now is None else now) - window * 86400
    with connection() as conn:
        # +id keeps SQLite off its MAX(rowid) shortcut (a walk down from the
        # newest row); the timestamp index covers rowid, so this reads only
        # the old range of that index.
        row = conn.execute(
            "SELECT MAX(+id) FROM pipeline_events WHERE timestamp < ?",
            (cutoff,),
        ).fetchone()
    if row is None or row[0] is None:
        return 0
    # The highest old id bounds the walk, so the newest rows (the bulk of the
    # desk's reads) are never scanned.
    max_id = int(row[0])
    last_id = 0
    deleted = 0
    while last_id < max_id:
        with connection() as conn:
            rows = conn.execute(
                "SELECT id, method, timestamp FROM pipeline_events "
                "WHERE id > ? AND id <= ? ORDER BY id LIMIT ?",
                (last_id, max_id, batch_size),
            ).fetchall()
            if not rows:
                break
            last_id = int(rows[-1][0])
            doomed = [int(r[0]) for r in rows
                      if float(r[2]) < cutoff and is_read_method(str(r[1]))]
            if doomed:
                marks = ",".join("?" for _ in doomed)
                conn.execute(f"DELETE FROM pipeline_events WHERE id IN ({marks})", doomed)
                deleted += len(doomed)
        if pause_s:
            time.sleep(pause_s)
    return deleted


def _loop(connection: Callable[..., Any], first_delay_s: float, interval_s: float) -> None:
    delay = first_delay_s
    while True:
        time.sleep(delay)
        delay = interval_s
        try:
            started = time.monotonic()
            gone = prune_read_events(connection, pause_s=0.02)
            if gone:
                log.info("Pipeline event retention: removed %d read receipts in %.1f s",
                         gone, time.monotonic() - started)
        except sqlite3.OperationalError as exc:
            if "no such table" not in str(exc):
                log.warning("Pipeline event retention failed: %s", exc)
            # else: the database went away under the thread (a closed test hub).
        except Exception:
            log.warning("Pipeline event retention failed", exc_info=True)


def start_retention(
    connection: Callable[..., Any],
    *,
    first_delay_s: float = FIRST_RUN_DELAY_S,
    interval_s: float = INTERVAL_S,
) -> Optional[threading.Thread]:
    """Start the daily prune thread once per process; None when retention is off."""
    global _thread
    if retention_days() <= 0:
        log.info("Pipeline event retention is OFF (HOLDSPEAK_EVENT_RETENTION_DAYS=0).")
        return None
    with _thread_lock:
        if _thread is not None and _thread.is_alive():
            return _thread
        _thread = threading.Thread(
            target=_loop,
            args=(connection, first_delay_s, interval_s),
            name="HoldSpeakEventRetention",
            daemon=True,
        )
        _thread.start()
        return _thread
