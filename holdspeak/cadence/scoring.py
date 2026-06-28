"""Stale-scoring v1 (CAD-1-03) — deterministic and explainable.

A pure function: given a loop, the current time, and a small `signals` struct the
collector assembles, return a `ScoreBreakdown` (the total AND the per-signal
contributions, so every nudge can say *why*). No clock or randomness inside — `now`
is injected. No LLM. The weights are the single tuning surface.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from .models import OpenLoop, ScoreBreakdown

# The single tuning surface (design §7.1). Positive = more urgent.
W_PRIORITY = {"low": 0.0, "normal": 4.0, "high": 9.0, "urgent": 16.0}
W_AGE_PER_DAY = 1.5          # per day since created, capped
W_AGE_CAP = 12.0
W_ACCEPTED_UNEXECUTED = 10.0  # an accepted action not yet filed/executed
W_UNOWNED = 5.0               # nobody owns it
W_RECURRENCE_PER = 4.0        # appears across N related meetings
W_SOURCE = {                  # which source it came from
    "agent_question": 20.0,   # a coding agent is blocked on you (Phase 3 populates)
    "proposal": 7.0,
    "meeting_action": 3.0,
    "meeting_decision": 3.0,
    "activity_record": 1.0,
    "manual": 2.0,
    "system": 0.0,
}
W_RECENT_ACTIVITY = 6.0       # touched today ⇒ alive ⇒ surface it (boost, not suppress)
W_NEEDS_REVIEW = 14.0         # low-confidence ⇒ strongly suppress (never a push)
W_DISMISS_PER = 5.0           # user dismissed it before ⇒ suppress


@dataclass
class LoopSignals:
    """The collector-assembled context the scorer needs (no DB access in scoring)."""

    accepted_unexecuted: bool = False
    unowned: bool = False
    recurrence_count: int = 0       # # of related meetings it appears across (beyond the first)
    recent_activity: bool = False   # related project touched today
    dismissals: int = 0             # prior dismissals of this loop
    age_days: float = 0.0


def _age_days(loop: OpenLoop, now: datetime) -> float:
    if not loop.created_at:
        return 0.0
    try:
        created = datetime.fromisoformat(loop.created_at)
    except ValueError:
        return 0.0
    return max(0.0, (now - created).total_seconds() / 86400.0)


def score_loop(
    loop: OpenLoop, *, now: datetime, signals: Optional[LoopSignals] = None
) -> ScoreBreakdown:
    """Deterministic staleness score + the per-signal breakdown."""
    s = signals or LoopSignals()
    age_days = s.age_days or _age_days(loop, now)
    c: dict[str, float] = {}

    c["priority"] = W_PRIORITY.get(loop.priority, 0.0)
    c["age"] = min(W_AGE_CAP, W_AGE_PER_DAY * age_days)
    c["source"] = W_SOURCE.get(loop.source_type, 0.0)
    if s.accepted_unexecuted:
        c["accepted_unexecuted"] = W_ACCEPTED_UNEXECUTED
    if s.unowned:
        c["unowned"] = W_UNOWNED
    if s.recurrence_count > 0:
        c["recurrence"] = W_RECURRENCE_PER * s.recurrence_count
    if s.recent_activity:
        c["recent_activity"] = W_RECENT_ACTIVITY
    if loop.needs_review:
        c["needs_review"] = -W_NEEDS_REVIEW
    if s.dismissals > 0:
        c["dismissals"] = -W_DISMISS_PER * s.dismissals

    total = round(sum(c.values()), 2)
    return ScoreBreakdown(total=total, contributions=dict(c))
