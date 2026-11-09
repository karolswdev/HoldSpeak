"""Constitutional context routes (HS-116-03, hardened HS-116-13).

GET/PUT the owner's always-on context that every agent run receives. The three
routes are produced from ``holdspeak/desk_state_operations.py``
(constitutional_context.read / update / history) through
``OperationRegistry.invoke`` (2026-11-09); the update is the owner's alone.
"""
from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from ... import operations
from ...constitutional_context import ConstitutionalContextService
from ...logging_config import get_logger
from ...services.errors import ValidationError
from ..operation_routes import operation_router
from ..runtime_support import error_500
from ._mount import mount_router

log = get_logger("web.routes.constitutional")

_FAILED = {"constitutional_context.read": "Failed to read constitutional context",
           "constitutional_context.update": "Failed to update constitutional context",
           "constitutional_context.history": "Failed to read context history"}


def _answer(name: str) -> Callable[..., Any]:
    async def answer(fn: Callable[[], Any], *, status: int = 200) -> JSONResponse:
        try:
            return JSONResponse(await run_in_threadpool(fn), status_code=status)
        except (operations.OperationRefused, operations.OperationOwnerRequired) as exc:
            return JSONResponse({"error": exc.detail, "code": exc.code},
                                status_code=403 if exc.code == "owner_required" else 400)
        except ValidationError as exc:
            return JSONResponse({"error": exc.detail}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, _FAILED[name])

    return answer


def build_constitutional_router(ctx: Any = None) -> APIRouter:
    router = APIRouter()

    def _registry() -> Any:
        return operations.for_context(ctx, constitutional_context_service=ConstitutionalContextService)

    for descriptor in (d for d in operations.DESK_STATE_OPERATIONS if d.name in _FAILED):
        mount_router(router, operation_router([descriptor], _registry, _answer(descriptor.name), module=__name__))
    return router
