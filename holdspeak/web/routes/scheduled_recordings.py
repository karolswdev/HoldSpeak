"""Scheduled recording CRUD + cancel-armed routes (HS-136-02).

Beside the meeting routes. Same auth and error grammar: typed refusals
for validation errors (4xx), not 500s.
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Body, Request
from fastapi.responses import JSONResponse

from ...db import get_database
from ...logging_config import get_logger
from ...principals import UNAUTHENTICATED
from ...services.errors import ConflictError, NotFound, ValidationError
from ...services.scheduled_recording_service import ScheduledRecordingService
from ..context import WebContext

log = get_logger("web.routes.scheduled_recordings")


def _principal(request: Request):
    return getattr(request.state, "principal", UNAUTHENTICATED)


def _service() -> ScheduledRecordingService:
    return ScheduledRecordingService(get_database())


def _error_response(exc: Exception) -> JSONResponse:
    """Map service errors to typed HTTP responses -- never a bare 500."""
    if isinstance(exc, NotFound):
        return JSONResponse(
            {"success": False, "error": str(exc), "code": exc.code},
            status_code=404,
        )
    if isinstance(exc, ValidationError):
        return JSONResponse(
            {"success": False, "error": str(exc), "code": exc.code,
             **({"context": exc.context} if exc.context else {})},
            status_code=422,
        )
    if isinstance(exc, ConflictError):
        return JSONResponse(
            {"success": False, "error": str(exc), "code": exc.code},
            status_code=409,
        )
    log.error("Unexpected error in scheduled recording route: %s", exc)
    return JSONResponse(
        {"success": False, "error": str(exc)}, status_code=500,
    )


def build_scheduled_recordings_router(ctx: WebContext) -> APIRouter:
    router = APIRouter(prefix="/api/scheduled-recordings", tags=["scheduled-recordings"])

    @router.get("")
    async def list_schedules(request: Request) -> Any:
        try:
            schedules = _service().list_schedules(_principal(request))
            return JSONResponse({"success": True, "schedules": schedules})
        except Exception as exc:
            return _error_response(exc)

    @router.post("")
    async def create_schedule(request: Request, body: dict = Body(default={})) -> Any:
        try:
            kwargs: dict[str, Any] = {}
            # HS-147-01: calendar_event_id triggers the event-linked arm path;
            # when present, the service computes everything from the event.
            calendar_event_id = str(body.get("calendar_event_id") or "")
            if calendar_event_id:
                kwargs["calendar_event_id"] = calendar_event_id
            else:
                kwargs["title"] = str(body.get("title") or "")
                kwargs["cron_expr"] = str(body.get("cron_expr") or "")
                kwargs["tz"] = str(body.get("tz") or "UTC")
                kwargs["one_shot"] = bool(body.get("one_shot", False))
                kwargs["duration_minutes"] = int(body.get("duration_minutes", 60))
                kwargs["enabled"] = bool(body.get("enabled", False))
            result = _service().create_schedule(
                _principal(request), **kwargs,
            )
            return JSONResponse({"success": True, "schedule": result}, status_code=201)
        except (ValidationError, NotFound, ConflictError) as exc:
            return _error_response(exc)
        except (ValueError, TypeError) as exc:
            return JSONResponse(
                {"success": False, "error": str(exc), "code": "validation_error"},
                status_code=422,
            )
        except Exception as exc:
            return _error_response(exc)

    @router.get("/{schedule_id}")
    async def get_schedule(request: Request, schedule_id: str) -> Any:
        try:
            result = _service().get_schedule(_principal(request), schedule_id)
            return JSONResponse({"success": True, "schedule": result})
        except (NotFound, ValidationError, ConflictError) as exc:
            return _error_response(exc)
        except Exception as exc:
            return _error_response(exc)

    @router.patch("/{schedule_id}")
    async def update_schedule(request: Request, schedule_id: str, body: dict = Body(default={})) -> Any:
        try:
            kwargs: dict[str, Any] = {}
            if "title" in body:
                kwargs["title"] = str(body["title"])
            if "cron_expr" in body:
                kwargs["cron_expr"] = str(body["cron_expr"])
            if "tz" in body:
                kwargs["tz"] = str(body["tz"])
            if "one_shot" in body:
                kwargs["one_shot"] = bool(body["one_shot"])
            if "duration_minutes" in body:
                kwargs["duration_minutes"] = int(body["duration_minutes"])
            if "enabled" in body:
                kwargs["enabled"] = bool(body["enabled"])
            result = _service().update_schedule(
                _principal(request), schedule_id, **kwargs,
            )
            return JSONResponse({"success": True, "schedule": result})
        except (ValidationError, NotFound, ConflictError) as exc:
            return _error_response(exc)
        except (ValueError, TypeError) as exc:
            return JSONResponse(
                {"success": False, "error": str(exc), "code": "validation_error"},
                status_code=422,
            )
        except Exception as exc:
            return _error_response(exc)

    @router.delete("/{schedule_id}")
    async def delete_schedule(request: Request, schedule_id: str) -> Any:
        try:
            result = _service().delete_schedule(_principal(request), schedule_id)
            return JSONResponse({"success": True, **result})
        except (NotFound, ValidationError, ConflictError) as exc:
            return _error_response(exc)
        except Exception as exc:
            return _error_response(exc)

    @router.post("/{schedule_id}/cancel")
    async def cancel_armed(request: Request, schedule_id: str) -> Any:
        try:
            result = _service().cancel_armed(_principal(request), schedule_id)
            return JSONResponse({"success": True, **result})
        except (NotFound, ValidationError, ConflictError) as exc:
            return _error_response(exc)
        except Exception as exc:
            return _error_response(exc)

    return router
