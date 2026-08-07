"""Transport adapters for persisted meeting intelligence projections."""
from __future__ import annotations
from typing import Any, Optional
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from ....logging_config import get_logger
from ....principals import UNAUTHENTICATED
from ....services.errors import NotFound
from ....services.meeting_service import MeetingService
from ...context import WebContext
from ...runtime_support import error_500

log = get_logger("web.routes.meetings")

def _service(ctx: WebContext) -> MeetingService:
    if ctx.meeting_service_factory is not None:
        service = ctx.meeting_service_factory()
        if isinstance(service, MeetingService):
            return service
    if isinstance(ctx.meeting_service, MeetingService):
        return ctx.meeting_service
    raise RuntimeError("Meeting service is not configured")

def _principal(request: Request):
    return getattr(request.state, "principal", UNAUTHENTICATED)

def build_insights_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()
    @router.get("/api/meetings/{meeting_id}/intent-timeline")
    async def api_get_meeting_intent_timeline(meeting_id: str, request: Request, limit: int = 200) -> Any:
        try:
            return JSONResponse(_service(ctx).get_intent_timeline(_principal(request), meeting_id, limit))
        except NotFound:
            return JSONResponse({"error": "Meeting not found"}, status_code=404)
        except Exception as exc:
            return error_500(exc, log, "Failed to load meeting intent timeline")
    @router.get("/api/meetings/{meeting_id}/plugin-runs")
    async def api_get_meeting_plugin_runs(meeting_id: str, request: Request, limit: int = 500, window_id: Optional[str] = None) -> Any:
        try:
            return JSONResponse(_service(ctx).list_plugin_runs(_principal(request), meeting_id, limit=limit, window_id=window_id))
        except NotFound:
            return JSONResponse({"error": "Meeting not found"}, status_code=404)
        except Exception as exc:
            return error_500(exc, log, "Failed to load meeting plugin runs")
    @router.get("/api/meetings/{meeting_id}/artifacts")
    async def api_get_meeting_artifacts(meeting_id: str, request: Request, limit: int = 200) -> Any:
        try:
            return JSONResponse(_service(ctx).list_artifacts(_principal(request), meeting_id, limit))
        except NotFound:
            return JSONResponse({"error": "Meeting not found"}, status_code=404)
        except Exception as exc:
            return error_500(exc, log, "Failed to load meeting artifacts")
    return router
