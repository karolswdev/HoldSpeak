"""Live-meeting lifecycle routes backed by :class:`MeetingService`."""
from __future__ import annotations

import asyncio
from typing import Any, Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ....logging_config import get_logger
from ....principals import UNAUTHENTICATED
from ....services.meeting_service import MeetingService
from ....services.errors import ValidationError
from ....web_requests import (
    _BookmarkRequest,
    _MeetingStartRequest,
    _StopRequest,
    _UpdateMeetingRequest,
)
from ...runtime_support import _UnknownDeviceError
from ...context import WebContext

log = get_logger("web.routes.meetings")

# The runtime's named refusal when a stop press finds no meeting running
# (`runtime/meeting_glue.py::_stop_active_meeting`). Matched on the message
# rather than the type so this transport adapter need not import the runtime.
_NO_ACTIVE_MEETING = "No active meeting"
_STOP_IN_PROGRESS = "Meeting is already stopping"


def _service(ctx: WebContext) -> MeetingService:
    """Get the composition-bound service, retaining partial-context support."""
    if isinstance(ctx.meeting_service, MeetingService):
        return ctx.meeting_service
    from ....db import get_database, get_observer

    def update_callback(*, title: str | None, tags: list[str] | None) -> Any:
        if ctx.on_update_meeting is not None:
            return ctx.on_update_meeting(title=title, tags=tags)
        if title is not None and ctx.on_set_title is not None:
            ctx.on_set_title(title)
        if tags is not None and ctx.on_set_tags is not None:
            ctx.on_set_tags(tags)
        return ctx.get_state() or {}

    service = MeetingService(get_database(), observer=get_observer())  # _service composition
    service.bind_lifecycle(
        on_start=ctx.on_start,
        on_stop=ctx.on_meeting_stop or ctx.on_stop,
        on_bookmark=ctx.on_bookmark,
        on_update=update_callback,
    )
    ctx.meeting_service = service
    return service


def _principal(request: Request):
    return getattr(request.state, "principal", UNAUTHENTICATED)


def build_live_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    @router.post("/api/bookmark")
    async def api_bookmark(
        request: Request, payload: Optional[_BookmarkRequest] = None
    ) -> Any:
        try:
            result = _service(ctx).bookmark(
                _principal(request), label=payload.label if payload else ""
            )
            if result is not None:
                ctx.broadcast("bookmark", result)
            return JSONResponse({"success": True})
        except Exception as exc:
            log.error("on_bookmark failed: %s", exc)
            return JSONResponse({"success": False, "error": str(exc)}, status_code=500)

    async def _stop(request: Request) -> Any:
        try:
            service = _service(ctx)
            stopped = await asyncio.to_thread(service.stop_capture, _principal(request))
            ctx.broadcast("stopped", stopped)
            # A stopped capture is a successful Stop even when persistence is
            # partial. Keep the runtime's facts together so clients can say
            # what stopped and what, if anything, was retained.
            result: dict[str, Any] = dict(stopped) if isinstance(stopped, dict) else {}
            result["success"] = True
            if isinstance(stopped, dict):
                meeting = stopped.get("meeting")
                save = stopped.get("save")
                if isinstance(meeting, dict) and isinstance(save, dict):
                    meeting_id = str(meeting.get("id") or meeting.get("meeting_id") or "")
                    checkpoint_candidate = (
                        save.get("database_saved") is False
                        and save.get("json_saved") is True
                        and str(meeting.get("capture_status") or "").lower() == "recoverable"
                    )
                    if meeting_id and checkpoint_candidate:
                        try:
                            retained = service.get_meeting(
                                _principal(request), meeting_id, include_parked=True
                            )
                        except Exception:
                            retained = None
                        # Recovery is a door only when the durable row exists;
                        # a Stop payload alone is not proof of recoverability.
                        result["capture_recovery_available"] = retained is not None
            if result.get("device_cleanup_error"):
                result["warning"] = result["device_cleanup_error"]
            return JSONResponse(result)
        except Exception as exc:
            # HS-132-02: HS-132-01 made the meeting verb refuse by name when no
            # meeting is live, but the refusal rode a 500 — a server fault for
            # what is a client asking to stop nothing. It is a conflict with the
            # current state, so it answers 409 and keeps the named reason.
            status = 409 if any(reason in str(exc) for reason in (_NO_ACTIVE_MEETING, _STOP_IN_PROGRESS)) else 500
            log.error("on_stop failed: %s", exc)
            return JSONResponse({"success": False, "error": str(exc)}, status_code=status)

    @router.post("/api/meeting/start")
    async def api_meeting_start(
        request: Request, payload: Optional[_MeetingStartRequest] = None
    ) -> Any:
        try:
            meeting = _service(ctx).start_capture(
                _principal(request),
                {
                    "devices": list(payload.devices) if payload and payload.devices else [],
                    "calendar_event_id": payload.calendar_event_id if payload else None,
                },
            )
        except ValidationError as exc:
            status = 409 if exc.code == "calendar_event_unavailable" else 501
            return JSONResponse({"success": False, "error": str(exc)}, status_code=status)
        except _UnknownDeviceError as exc:
            return JSONResponse(
                {"success": False, "error": str(exc), "device_id": exc.device_id},
                status_code=404,
            )
        except Exception as exc:
            log.error("on_start failed: %s", exc)
            return JSONResponse({"success": False, "error": str(exc)}, status_code=500)
        if meeting is not None:
            ctx.broadcast("meeting_started", meeting)
        return JSONResponse({"success": True, "meeting": meeting})

    @router.post("/api/meeting/stop")
    async def api_meeting_stop(request: Request, _: Optional[_StopRequest] = None) -> Any:
        return await _stop(request)

    @router.post("/api/stop")
    async def api_stop(request: Request, _: Optional[_StopRequest] = None) -> Any:
        return await _stop(request)

    @router.patch("/api/meeting")
    async def api_update_meeting(request: Request, payload: _UpdateMeetingRequest) -> Any:
        try:
            state = ctx.get_state() or {}
            meeting_id = str(state.get("id") or state.get("meeting_id") or "")
            meeting = _service(ctx).update_meeting(
                _principal(request), meeting_id, title=payload.title, tags=payload.tags
            )
            ctx.broadcast(
                "meeting_updated",
                {
                    "title": meeting.get("title"),
                    "tags": meeting.get("tags") if isinstance(meeting.get("tags"), list) else [],
                },
            )
            return JSONResponse({"success": True, "meeting": meeting})
        except Exception as exc:
            log.error("Failed to update meeting: %s", exc)
            return JSONResponse({"success": False, "error": str(exc)}, status_code=500)

    return router
