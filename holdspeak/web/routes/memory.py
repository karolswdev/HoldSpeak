"""Authenticated long-horizon memory retrieval (HS-109-04).

Every route is produced from ``holdspeak/memory_operations.py`` through
``OperationRegistry.invoke`` (2026-11-09): Search, the standing pages, Recall
and the meaning-search switch. The hand-written router is parked in
``_parked/memory_routes_20261109.py``.
"""
from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from ... import operations
from ...services.errors import ServiceError, ValidationError
from ..context import WebContext
from ..operation_routes import operation_router
from ._mount import mount_router

#: The meaning-search rows answer a refusal as ``{code, message}`` (the Settings row reads it).
_MEANING = {"memory.meaning.status", "memory.meaning.turn_on", "memory.meaning.turn_off"}


def _answer(name: str) -> Callable[..., Any]:
    async def answer(fn: Callable[[], Any], *, status: int = 200) -> JSONResponse:
        try:
            return JSONResponse(await run_in_threadpool(fn), status_code=status)
        except operations.OperationRefused as exc:
            code = 403 if exc.code == "owner_required" else 400
            return JSONResponse({"code": exc.code, "message": exc.detail, "error": exc.detail}, status_code=code)
        except ServiceError as exc:
            if exc.code == "owner_required":
                return JSONResponse({"code": exc.code, "message": exc.detail, "error": exc.detail}, status_code=403)
            if name in _MEANING:
                return JSONResponse({"code": exc.code, "message": exc.detail},
                                    status_code=int(exc.context.get("status") or 400))
            if isinstance(exc, ValidationError):
                return JSONResponse({"error": exc.detail}, status_code=400)
            response = exc.context.get("response")
            return JSONResponse(response if isinstance(response, dict) else {"error": exc.detail},
                                status_code=int(exc.context.get("status") or 400))

    return answer


def build_memory_router(ctx: WebContext) -> APIRouter:
    if ctx.memory_service is None:
        raise RuntimeError("MemoryService must be supplied at application composition")
    router = APIRouter(tags=["memory"])

    def _recall() -> Any:
        from ...db import get_database
        from ...services.recall_service import RecallService

        return RecallService(get_database())

    def _registry() -> Any:
        return operations.for_context(ctx, recall_service=_recall)

    for descriptor in operations.MEMORY_OPERATIONS:
        mount_router(router, operation_router([descriptor], _registry, _answer(descriptor.name), module=__name__))
    return router
