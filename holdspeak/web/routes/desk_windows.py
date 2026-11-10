"""The desk over HTTP: its windows and its display requests (COMPOSITOR.md §13 L1, L10).

Produced from ``holdspeak/desk_operations.py`` (one declared contract,
2026-11-08) through ``OperationRegistry.invoke``; the answer keeps the
envelope the hand-written routes had (``{error, detail, ...context}``).

* ``GET  /api/desk/windows`` -- every open window, back to front, the desk's
  Stage shelf, and the window registry.
* ``POST /api/desk/windows/{window_id}/<verb>`` -- one verb on one window:
  ``open close move resize set_geometry raise send_back seat zoom``. The body
  carries the verb's arguments and an optional ``expected_revision``.
* ``POST /api/desk/windows/arrange`` -- many rects, one transaction, one frame.
* ``POST /api/desk/windows/stage-shelf`` -- ``{"side": "left"|"right"}``.
* ``POST /api/desk/requests/<mark|press|say|scroll>`` -- one display request
  (one ``desk_request`` frame); ``GET /api/desk/requests/{request_id}`` reads
  it; the compositor answers ``POST /api/desk/requests/{request_id}/result``.

Under ``/api/`` with no narrower right in ``principals.required_right``, so
the edge gate admits the OWNER only, like the other desk routes. The service
announces each change (one ``desk_changed`` frame, kind ``windows``); the
routes are quiet in ``web/announce.py`` so a no-op sends nothing.
"""
from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from ... import operations
from ...desk_operations import DESK_DISPLAY_OPERATIONS
from ...logging_config import get_logger
from ...services.desk_window_service import DeskWindowService, default_desk_window_service
from ...services.errors import ConflictError, NotFound, ServiceError
from ..context import WebContext
from ..operation_routes import operation_router
from ..runtime_support import error_500
from ._mount import mount_router

log = get_logger("web.routes.desk_windows")

def _status(exc: ServiceError) -> int:
    if "status" in exc.context:
        return int(exc.context["status"])
    if isinstance(exc, ConflictError):
        return 409
    if isinstance(exc, NotFound):
        return 404
    return 400


def _error(exc: ServiceError) -> JSONResponse:
    context = {key: value for key, value in exc.context.items() if key != "status"}
    return JSONResponse({"error": exc.code, "detail": exc.detail, **context}, status_code=_status(exc))


async def _answer(fn: Callable[[], Any], *, status: int = 200) -> Any:
    try:
        return JSONResponse(await run_in_threadpool(fn), status_code=status)
    except ServiceError as exc:
        return _error(exc)
    except operations.OperationRefused as exc:
        return JSONResponse({"error": exc.code, "detail": exc.detail}, status_code=400)
    except Exception as exc:
        return error_500(exc, log, "Failed to change the desk")


def build_desk_windows_router(
    ctx: WebContext, *, service: Callable[[], DeskWindowService] | None = None
) -> APIRouter:
    router = APIRouter()
    # The hub's composed instance (the one the MCP rows bind to), else a bare
    # one over the same database (a partially wired route context).
    make = service or (lambda: getattr(ctx, "desk_window_service", None) or default_desk_window_service())

    def registry() -> operations.OperationRegistry:
        """The hub's bound contract, else one over this router's service."""
        bound = getattr(ctx, "operations", None)
        if service is None and bound is not None:
            return bound
        return operations.bind({"desk_window_service": make()}, DESK_DISPLAY_OPERATIONS)

    mount_router(router, operation_router(DESK_DISPLAY_OPERATIONS, registry, _answer, module=__name__))
    return router
