"""Shared cron parsing utilities (HS-136-01).

Factored from workbench_conductor._cron_is_due so the scheduled-recording
conductor and future cron consumers share one parser.
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta, tzinfo
from typing import Optional


def _match_field(pattern: str, value: int) -> bool:
    """Check whether a single cron field matches a value."""
    if pattern == "*":
        return True
    if pattern.startswith("*/"):
        step = int(pattern[2:])
        return step > 0 and value % step == 0
    allowed: set[int] = set()
    for part in pattern.split(","):
        if "-" in part:
            lo, hi = part.split("-", 1)
            allowed.update(range(int(lo), int(hi) + 1))
        else:
            allowed.add(int(part))
    return value in allowed


def _cron_dow(dt: datetime) -> int:
    """Convert Python weekday (0=Mon) to cron weekday (0=Sun)."""
    return (dt.weekday() + 1) % 7


def cron_is_due(cron_expr: str, *, now: Optional[datetime] = None) -> bool:
    """Simple cron check: minute hour dom month dow.

    Weekday mapping: cron uses 0=Sunday, 1=Monday, ..., 6=Saturday.
    Python's weekday() uses 0=Monday, ..., 6=Sunday.
    """
    try:
        parts = cron_expr.strip().split()
        if len(parts) != 5:
            return False
        if now is None:
            now = datetime.now()
        fields = [
            (parts[0], now.minute),
            (parts[1], now.hour),
            (parts[2], now.day),
            (parts[3], now.month),
            (parts[4], _cron_dow(now)),
        ]
        for pattern, value in fields:
            if not _match_field(pattern, value):
                return False
        return True
    except (ValueError, IndexError):
        return False


def resolve_tz(tz_name: Optional[str]) -> tzinfo:
    """A schedule's IANA zone name as a tzinfo; UTC when absent or unknown."""
    if not tz_name or str(tz_name).upper() == "UTC":
        return timezone.utc
    try:
        from zoneinfo import ZoneInfo

        return ZoneInfo(str(tz_name))
    except Exception:
        return timezone.utc


def next_cron_fire_in_zone(
    cron_expr: str, tz_name: Optional[str], *, now_epoch: Optional[float] = None
) -> Optional[float]:
    """The next fire (epoch seconds) of a cron written in the schedule's zone.

    The cron fields are wall-clock values in ``tz_name``: "32 21 * * *" with
    America/Denver fires at 21:32 in Denver, not at 21:32 UTC.
    """
    zone = resolve_tz(tz_name)
    after = (
        datetime.fromtimestamp(now_epoch, tz=zone)
        if now_epoch is not None
        else datetime.now(zone)
    )
    return next_cron_fire(cron_expr, after=after)


def next_cron_fire(cron_expr: str, *, after: Optional[datetime] = None) -> Optional[float]:
    """Compute the next fire time (epoch seconds) strictly after ``after``.

    Scans minute-by-minute up to 400 days. Returns None for invalid expressions.

    Known: during a DST fall-back repeated hour, a short-interval schedule
    CAN fire twice (standard cron semantics). Accepted, not mitigated.
    """
    try:
        parts = cron_expr.strip().split()
        if len(parts) != 5:
            return None
    except (ValueError, AttributeError):
        return None
    if after is None:
        after = datetime.now(timezone.utc)
    # Start from the next full minute
    candidate = after.replace(second=0, microsecond=0) + timedelta(minutes=1)
    limit = after + timedelta(days=400)
    while candidate < limit:
        if cron_is_due(cron_expr, now=candidate):
            return candidate.timestamp()
        candidate += timedelta(minutes=1)
    return None
