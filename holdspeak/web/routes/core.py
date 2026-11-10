"""Core runtime routes: liveness + raw meeting state (HS-26-01 pilot).

The reference pattern the other Phase 26 migrations follow: a `build_*_router`
factory that closes over a `WebContext` instead of the `MeetingWebServer`
instance. Behavior must match the prior inline handlers exactly.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from starlette.concurrency import run_in_threadpool

from ... import operations
from ...system_operations import SYSTEM_OPERATIONS, system_service
from ..context import WebContext
from ..operation_routes import operation_router
from ._mount import mount_router

def _desk() -> Any:
    from ...db import get_database, get_observer
    from ...services.desk_service import DeskService

    return DeskService(get_database(), observer=get_observer())


async def _health_answer(fn: Any, *, status: int = 200) -> JSONResponse:
    return JSONResponse(await run_in_threadpool(fn), status_code=status)


def build_core_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    mount_router(router, operation_router(
        [d for d in SYSTEM_OPERATIONS if d.name == "system.state"],
        lambda: operations.for_context(ctx, system_service=lambda: system_service(ctx)),
        _health_answer, module=__name__,
    ))

    # 2026-11-09: GET /health is produced from desk_state_operations.py (desk.health).
    descriptor = next(d for d in operations.DESK_STATE_OPERATIONS if d.name == "desk.health")
    mount_router(router, operation_router([descriptor], lambda: operations.for_context(ctx, desk_service=_desk), _health_answer,
                                          module=__name__))
    return router
