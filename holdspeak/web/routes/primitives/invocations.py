"""Read-only capability run receipts for retry, inspection, and return.

Both routes are produced from ``holdspeak/invocation_operations.py``
(2026-11-09) through ``OperationRegistry.invoke``; the MCP tools come from the
same rows."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from .... import operations
from ....logging_config import get_logger
from ....services.errors import NotFound, ServiceError
from ....services.invocation_service import InvocationService
from ...context import WebContext
from ...operation_routes import operation_router
from ...runtime_support import error_500

log = get_logger("web.routes.primitives.invocations")


def recover_inference_on_startup() -> list[str]:
    """Project hub-killed, actually claimed inference attempts as unknown."""
    return InvocationService.recover_inference_on_startup()


async def _answer(fn: Any, *, status: int = 200) -> JSONResponse:
    try:
        return JSONResponse(await run_in_threadpool(fn), status_code=status)
    except NotFound as exc:
        return JSONResponse({"error": exc.detail}, status_code=404)
    except ServiceError as exc:
        payload = dict(exc.context)
        return JSONResponse({"error": exc.detail, "code": exc.code}, status_code=int(payload.get("status", 400)))
    except Exception as exc:
        return error_500(exc, log, "Failed to read capability invocations")


def build_invocations_router(ctx: WebContext) -> APIRouter:
    from ....invocation_operations import INVOCATION_OPERATIONS

    def registry() -> operations.OperationRegistry:
        return operations.for_context(ctx, invocation_service=InvocationService.from_runtime)

    return operation_router(INVOCATION_OPERATIONS, registry, _answer, module=__name__)
