"""Live-meeting lifecycle routes: bookmark, start/stop, and meeting metadata.

The lifecycle/mutation handlers read callbacks (`on_*`, `broadcast`) from the
shared `WebContext`, exactly as before the Phase-72 package split.
"""

from __future__ import annotations

from typing import Any, Callable, Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ....logging_config import get_logger
from ....web_requests import (
    _BookmarkRequest,
    _MeetingStartRequest,
    _StopRequest,
    _UpdateMeetingRequest,
)
from ...runtime_support import _UnknownDeviceError, _meeting_callback_payload
from ...context import WebContext

log = get_logger("web.routes.meetings")


def build_live_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    @router.post("/api/bookmark")
    async def api_bookmark(payload: Optional[_BookmarkRequest] = None) -> Any:
        try:
            label = payload.label if payload is not None else ""
            result = ctx.on_bookmark(label)
        except Exception as e:
            log.error(f"on_bookmark failed: {e}")
            return JSONResponse({"success": False, "error": str(e)}, status_code=500)

        bookmark_data: Any = None
        if hasattr(result, "to_dict"):
            try:
                bookmark_data = result.to_dict()
            except Exception:
                bookmark_data = None
        elif isinstance(result, dict):
            bookmark_data = result

        if bookmark_data is not None:
            ctx.broadcast("bookmark", bookmark_data)

        return JSONResponse({"success": True})

    async def _handle_stop_request(callback: Callable[[], Any]) -> Any:
        try:
            result = callback()
        except Exception as e:
            log.error(f"on_stop failed: {e}")
            return JSONResponse({"success": False, "error": str(e)}, status_code=500)

        stopped_data: Any = None
        if hasattr(result, "to_dict"):
            try:
                stopped_data = result.to_dict()
            except Exception:
                stopped_data = None
        elif isinstance(result, dict):
            stopped_data = result
        else:
            stopped_data = {"status": "stopped"}

        ctx.broadcast("stopped", stopped_data)
        return JSONResponse({"success": True})

    @router.post("/api/meeting/start")
    async def api_meeting_start(
        payload: Optional[_MeetingStartRequest] = None,
    ) -> Any:
        if ctx.on_start is None:
            return JSONResponse(
                {"success": False, "error": "Meeting start control not supported"},
                status_code=501,
            )

        devices = list(payload.devices) if payload and payload.devices else []

        try:
            result = ctx.on_start(devices=devices) if devices else ctx.on_start()
        except _UnknownDeviceError as exc:
            return JSONResponse(
                {"success": False, "error": str(exc), "device_id": exc.device_id},
                status_code=404,
            )
        except Exception as e:
            log.error(f"on_start failed: {e}")
            return JSONResponse({"success": False, "error": str(e)}, status_code=500)

        meeting_data = _meeting_callback_payload(result)

        if meeting_data is not None:
            ctx.broadcast("meeting_started", meeting_data)
        return JSONResponse({"success": True, "meeting": meeting_data})

    @router.post("/api/meeting/stop")
    async def api_meeting_stop(_: Optional[_StopRequest] = None) -> Any:
        callback = ctx.on_meeting_stop or ctx.on_stop
        return await _handle_stop_request(callback)

    @router.post("/api/stop")
    async def api_stop(_: Optional[_StopRequest] = None) -> Any:
        # Backward-compatible alias.
        return await _handle_stop_request(ctx.on_stop)

    @router.patch("/api/meeting")
    async def api_update_meeting(payload: _UpdateMeetingRequest) -> Any:
        """Update meeting title and/or tags."""
        try:
            meeting_data: Optional[dict[str, Any]] = None
            if ctx.on_update_meeting is not None:
                result = ctx.on_update_meeting(title=payload.title, tags=payload.tags)
                if hasattr(result, "to_dict"):
                    try:
                        meeting_data = result.to_dict()
                    except Exception:
                        meeting_data = None
                elif isinstance(result, dict):
                    meeting_data = result
            else:
                if payload.title is not None and ctx.on_set_title is not None:
                    ctx.on_set_title(payload.title)
                if payload.tags is not None and ctx.on_set_tags is not None:
                    ctx.on_set_tags(payload.tags)
                try:
                    meeting_data = ctx.get_state() or {}
                except Exception:
                    meeting_data = None

            if isinstance(meeting_data, dict):
                ctx.broadcast(
                    "meeting_updated",
                    {
                        "title": meeting_data.get("title"),
                        "tags": meeting_data.get("tags") if isinstance(meeting_data.get("tags"), list) else [],
                    },
                )
            return JSONResponse({"success": True, "meeting": meeting_data})
        except Exception as e:
            log.error(f"Failed to update meeting: {e}")
            return JSONResponse(
                {"success": False, "error": str(e)}, status_code=500
            )

    return router
