"""Live-meeting lifecycle routes backed by :class:`MeetingService`."""
from __future__ import annotations

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

    def _stop(request: Request) -> Any:
        try:
            stopped = _service(ctx).stop_capture(_principal(request))
            ctx.broadcast("stopped", stopped)
            return JSONResponse({"success": True})
        except Exception as exc:
            log.error("on_stop failed: %s", exc)
            return JSONResponse({"success": False, "error": str(exc)}, status_code=500)

    @router.post("/api/meeting/start")
    async def api_meeting_start(
        request: Request, payload: Optional[_MeetingStartRequest] = None
    ) -> Any:
        try:
            meeting = _service(ctx).start_capture(
                _principal(request), {"devices": list(payload.devices) if payload and payload.devices else []}
            )
        except ValidationError as exc:
            return JSONResponse({"success": False, "error": str(exc)}, status_code=501)
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
        return _stop(request)

    @router.post("/api/stop")
    async def api_stop(request: Request, _: Optional[_StopRequest] = None) -> Any:
        return _stop(request)

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
