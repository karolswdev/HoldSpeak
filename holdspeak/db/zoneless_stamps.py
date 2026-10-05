"""One-time repair: old zoneless stamps become UTC instants, in place.

Before 2026-10-05 most writers stored ``datetime.now().isoformat()``: a bare
ISO stamp on the hub's wall clock (``2026-10-05T21:32:00``). New writers store
an aware UTC instant (``2026-10-06T03:32:00+00:00``, ``holdspeak/timestamps.py``).
SQL compares stamps as text, and a bare local stamp sorts wrong against a UTC
one: in Denver an old queued retry ran up to six hours early.

This repair rewrites every bare stamp in a time column to the same instant in
UTC, so one column holds one shape again. Values only: no row is deleted or
added. It runs once per database (a milestone), at open, before any reader.

The hub's zone is the process's local zone, read per instant (DST-correct:
``datetime.astimezone`` uses the zone rules of that date). In the repeated
autumn hour a bare stamp is ambiguous; the first occurrence is taken, as the
readers always did.

Two columns held naive UTC, not local (browser visit times converted from the
browser's own epoch): ``activity_records.first_seen_at`` and ``last_seen_at``.
Their bare stamps get ``+00:00`` without a shift.
"""
from __future__ import annotations

import re
import sqlite3
from datetime import datetime, timezone

MILESTONE = "timestamps.zoneless_to_utc.v1"

#: A bare ISO date-time with no zone: the shape the old naive writers stored.
_BARE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2}(\.\d{1,6})?)?$")

#: A column is a time column by name.
_TIME_COLUMN = re.compile(r"(_at|^timestamp|^first_seen|^last_seen|_since|_until)$")

#: Time-named columns that hold a wall time the owner typed (a due date), a
#: calendar time already in UTC, or a meaning extracted from text (memory
#: facts). Their bare values are not a writer's clock and are left alone.
_NOT_A_CLOCK = frozenset({
    "due_at", "target_at", "start_at", "starts_at", "ends_at", "calendar_starts_at",
})

#: Bare stamps that were naive UTC, not local.
_BARE_IS_UTC = frozenset({
    ("activity_records", "first_seen_at"),
    ("activity_records", "last_seen_at"),
})


def time_columns(conn: sqlite3.Connection) -> list[tuple[str, str]]:
    """Every ``(table, column)`` that holds a writer's clock as TEXT."""
    found: list[tuple[str, str]] = []
    tables = [
        row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%' AND sql NOT LIKE 'CREATE VIRTUAL TABLE%'"
        )
    ]
    for table in tables:
        for column in conn.execute(f'PRAGMA table_info("{table}")'):
            name, declared = str(column[1]), str(column[2] or "").upper()
            if declared not in ("TEXT", ""):
                continue
            if name in _NOT_A_CLOCK or not _TIME_COLUMN.search(name):
                continue
            found.append((table, name))
    return found


def to_utc(value: str, *, bare_is_utc: bool = False) -> str:
    """A bare stamp as the same instant in UTC (``...+00:00``)."""
    naive = datetime.fromisoformat(value)
    aware = naive.replace(tzinfo=timezone.utc) if bare_is_utc else naive.astimezone()
    return aware.astimezone(timezone.utc).isoformat()


def zoneless_rows(conn: sqlite3.Connection) -> dict[tuple[str, str], int]:
    """How many bare stamps each time column still holds (the fence reads this)."""
    left: dict[tuple[str, str], int] = {}
    for table, column in time_columns(conn):
        values = conn.execute(
            f'SELECT "{column}" FROM "{table}" WHERE "{column}" GLOB ?',
            ("[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]*",),
        ).fetchall()
        count = sum(1 for (value,) in values if isinstance(value, str) and _BARE.match(value))
        if count:
            left[(table, column)] = count
    return left


def repair_zoneless_stamps(conn: sqlite3.Connection, *, force: bool = False) -> dict[tuple[str, str], int]:
    """Rewrite every bare stamp to UTC, once. Returns the rows changed per column.

    A table whose triggers refuse an UPDATE (an append-only ledger) is left
    as it is and named in the log; the repair goes on with the others.
    """
    from ..logging_config import get_logger

    log = get_logger("db.zoneless_stamps")
    if not force:
        done = conn.execute("SELECT 1 FROM milestones WHERE key = ?", (MILESTONE,)).fetchone()
        if done:
            return {}
    changed: dict[tuple[str, str], int] = {}
    for table, column in time_columns(conn):
        values = conn.execute(
            f'SELECT DISTINCT "{column}" FROM "{table}" WHERE "{column}" GLOB ?',
            ("[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]*",),
        ).fetchall()
        bare = [value for (value,) in values if isinstance(value, str) and _BARE.match(value)]
        if not bare:
            continue
        utc = (table, column) in _BARE_IS_UTC
        count = 0
        try:
            conn.execute("SAVEPOINT zoneless_stamps")
            for value in bare:
                cursor = conn.execute(
                    f'UPDATE "{table}" SET "{column}" = ? WHERE "{column}" = ?',
                    (to_utc(value, bare_is_utc=utc), value),
                )
                count += int(cursor.rowcount or 0)
            conn.execute("RELEASE zoneless_stamps")
        except sqlite3.DatabaseError as exc:
            conn.execute("ROLLBACK TO zoneless_stamps")
            conn.execute("RELEASE zoneless_stamps")
            log.warning("Zoneless stamps left in %s.%s: %s", table, column, exc)
            continue
        if count:
            changed[(table, column)] = count
    conn.execute(
        "INSERT OR IGNORE INTO milestones (key, achieved_at) VALUES (?, ?)",
        (MILESTONE, datetime.now(timezone.utc).isoformat()),
    )
    if changed:
        log.info("Zoneless stamps rewritten to UTC: %s", changed)
    return changed
