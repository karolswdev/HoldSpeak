"""Thin HTTP adapters for durable Desk projections (HS-123-05).

Both routes are produced from ``holdspeak/desk_state_operations.py``
(desk.projection.list, desk.projection.present) through
``OperationRegistry.invoke`` (2026-11-09)."""
from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from ... import operations
from ...logging_config import get_logger
from ...services.errors import NotFound, ValidationError
from ..context import WebContext
from ..operation_routes import operation_router
from ..runtime_support import error_500
from ._mount import mount_router

log = get_logger("web.routes.projections")

_NAMES = ("desk.projection.list", "desk.projection.present")
_FAILED = {"desk.projection.list": "Failed to project Desk attention and receipts",
           "desk.projection.present": "Failed to update projection presentation"}


def _answer(name: str) -> Callable[..., Any]:
    async def answer(fn: Callable[[], Any], *, status: int = 200) -> JSONResponse:
        try:
            return JSONResponse(await run_in_threadpool(fn), status_code=status)
        except NotFound:
            return JSONResponse({"error": "Projection not found"}, status_code=404)
        except (ValidationError, operations.OperationRefused) as exc:
            return JSONResponse({"error": exc.detail}, status_code=400)
        except (TypeError, ValueError) as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, _FAILED[name])

    return answer


def _projections() -> Any:
    from ...db import get_database, get_observer
    from ...services.projection_service import ProjectionService

    return ProjectionService(get_database(), observer=get_observer())


def build_projections_router(ctx: WebContext) -> APIRouter:
    router = APIRouter(tags=["desk"])
    for descriptor in (d for d in operations.DESK_STATE_OPERATIONS if d.name in _NAMES):
        mount_router(router, operation_router([descriptor], lambda: operations.for_context(ctx, projection_service=_projections),
                                              _answer(descriptor.name), module=__name__))
    return router


__all__ = ["build_projections_router"]
