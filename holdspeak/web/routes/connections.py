"""HS-168-02: Connections routes -- ONE readiness shape on the hub.

GET  /api/connections                          -- list all tools
POST /api/connections/{provider}/recheck       -- recheck one provider

Parse-and-serialize ONLY: the ConnectionsService docstring law.
Owner-scoped; same auth gate as providers.py.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ...logging_config import get_logger
from ...principals import UNAUTHENTICATED
from ..context import WebContext
from ..runtime_support import error_500

log = get_logger("web.routes.connections")


def build_connections_router(ctx: WebContext) -> APIRouter:
    router = APIRouter(tags=["connections"])

    def principal(request: Request) -> Any:
        return getattr(request.state, "principal", UNAUTHENTICATED)

    # ── GET /api/connections ──────────────────────────────────────────

    @router.get("/api/connections")
    async def list_connections(request: Request) -> Any:
        """The ONE readiness shape: one entry per known tool."""
        try:
            svc = ctx.connections_service
            if svc is None:
                return JSONResponse(
                    {"code": "service_unavailable",
                     "message": "Connections service not configured"},
                    status_code=503,
                )
            result = svc.list_tools(principal(request))
            return JSONResponse(result)
        except Exception as exc:
            return error_500(exc, log, "Failed to list connections")

    # ── POST /api/connections/{provider}/recheck ─────────────────────

    @router.post("/api/connections/{provider}/recheck")
    async def recheck_connection(provider: str, request: Request) -> Any:
        """Recheck one provider and return its refreshed tool entry."""
        try:
            svc = ctx.connections_service
            if svc is None:
                return JSONResponse(
                    {"code": "service_unavailable",
                     "message": "Connections service not configured"},
                    status_code=503,
                )
            body: dict[str, Any] = {}
            try:
                body = await request.json()
            except Exception:
                pass  # empty body is fine
            ref = body.get("ref")
            result = svc.recheck(principal(request), provider, ref=ref)
            return JSONResponse(result)
        except Exception as exc:
            return error_500(exc, log, "Failed to recheck connection")

    return router
