"""Calendar snapshot upload and confirm (HS-146-07).

POST /api/calendar/snapshot          -- upload screenshot(s), read the events with the vision model
POST /api/calendar/snapshot/confirm  -- confirm the reviewed events, write the .ics

Confirm is produced from ``calendar.snapshot.confirm``
(``holdspeak/calendar_operations.py``, 2026-11-09): owner only, his press.
The upload stays hand-written (a produced route takes no file) and calls
``CalendarService.extract``. Both answer ``{success: false, error}`` with
their status on a refusal.
"""
from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter, File, Request, UploadFile
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from ...calendar_operations import CALENDAR_OPERATIONS
from ...logging_config import get_logger
from ...operations import OperationRefused
from ...principals import UNAUTHENTICATED
from ...services.calendar_service import MAX_FILE_BYTES, CalendarService  # noqa: F401 (MAX_FILE_BYTES re-exported)
from ...services.errors import ServiceError
from ..context import WebContext
from ..operation_routes import operation_router
from ..runtime_support import error_500
from ._mount import mount_router
from .calendar_sources import calendar_registry

log = get_logger("web.routes.calendar_snapshot")


async def _answer(fn: Callable[[], Any], *, status: int = 200) -> Any:
    try:
        return JSONResponse(await run_in_threadpool(fn), status_code=status)
    except OperationRefused as exc:
        return JSONResponse({"success": False, "error": exc.detail}, status_code=422)
    except ServiceError as exc:
        return JSONResponse({"success": False, "error": exc.detail},
                            status_code=int((exc.context or {}).get("status") or 422))
    except Exception as exc:
        return error_500(exc, log, "Failed to confirm the calendar snapshot")


def build_calendar_snapshot_router(ctx: WebContext) -> APIRouter:
    router = APIRouter(tags=["calendar-snapshot"])

    @router.post("/api/calendar/snapshot")
    async def extract_snapshot(request: Request, files: list[UploadFile] = File(...)) -> Any:
        images = [((upload.content_type or ""), await upload.read()) for upload in files]
        principal = getattr(request.state, "principal", UNAUTHENTICATED)
        calendar_service = getattr(ctx, "calendar_service", None) or CalendarService(ctx)
        return await _answer(lambda: calendar_service.extract(principal, images))

    rows = [row for row in CALENDAR_OPERATIONS if row.name == "calendar.snapshot.confirm"]
    mount_router(router, operation_router(rows, calendar_registry(ctx), _answer, module=__name__))
    return router
