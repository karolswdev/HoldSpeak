"""HS-168-02: Connections routes -- ONE readiness shape on the hub.

GET  /api/connections                          -- list all tools
POST /api/connections/{provider}/recheck       -- recheck one provider

Parse-and-serialize ONLY: the ConnectionsService docstring law.
Owner-scoped; same auth gate as providers.py.
"""
from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ... import operations
from ...logging_config import get_logger
from ...operations import OperationRefused
from ...principals import UNAUTHENTICATED
from ...room_operations import REMOTE_PROVIDERS
from ...services.errors import ServiceError
from ..context import WebContext
from ..runtime_support import error_500
from ._room_kernel import exempt_form_right, kernel_fields, kernel_refusal, refuse_identifiable, refusal_fields

log = get_logger("web.routes.connections")


def build_connections_router(ctx: WebContext) -> APIRouter:
    router = APIRouter(tags=["connections"])

    def principal(request: Request) -> Any:
        return getattr(request.state, "principal", UNAUTHENTICATED)

    def ops() -> Any:
        return operations.for_context(ctx)

    # ── GET /api/connections ──────────────────────────────────────────
    # PHILO-9-02 (B1): the declared connection.list -- a cached read; it
    # makes no provider call.

    @router.get("/api/connections")
    async def list_connections(request: Request) -> Any:
        """The ONE readiness shape: one entry per known tool."""
        try:
            if ctx.connections_service is None:
                return JSONResponse(
                    {"code": "service_unavailable",
                     "message": "Connections service not configured"},
                    status_code=503,
                )
            return JSONResponse(ops().invoke(principal(request), "connection.list", {}))
        except Exception as exc:
            return error_500(exc, log, "Failed to list connections")

    # ── POST /api/connections/{provider}/recheck ─────────────────────
    # Conditional: github, jira, confluence ask the provider (egress:
    # admitted, with its receipt); calendar and models read local state
    # (exempt: the previous edge right is re-applied here).

    @router.post("/api/connections/{provider}/recheck")
    async def recheck_connection(provider: str, request: Request) -> Any:
        """Recheck one provider and return its refreshed tool entry."""
        p = principal(request)
        admitted = provider in REMOTE_PROVIDERS
        if not admitted and (refused := exempt_form_right(p)) is not None:
            return refused
        raw_bytes = await request.body()
        try:
            body = json.loads(raw_bytes) if raw_bytes.strip() else {}
        except ValueError:
            body = None
        if not isinstance(body, dict):
            kernel = refuse_identifiable(ops(), p, "connection.recheck", "invalid_arguments") if admitted else None
            return JSONResponse({"code": "invalid_arguments", "message": "the body must be a JSON object",
                                 **kernel_fields(kernel)}, status_code=400)
        try:
            if ctx.connections_service is None:
                return JSONResponse(
                    {"code": "service_unavailable",
                     "message": "Connections service not configured"},
                    status_code=503,
                )
            from starlette.concurrency import run_in_threadpool

            # PHILO-10-02: the probe runs gh/acli -- off the event loop.
            result, kernel = await run_in_threadpool(
                ops().invoke_receipted, p, "connection.recheck", {"provider_id": provider, "ref": body.get("ref")})
            return JSONResponse({**result, **kernel_fields(kernel)} if isinstance(result, dict) else result)
        except OperationRefused as exc:
            return JSONResponse({"code": "invalid_arguments", "message": exc.detail, **refusal_fields(exc)},
                                status_code=400)
        except ServiceError as exc:
            if (refused := kernel_refusal(exc)) is not None:
                return refused
            return JSONResponse({"code": exc.code, "message": exc.detail, **refusal_fields(exc)},
                                status_code=int(exc.context.get("status") or 409))
        except Exception as exc:
            return error_500(exc, log, "Failed to recheck connection")

    return router
