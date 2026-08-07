"""Transport adapters for persisted speaker profiles."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ....logging_config import get_logger
from ....principals import UNAUTHENTICATED
from ....services.errors import NotFound, ValidationError
from ....services.meeting_service import MeetingService
from ....web_requests import _SpeakerUpdateRequest
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
    async def api_list_speakers(request: Request) -> Any:
        try:
            return JSONResponse(_service(ctx).list_speakers(_principal(request)))
        except Exception as exc:
            return error_500(exc, log, "Failed to list speakers")

    @router.get("/api/speakers/{speaker_id}")
    async def api_get_speaker(speaker_id: str, request: Request, limit: int = 500) -> Any:
        try:
            return JSONResponse(_service(ctx).get_speaker(_principal(request), speaker_id, limit))
        except NotFound:
            return JSONResponse({"error": "Speaker not found"}, status_code=404)
        except Exception as exc:
            return error_500(exc, log, "Failed to get speaker")

    @router.patch("/api/speakers/{speaker_id}")
    async def api_update_speaker(speaker_id: str, payload: _SpeakerUpdateRequest, request: Request) -> Any:
        try:
            return JSONResponse(_service(ctx).update_speaker(_principal(request), speaker_id, payload.model_dump()))
        except ValidationError as exc:
            return JSONResponse({"success": False, "error": str(exc)}, status_code=400)
        except NotFound:
            return JSONResponse({"success": False, "error": "Speaker not found"}, status_code=404)
        except Exception as exc:
            log.error("Failed to update speaker: %s", exc)
            return JSONResponse({"success": False, "error": str(exc)}, status_code=500)

    return router
