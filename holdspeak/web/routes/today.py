"""Today's own reads (DELIGHT slice 5, 2026-10-28).

``GET /api/today/since-morning``: what got done today (tasks ticked,
Desk decisions and Projects added, decisions confirmed or recorded, notes
filed, sends sent and meetings recorded), newest first.
Today draws it after 17:00 as Since this morning; its ``programs`` block (PG18)
feeds the Programs line at any hour. The route is produced from
``holdspeak/desk_state_operations.py`` (today.since_morning) through
``OperationRegistry.invoke`` (2026-11-09)."""
from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from ... import operations
from ...db import get_database
from ...logging_config import get_logger
from ...services.today_service import TodayService
from ..context import WebContext
from ..operation_routes import operation_router
from ..runtime_support import error_500
from ._mount import mount_router

log = get_logger("web.routes.today")


async def _answer(fn: Callable[[], Any], *, status: int = 200) -> JSONResponse:
    try:
        return JSONResponse(await run_in_threadpool(fn), status_code=status)
    except Exception as exc:
        return error_500(exc, log, "Failed to read what got done today")


def build_today_router(ctx: WebContext) -> APIRouter:
    router = APIRouter(tags=["today"])

    def _registry() -> Any:
        return operations.for_context(ctx, today_service=lambda: TodayService(get_database()))

    descriptors = [operations.TODAY_GET, *(d for d in operations.DESK_STATE_OPERATIONS if d.name == "today.since_morning")]
    mount_router(router, operation_router(descriptors, _registry, _answer, module=__name__))
    return router
