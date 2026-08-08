"""The architect's desk — seed + reset routes (HS-112-03).

Thin wrappers over ``holdspeak.db.seed`` (the same repositories the
primitive routes wrap). Both are POSTs under ``/api/`` with no narrower
right named in ``principals.required_right``, so the centralized edge
gate requires the OWNER principal — reset is the desk's first
destructive act and belongs to the owner alone.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ...logging_config import get_logger
from ...services.desk_service import DeskService
from ..context import WebContext
from ..runtime_support import error_500

log = get_logger("web.routes.desk_seed")


def build_desk_seed_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    def _svc() -> DeskService:
        from ...db import get_database, get_observer

        return DeskService(get_database(), observer=get_observer())

    @router.post("/api/desk/seed")
    async def api_desk_seed(request: Request) -> Any:
        try:
            return JSONResponse(_svc().seed(getattr(request.state, "principal", None)))
        except Exception as exc:
            return error_500(exc, log, "Failed to seed the desk")

    @router.post("/api/desk/reset")
    async def api_desk_reset(request: Request) -> Any:
        try:
            return JSONResponse(_svc().reset(getattr(request.state, "principal", None)))
        except Exception as exc:
            return error_500(exc, log, "Failed to reset the desk")

    return router
