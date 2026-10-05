"""One clock for stored times.

Every stamp HoldSpeak stores (a DB row, a file, a wire frame) is an aware UTC
instant: ``utc_now()`` / ``utc_now_iso()``. Local wall-clock reads (quiet
hours, the local week, a display, a file name) use ``local_now()``, which is
aware too. A zero-arg ``datetime.now()`` is fenced
(``tests/unit/test_aware_time_census.py``).

Old rows hold three shapes, read by ``parse_stamp`` exactly as
``db/projections.py`` reads them for the wire:

- a SQLite stamp ``YYYY-MM-DD HH:MM:SS`` (``CURRENT_TIMESTAMP``) is UTC;
- an ISO string with an offset or ``Z`` is exact;
- a bare ISO string ``YYYY-MM-DDTHH:MM:SS`` (the old
  ``datetime.now().isoformat()``) is the hub's LOCAL wall time.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional

__all__ = [
    "utc_now", "utc_now_iso", "utc_iso", "local_now", "local_wall", "parse_stamp", "aware",
    "sql_window", "in_window", "parse_wall",
]


def utc_now() -> datetime:
    """Now, as an aware UTC datetime."""
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    """Now, as an aware UTC ISO string (``...+00:00``)."""
    return datetime.now(timezone.utc).isoformat()


def utc_iso(value: Optional[datetime] = None) -> str:
    """``value`` (naive = hub-local) or now, as an aware UTC ISO string."""
    if value is None:
        return utc_now_iso()
    return aware(value).astimezone(timezone.utc).isoformat()


def local_now() -> datetime:
    """Now on the hub's wall clock, aware (carries the local offset)."""
    return datetime.now().astimezone()


def local_wall() -> datetime:
    """Now on the hub's wall clock, NAIVE: only for a read that compares
    against naive local values (a parsed legacy stamp, a quiet-hours clock).
    Never store it: a stored stamp is ``utc_now_iso()``."""
    return datetime.now().astimezone().replace(tzinfo=None)


def aware(value: datetime) -> datetime:
    """A datetime made aware: a naive value is hub-local wall time."""
    if value.tzinfo is None:
        return value.astimezone()
    return value


def parse_stamp(value: Any) -> Optional[datetime]:
    """A stored stamp (any of the three shapes) as an aware datetime.

    The result is aware and on the hub's local offset. Returns None for an
    empty or unreadable value. A ``datetime`` passes through ``aware``; a
    ``date`` is local midnight.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return aware(value)
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day).astimezone()
    clean = str(value).strip()
    if not clean:
        return None
    sqlite_utc = "T" not in clean and " " in clean
    if sqlite_utc:
        clean = clean.replace(" ", "T", 1)
    if clean.endswith("Z") or clean.endswith("z"):
        clean = clean[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(clean)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc) if sqlite_utc else parsed.astimezone()
    # The same instant on the hub's wall clock, so a face that formats it
    # (``strftime``) prints local time, as it did for the old naive rows.
    return parsed.astimezone()


_PAD = timedelta(days=1)


def sql_window(start: Any, end: Any) -> tuple[str, str]:
    """Text bounds for a SQL prefilter over a column of mixed stamp shapes.

    Old rows hold local wall time, new rows UTC; the two differ by at most a
    day, so the bounds are padded by one day. The caller then keeps a row only
    when ``in_window`` says its instant is inside: text order is never trusted.
    """
    lo = parse_stamp(start)
    hi = parse_stamp(end)
    fmt = "%Y-%m-%dT%H:%M:%S"
    lo_text = (lo - _PAD).astimezone(timezone.utc).strftime(fmt) if lo else ""
    hi_text = (hi + _PAD).astimezone(timezone.utc).strftime(fmt) if hi else "9999"
    return lo_text, hi_text


def in_window(value: Any, start: Any, end: Any) -> bool:
    """True when the stamp's instant is inside [start, end] (inclusive)."""
    stamp = parse_stamp(value)
    if stamp is None:
        return False
    lo = parse_stamp(start)
    hi = parse_stamp(end)
    if lo is not None and stamp < lo:
        return False
    if hi is not None and stamp > hi:
        return False
    return True


def parse_wall(value: Any) -> Optional[datetime]:
    """A stored stamp as a NAIVE hub-local wall time: the in-memory form the
    repositories hand out (models and their callers compare naive values).
    Writing it back through ``utc_iso`` stores the same instant in UTC."""
    stamp = parse_stamp(value)
    if stamp is None:
        return None
    return stamp.astimezone().replace(tzinfo=None)
