"""The architect's desk — seed + reset routes (HS-112-03).

Both are produced from ``holdspeak/desk_state_operations.py`` (desk.seed,
desk.reset; owner only) through ``OperationRegistry.invoke`` (2026-11-09).
Reset is the desk's first destructive act and belongs to the owner alone: the
registry refuses any other principal with ``owner_required``.
"""
from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from ... import operations
from ...logging_config import get_logger
from ..context import WebContext
from ..operation_routes import operation_router
from ..runtime_support import error_500
from ._mount import mount_router

def _desk() -> Any:
    from ...db import get_database, get_observer
    from ...services.desk_service import DeskService

    return DeskService(get_database(), observer=get_observer())


log = get_logger("web.routes.desk_seed")

_FAILED = {"desk.seed": "Failed to seed the desk", "desk.reset": "Failed to reset the desk"}


def _answer(name: str) -> Callable[..., Any]:
    async def answer(fn: Callable[[], Any], *, status: int = 200) -> JSONResponse:
        try:
            return JSONResponse(await run_in_threadpool(fn), status_code=status)
        except (operations.OperationRefused, operations.OperationOwnerRequired) as exc:
            return JSONResponse({"error": exc.detail, "code": exc.code},
                                status_code=403 if exc.code == "owner_required" else 400)
        except Exception as exc:
            return error_500(exc, log, _FAILED[name])

    return answer


def build_desk_seed_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()
    for descriptor in (d for d in operations.DESK_STATE_OPERATIONS if d.name in _FAILED):
        mount_router(router, operation_router([descriptor], lambda: operations.for_context(ctx, desk_service=_desk),
                                              _answer(descriptor.name), module=__name__))
    return router
