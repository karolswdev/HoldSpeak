"""HS-175-02: Calendar event API routes.

POST /api/calendar/events/{id}/link -- manually link an event to a Room.
DELETE /api/calendar/events/{id}/link -- remove a manual link.
GET /api/calendar/events -- list events for a date range.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Body, Query, Request
from fastapi.responses import JSONResponse

from ...db import get_database, get_observer
from ..context import WebContext


def build_calendar_events_router(ctx: WebContext) -> APIRouter:
    router = APIRouter(prefix="/api/calendar/events", tags=["calendar-events"])

    @router.get("")
    async def list_events(
        request: Request,
        start: str | None = Query(default=None),
        end: str | None = Query(default=None),
    ) -> Any:
        """List calendar events in a date range (default: next 7 days)."""
        db = get_database()
        now = datetime.now(timezone.utc)
        if start:
            start_iso = start
        else:
            start_iso = now.isoformat(timespec="seconds").replace("+00:00", "Z")
        if end:
            end_iso = end
        else:
            end_iso = (now + timedelta(days=7)).isoformat(timespec="seconds").replace("+00:00", "Z")
        events = db.calendar_events.list_in_range(start_iso, end_iso)
        # Build project index for Room links.
        try:
            project_index = db.calendar_event_projects.build_event_project_index()
        except Exception:
            project_index = {}
        items = []
        for event in events:
            item: dict[str, Any] = {
                "id": event.id,
                "uid": event.uid,
                "title": event.title,
                "starts_at": event.starts_at,
                "ends_at": event.ends_at,
                "location": event.location,
                "meeting_url": event.meeting_url,
                "source_id": event.source_id,
                "source_label": event.source_label,
            }
            room = project_index.get(event.id)
            if room:
                item["project_id"] = room[0]
                item["project_name"] = room[1]
            items.append(item)
        return JSONResponse({"events": items})

    @router.post("/{event_id}/link")
    async def link_event(
        request: Request,
        event_id: str,
        body: dict[str, Any] = Body(default={}),
    ) -> Any:
        """Manually link a calendar event to a Room (project)."""
        db = get_database()
        project_id = body.get("project_id", "")
        if not project_id:
            return JSONResponse(
                {"detail": "project_id is required"}, status_code=400,
            )
        # Verify event exists.
        event = db.calendar_events.get(event_id)
        if event is None:
            return JSONResponse(
                {"detail": "calendar event not found"}, status_code=404,
            )
        db.calendar_event_projects.link(event_id, project_id, "manual")
        # Receipt via pipeline event (ledger, not gate).
        _write_link_receipt(event_id, project_id, "link")
        return JSONResponse({"linked": True, "event_id": event_id, "project_id": project_id})

    @router.delete("/{event_id}/link")
    async def unlink_event(
        request: Request,
        event_id: str,
        body: dict[str, Any] = Body(default={}),
    ) -> Any:
        """Remove a manual link between a calendar event and a Room."""
        db = get_database()
        project_id = body.get("project_id", "")
        if not project_id:
            # Unlink all for this event.
            count = db.calendar_event_projects.unlink_event(event_id)
        else:
            count = db.calendar_event_projects.unlink(event_id, project_id)
        _write_link_receipt(event_id, project_id or "*", "unlink")
        return JSONResponse({"unlinked": count, "event_id": event_id})

    return router


def _write_link_receipt(event_id: str, project_id: str, action: str) -> None:
    """Write a pipeline event for the manual link/unlink (ledger, not gate)."""
    from ...services.observer import PipelineEvent

    try:
        event = PipelineEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).timestamp(),
            service="CalendarEventLink",
            method=action,
            principal_kind="owner",
            principal_identity="calendar-event-link",
            args_summary=json.dumps({"event_id": event_id, "project_id": project_id}),
            result_summary=json.dumps({"action": action}),
            error=None,
            error_code=None,
            duration_ms=0.0,
            correlation_id=str(uuid.uuid4()),
            is_async=False,
            origin="local",
            caller="",
            caller_identity="",
        )
        obs = get_observer()
        if obs:
            obs.on_event(event)
    except Exception:
        pass
