"""Device and runtime reads, produced from the hub-local system rows."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from .... import operations
from ....logging_config import get_logger
from ....operations import OperationRefused
from ....services.errors import ServiceError
from ....system_operations import SYSTEM_OPERATIONS, system_service
from ...context import WebContext
from ...operation_routes import operation_router
from ...runtime_support import error_500
from .._mount import mount_router

log = get_logger("web.routes.system")


async def _answer(fn: Any, *, status: int = 200) -> JSONResponse:
    try:
        return JSONResponse(await run_in_threadpool(fn), status_code=status)
    except OperationRefused as exc:
        return JSONResponse({"success": False, "code": exc.code, "error": exc.detail},
                            status_code=403 if exc.code == "owner_required" else 400)
    except ServiceError as exc:
        return JSONResponse({"success": False, "error": exc.detail,
                             **({"code": exc.code} if exc.code == "owner_required" else {})},
                            status_code=int(exc.context.get("status") or 400))
    except Exception as exc:
        return error_500(exc, log, "Failed to read runtime identity")


def build_health_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()
    mount_router(router, operation_router(
        [d for d in SYSTEM_OPERATIONS if d.name not in {"system.state", "plugin_job.process"}],
        lambda: operations.for_context(ctx, system_service=lambda: system_service(ctx)), _answer, module=__name__,
    ))
    return router
