"""Parked legacy primitive decision list route.

The canonical decision-record router owns ``GET /api/decisions``.  This
adapter remains byte-for-byte available for historical reference, but is not
registered by the live primitive router.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..... import operations
from .....logging_config import get_logger
from .....web.context import WebContext
from .....web.runtime_support import error_500

log = get_logger("web.routes.primitives.parked")

def build_parked_desk_decisions_router(ctx: WebContext) -> APIRouter:
    """The former desk projection list handler, intentionally unregistered."""
    router = APIRouter()

    def _ops() -> operations.OperationRegistry:
        return operations.for_context(ctx, "primitive_service")

    def _principal(request: Request) -> Any:
        return getattr(request.state, "principal", None)

    @router.get("/api/decisions")
    def api_list_desk_decisions(request: Request) -> Any:
        try:
            return JSONResponse({"decisions": _ops().invoke(_principal(request), "decision.list", {})})
        except Exception as exc:
            return error_500(exc, log, "Failed to list decisions")

    return router
