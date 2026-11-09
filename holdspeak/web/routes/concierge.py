"""Concierge routes (HS-170-03): the Engines window.

Produced from ``holdspeak/concierge_operations.py`` (2026-11-09): every route
is ``OperationRegistry.invoke`` over its declared row, served by
``ConciergeService`` (``services/concierge_service.py``); the MCP tools come
from the same rows. Every row is owner only. A refusal answers
``{code, message}`` (and ``group`` when one group is refused) with its status.
The hand-written bodies are parked (``_parked/concierge_handwritten_20261109.py``).
"""
from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from ... import operations
from ...concierge_operations import CONCIERGE_OPERATIONS
from ...logging_config import get_logger
from ...operations import OperationRefused
from ...services.errors import ConflictError, ServiceError
from ..context import WebContext
from ..operation_routes import operation_router
from ..runtime_support import error_500
from ._mount import mount_router

log = get_logger("web.routes.concierge")


def _refused(exc: ServiceError) -> JSONResponse:
    ctx = exc.context or {}
    status = int(ctx.get("status", 400))
    if isinstance(exc, ConflictError) and status < 400:
        status = 409
    body: dict[str, Any] = {"code": exc.code, "message": exc.detail}
    # PHILO-15 10: a refused group is named, so the face can say which one.
    if ctx.get("group"):
        body["group"] = str(ctx["group"])
    if "ok" in ctx:  # Retry's answer keeps its ok flag
        body = {"ok": ctx["ok"], **body}
    return JSONResponse(body, status_code=status)


async def _answer(fn: Callable[[], Any], *, status: int = 200) -> Any:
    try:
        return JSONResponse(await run_in_threadpool(fn), status_code=status)
    except OperationRefused as exc:
        return JSONResponse({"code": exc.code, "message": exc.detail}, status_code=400)
    except ServiceError as exc:
        return _refused(exc)
    except Exception as exc:
        return error_500(exc, log, "The engines request failed")


def build_concierge_router(ctx: WebContext) -> APIRouter:
    router = APIRouter(tags=["concierge"])

    def registry() -> Any:
        from ...services.concierge_service import ConciergeService

        return operations.for_context(ctx, concierge_service=lambda: ConciergeService(ctx))

    mount_router(router, operation_router(CONCIERGE_OPERATIONS, registry, _answer, module=__name__))
    return router


__all__ = ["build_concierge_router"]
