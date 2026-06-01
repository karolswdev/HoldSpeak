"""Core runtime routes: liveness + raw meeting state (HS-26-01 pilot).

The reference pattern the other Phase 26 migrations follow: a `build_*_router`
factory that closes over a `WebContext` instead of the `MeetingWebServer`
instance. Behavior must match the prior inline handlers exactly.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ...logging_config import get_logger
from ..context import WebContext

log = get_logger("web.routes.core")


def build_core_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    @router.get("/health")
    async def health() -> Any:
        return JSONResponse({"status": "ok"})

    @router.get("/api/state")
    async def api_state() -> Any:
        try:
            state = ctx.get_state() or {}
        except Exception as e:  # noqa: BLE001 - preserve prior fail-soft behavior
            log.error(f"get_state failed: {e}")
            state = {}
        return JSONResponse(state)

    return router
