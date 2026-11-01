"""Wall-clock times on a local day, with the offset that day has.

``local.replace(hour=13)`` keeps the offset of ``local``: on the day the
clocks change (2026-11-01 in America/Denver, the repeated 01:00 hour) "At
13:00" from 00:30 MDT came out 12:00 MST, and "tomorrow at 07:00" from the
evening before came out 06:00. These helpers build the wall time on the
date first, then give it the zone's offset for that date and hour.
"""
from __future__ import annotations

from datetime import datetime, timedelta


def at_local(moment: datetime, hour: int, minute: int = 0, *, days: int = 0) -> datetime:
    """``hour:minute`` on ``moment``'s local date (plus ``days``), aware, with
    the offset the local zone has at that wall time."""
    day = moment.astimezone().date() + timedelta(days=days)
    return datetime(day.year, day.month, day.day, int(hour) % 24, int(minute)).astimezone()


def next_local(moment: datetime, hour: int, minute: int = 0) -> datetime:
    """The next ``hour:minute`` after ``moment`` (today's, else tomorrow's)."""
    at = at_local(moment, hour, minute)
    return at if at > moment.astimezone() else at_local(moment, hour, minute, days=1)


__all__ = ["at_local", "next_local"]
