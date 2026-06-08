"""The pending dictation selection pin (Phase 53, HS-53-07).

When a user clicks **Dictate with this** on an activity nudge, the chosen
``ActivityRecord`` id is parked here — process-local, one-shot, recency-bounded —
so the *next* dictation run picks it up and folds that record into the rewrite
context. This is the seam that closes the pre-briefing loop: the nudge UI sets
the pin (``set_selected_record``), the live dictation runner consumes it
(``consume_selected_record``), and the project-rewriter names the record to the
model.

Why process-local rather than the DB: the pin is ephemeral intent (it lives for
the few seconds between a click and the next utterance), the web server and the
dictation runner share one process, and a pin that survived a restart would be a
surprise, not a feature. It mirrors the recency-bounded
``get_recent_awaiting_agent_session`` lookup the agent-reply path already uses.

Consumption is destructive and bounded: ``consume_selected_record`` returns the
id once and clears it, and a pin older than ``max_age_seconds`` is dropped
unused (a stale click never leaks into an unrelated dictation later).
"""

from __future__ import annotations

import threading
from datetime import datetime
from typing import Optional

# Default freshness window: a pin must be consumed within this many seconds of
# the click or it is dropped unused. Generous enough to cover "click the nudge,
# then start talking", tight enough that a forgotten click does not haunt a
# dictation minutes later.
DEFAULT_MAX_AGE_SECONDS = 300

_lock = threading.Lock()
_pending: Optional[tuple[int, datetime]] = None


def set_selected_record(record_id: int, *, now: Optional[datetime] = None) -> None:
    """Park a record id as the selection for the next dictation.

    A non-integer id is ignored (the pin is left untouched) — the engine never
    fabricates a selection. Setting a new id replaces any prior pending pin.
    """
    global _pending
    try:
        clean = int(record_id)
    except (TypeError, ValueError):
        return
    with _lock:
        _pending = (clean, now or datetime.now())


def consume_selected_record(
    *,
    max_age_seconds: int = DEFAULT_MAX_AGE_SECONDS,
    now: Optional[datetime] = None,
) -> Optional[int]:
    """Return the pending selection id once, then clear it.

    Returns ``None`` when nothing is pending or when the pin is older than
    ``max_age_seconds`` (a stale pin is dropped, not returned). The pin is
    one-shot: a second call without a fresh ``set_selected_record`` returns
    ``None``.
    """
    global _pending
    with _lock:
        if _pending is None:
            return None
        record_id, at = _pending
        _pending = None  # one-shot: clear whether fresh or stale
    age = ((now or datetime.now()) - at).total_seconds()
    if age > max(0, int(max_age_seconds)):
        return None
    return record_id


def peek_selected_record() -> Optional[int]:
    """Return the pending id without consuming it (None when empty). For tests/UI."""
    with _lock:
        return _pending[0] if _pending is not None else None


def clear_selected_record() -> None:
    """Drop any pending selection (the nudge UI's Clear button)."""
    global _pending
    with _lock:
        _pending = None


__all__ = [
    "DEFAULT_MAX_AGE_SECONDS",
    "set_selected_record",
    "consume_selected_record",
    "peek_selected_record",
    "clear_selected_record",
]
