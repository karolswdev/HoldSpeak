"""HS-175-03: the calendar source facts, ``GET /api/calendar/sources``.

Produced from ``calendar.sources`` (``holdspeak/calendar_operations.py``,
2026-11-09), served by ``services/calendar_service.CalendarService``; the
read moved there unchanged. The hand-written route is parked.
"""
from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from ... import operations
from ...calendar_operations import CALENDAR_OPERATIONS
from ...logging_config import get_logger
from ..context import WebContext
from ..operation_routes import operation_router
from ..runtime_support import error_500
from ._mount import mount_router

log = get_logger("web.routes.calendar_sources")


def calendar_registry(ctx: Any) -> Callable[[], Any]:
    """The route's registry: the hub's, else one over a CalendarService on this context."""
    def registry() -> Any:
        from ...services.calendar_service import CalendarService

        return operations.for_context(ctx, calendar_service=lambda: CalendarService(ctx))

    return registry


async def _answer(fn: Callable[[], Any], *, status: int = 200) -> Any:
    try:
        return JSONResponse(await run_in_threadpool(fn), status_code=status)
    except Exception as exc:
        return error_500(exc, log, "Failed to load calendar sources")


def build_calendar_sources_router(ctx: WebContext) -> APIRouter:
    router = APIRouter(tags=["calendar-sources"])
    rows = [row for row in CALENDAR_OPERATIONS if row.name == "calendar.sources"]
    mount_router(router, operation_router(rows, calendar_registry(ctx), _answer, module=__name__))
    return router
