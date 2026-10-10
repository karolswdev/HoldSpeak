"""PHILO-16 (16b): the desk's windows over HTTP (COMPOSITOR.md §13 L1, L10).

Thin: read the body, call ``services/desk_window_service.py``, serialize.

* ``GET  /api/desk/windows`` -- every open window, back to front, the desk's
  Stage shelf, and the window registry.
* ``POST /api/desk/windows/{window_id}/{verb}`` -- one verb on one window:
  ``open close move resize set_geometry raise send_back seat zoom``. The body
  carries the verb's arguments and an optional ``expected_revision``.
* ``POST /api/desk/windows/arrange`` -- many rects, one transaction, one frame.
* ``POST /api/desk/windows/stage-shelf`` -- ``{"side": "left"|"right"}``.

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

from ...logging_config import get_logger
from ...services.desk_window_service import (
    VERBS,
    DeskWindowService,
    call_verb,
    default_desk_window_service,
)
from ...services.errors import ConflictError, NotFound, ServiceError
from ..context import WebContext
from ..runtime_support import error_500

log = get_logger("web.routes.desk_windows")

def _status(exc: ServiceError) -> int:
    if isinstance(exc, ConflictError):
        return 409
    if isinstance(exc, NotFound):
        return 404
    return 400


def _error(exc: ServiceError) -> JSONResponse:
    return JSONResponse(
        {"error": exc.code, "detail": exc.detail, **exc.context}, status_code=_status(exc)
    )


def build_desk_windows_router(
    ctx: WebContext, *, service: Callable[[], DeskWindowService] | None = None
) -> APIRouter:
    router = APIRouter()
    # The hub's composed instance (the one the MCP rows bind to), else a bare
    # one over the same database (a partially wired route context).
    make = service or (lambda: getattr(ctx, "desk_window_service", None) or default_desk_window_service())

    async def _run(fn: Callable[[], Any], what: str) -> Any:
        try:
            return JSONResponse(await run_in_threadpool(fn))
        except ServiceError as exc:
            return _error(exc)
        except Exception as exc:
            return error_500(exc, log, what)

    async def _body(request: Request) -> dict[str, Any]:
        try:
            body = await request.json()
        except Exception:
            return {}
        return body if isinstance(body, dict) else {}

    @router.get("/api/desk/windows")
    async def api_desk_windows(request: Request) -> Any:
        return await _run(lambda: make().list(), "Failed to read the desk's windows")

    @router.post("/api/desk/windows/arrange")
    async def api_desk_windows_arrange(request: Request) -> Any:
        body = await _body(request)
        return await _run(
            lambda: make().arrange(body.get("rects") or {}, expected_revisions=body.get("expected_revisions")),
            "Failed to arrange the desk's windows",
        )

    @router.post("/api/desk/windows/stage-shelf")
    async def api_desk_windows_shelf(request: Request) -> Any:
        body = await _body(request)
        return await _run(
            lambda: make().set_stage_shelf(str(body.get("side") or ""), expected_revision=body.get("expected_revision")),
            "Failed to set the Stage shelf",
        )

    @router.post("/api/desk/windows/{window_id}/{verb}")
    async def api_desk_window_verb(window_id: str, verb: str, request: Request) -> Any:
        body = await _body(request)
        if verb not in VERBS:
            return JSONResponse({"error": "window_verb_unknown", "detail": f"No window verb {verb!r}",
                                 "verbs": list(VERBS)}, status_code=404)
        return await _run(lambda: call_verb(make(), window_id, verb, body), f"Failed to {verb} the window")

    return router
