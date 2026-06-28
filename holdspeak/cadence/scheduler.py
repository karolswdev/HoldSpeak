"""The scheduler (CAD-1-04) — decides which loops are DUE to nudge now.

Pure given `now`. Respects: terminal/needs_review suppression, snooze, quiet hours
(default-on), a per-loop repeat window scaled by the `pressure` setting, and the
daily nudge cap. Phase 1 returns the due set; rendering/delivery is Phase 2+.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from .models import OpenLoop

# Base repeat window (hours) before the same loop is eligible to nudge again.
_BASE_REPEAT_HOURS = 4.0
_PRESSURE_MULT = {"gentle": 2.0, "normal": 1.0, "aggressive": 0.5}


@dataclass
class SchedulerConfig:
    """The subset of CadenceConfig the scheduler needs (kept pure/injectable)."""

    pressure: str = "normal"
    quiet_hours_start: int = 22
    quiet_hours_end: int = 8
    max_nudges_per_day: int = 12


def in_quiet_hours(now: datetime, start: int, end: int) -> bool:
    """Is `now` inside the quiet window [start, end) on a 24h clock (wraps midnight)?"""
    h = now.hour
    if start == end:
        return False
    if start < end:
        return start <= h < end
    return h >= start or h < end  # wraps midnight (e.g. 22 → 8)


def _repeat_hours(pressure: str) -> float:
    return _BASE_REPEAT_HOURS * _PRESSURE_MULT.get(pressure, 1.0)


def _parse(ts: Optional[str]) -> Optional[datetime]:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts)
    except ValueError:
        return None


def due_loops(
    loops: list[OpenLoop],
    *,
    now: datetime,
    config: SchedulerConfig,
    nudged_today: int = 0,
) -> list[OpenLoop]:
    """Return the loops that should be nudged now, highest staleness first.

    `loops` is expected to already exclude closed/killed (the repo's default list).
    """
    if config.max_nudges_per_day and nudged_today >= config.max_nudges_per_day:
        return []
    if in_quiet_hours(now, config.quiet_hours_start, config.quiet_hours_end):
        return []  # Phase 1 has no urgent agent-blocker exception yet (Phase 3)

    repeat = _repeat_hours(config.pressure)
    eligible: list[OpenLoop] = []
    for loop in loops:
        if loop.status in ("closed", "killed", "delegated"):
            continue
        if loop.needs_review:
            continue  # low-confidence: surfaced in the queue, never a push
        snoozed = _parse(loop.snoozed_until)
        if loop.status == "snoozed" and snoozed and snoozed > now:
            continue
        last = _parse(loop.last_nudged_at)
        if last is not None and (now - last).total_seconds() < repeat * 3600.0:
            continue
        eligible.append(loop)

    eligible.sort(key=lambda l: l.stale_score, reverse=True)
    if config.max_nudges_per_day:
        room = max(0, config.max_nudges_per_day - nudged_today)
        return eligible[:room]
    return eligible
