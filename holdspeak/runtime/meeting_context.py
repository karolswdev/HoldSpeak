"""Consume pending meeting metadata before a capture admission attempt."""
from __future__ import annotations

from typing import Any


def consume_meeting_context(
    runtime: Any,
    *,
    principal: object | None,
    calendar_event_id: str | None,
) -> tuple[str | None, list[str] | None, str | None]:
    """Keep scheduler metadata out of an overlapping direct owner start.

    Pending context is consumed even when admission later refuses capture.
    Idle owner title/tag edits still apply when no scheduled event is pending.
    """
    principal_kind = getattr(
        getattr(principal, "kind", None),
        "value",
        getattr(principal, "kind", None),
    )
    scheduled_start = principal_kind == "scheduler"
    with runtime.state_lock:
        pending_title = runtime.pending_title
        pending_calendar_event_id = runtime.pending_calendar_event_id
        pending_tags = (
            list(runtime.pending_tags) if runtime.pending_tags is not None else None
        )
        runtime.pending_title = None
        runtime.pending_calendar_event_id = None
        runtime.pending_tags = None
    pending_calendar = str(pending_calendar_event_id or "").strip() or None
    scheduler_context = pending_calendar is not None
    title_override = (
        pending_title if scheduled_start or not scheduler_context else None
    )
    tags_override = (
        pending_tags if scheduled_start or not scheduler_context else None
    )
    calendar_event_id_override = str(
        calendar_event_id
        or (pending_calendar if scheduled_start else "")
        or ""
    ).strip() or None
    return title_override, tags_override, calendar_event_id_override
