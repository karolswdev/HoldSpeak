"""Transport adapters for persisted speaker profiles."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ....logging_config import get_logger
from ....principals import UNAUTHENTICATED
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


def build_speakers_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    @router.get("/api/speakers")
    def api_list_speakers(request: Request) -> Any:
        try:
            return JSONResponse(_service(ctx).list_speakers(_principal(request)))
        except Exception as exc:
            return error_500(exc, log, "Failed to list speakers")

    return router
