"""Today's own reads (DELIGHT slice 5, 2026-10-28).

``GET /api/today/since-morning``: what got done today (tasks ticked,
decisions recorded, notes filed, sends sent, meetings held), newest first.
Today draws it after 17:00 as Since this morning; its ``programs`` block (PG18)
feeds the Programs line at any hour. The read goes through the
one Today service; the router builds a service only when the context has
none (a route test)."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from ...db import get_database
from ...logging_config import get_logger
from ...principals import UNAUTHENTICATED
from ...services.today_service import TodayService
from ..context import WebContext
from ..runtime_support import error_500

log = get_logger("web.routes.today")


def build_today_router(ctx: WebContext) -> APIRouter:
    router = APIRouter(prefix="/api/today", tags=["today"])

    def service() -> TodayService:
        return getattr(ctx, "today_service", None) or TodayService(get_database())

    @router.get("/since-morning")
    async def since_morning(request: Request) -> Any:
        principal = getattr(request.state, "principal", UNAUTHENTICATED)
        try:
            return JSONResponse(await run_in_threadpool(service().since_morning, principal))
        except Exception as exc:
            return error_500(exc, log, "Failed to read what got done today")

    return router
