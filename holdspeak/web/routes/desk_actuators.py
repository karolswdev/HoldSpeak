"""Desk actuator transport adapters."""
from __future__ import annotations
from typing import Any
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from ...services.errors import NotFound, ServiceError
from ..context import WebContext
from ..runtime_support import error_500
from ...logging_config import get_logger
log = get_logger("web.routes.desk_actuators")


def _error(exc: ServiceError) -> JSONResponse:
    status = 404 if isinstance(exc, NotFound) else 400
    return JSONResponse({"success": False, "error": exc.detail, **exc.context}, status_code=status)


def build_desk_actuators_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()
    service = ctx.actuator_service
    if service is None:
        raise RuntimeError("ActuatorProposalService is not composed")

    from ... import operations
    from ...delivery_operations import DELIVERY_OPERATIONS
    from ...parity_operations import PARITY_OPERATIONS
    from ...operations import OperationOwnerRequired
    from ..operation_routes import operation_router
    from starlette.concurrency import run_in_threadpool
    from ._mount import mount_router

    async def answer(fn: Any, *, status: int = 200) -> Any:
        try:
            return JSONResponse(await run_in_threadpool(fn), status_code=status)
        except OperationOwnerRequired as exc:
            return JSONResponse({"error": exc.code, "code": exc.code}, status_code=403)
        except ServiceError as exc:
            return _error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to call desk actuator")

    mount_router(router, operation_router(
        [op for op in (*DELIVERY_OPERATIONS, *PARITY_OPERATIONS) if op.service == "actuator_service"],
        lambda: operations.for_context(ctx), answer, module=__name__))
    return router
