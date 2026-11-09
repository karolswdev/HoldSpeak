"""Cadence transport adapters; cadence state lives in the application service."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from ...db import get_observer
from ...principals import UNAUTHENTICATED
from ...services.errors import ConflictError, NotFound, ServiceError
from ..context import WebContext


def _raise(exc: ServiceError) -> None:
    if isinstance(exc, NotFound):
        raise HTTPException(status_code=404, detail="loop not found") from exc
    if isinstance(exc, ConflictError):
        # The loop is answerable in principle; the world is not ready for it
        # (no live pane, delivery refused). Distinct from a malformed request.
        raise HTTPException(status_code=409, detail=exc.detail) from exc
    raise HTTPException(status_code=400, detail=exc.detail) from exc


async def _reply_answer(fn: Any, *, status: int = 200) -> JSONResponse:
    """The reply's answer: its result, or the refusal as ``_raise`` words it (``{detail}``)."""
    try:
        return JSONResponse(await run_in_threadpool(fn), status_code=status)
    except ServiceError as exc:
        try:
            _raise(exc)
        except HTTPException as http:
            code = 403 if exc.code == "owner_required" else http.status_code
            return JSONResponse({"detail": http.detail, "code": exc.code}, status_code=code)
        raise  # pragma: no cover - _raise always raises


def build_cadence_router(ctx: WebContext) -> APIRouter:
    router = APIRouter(prefix="/api/cadence", tags=["cadence"])
    service = ctx.cadence_service
    if service is None:  # compatibility composition for isolated route fixtures
        from ... import db as hsdb
        from ...config import Config
        from ...services.cadence_service import CadenceService
        service = CadenceService(hsdb.get_database(), Config.load().cadence, observer=get_observer())
    principal = lambda request: getattr(request.state, "principal", UNAUTHENTICATED)

    @router.get("/status")
    def status(request: Request) -> dict[str, Any]:
        return service.status(principal(request))

    @router.get("/loops")
    def loops(request: Request, all: bool = False) -> dict[str, Any]:
        return service.list_loops(principal(request), include_terminal=all)

    @router.get("/history")
    def history(request: Request, limit: int = 50) -> dict[str, Any]:
        return service.history(principal(request), limit=limit)

    # These existing lifecycle actions remain local-only. They delegate through
    # the same service-owned database rather than reopening a route database seam.
    @router.post("/loops/{loop_id}/snooze")
    def snooze(request: Request, loop_id: str, body: dict = Body(default={})) -> dict[str, Any]:
        return service.snooze(principal(request), loop_id, body)

    @router.post("/loops/{loop_id}/kill")
    def kill(request: Request, loop_id: str) -> dict[str, Any]:
        return service.set_status(principal(request), loop_id, "killed")

    @router.post("/loops/{loop_id}/close")
    def close(request: Request, loop_id: str) -> dict[str, Any]:
        return service.set_status(principal(request), loop_id, "closed")

    # 2026-11-09 (ops/projects): the reply is the declared cadence.reply
    # (owner-only; ``project_operations.py``). Refuses by name; never guesses text.
    from ...project_operations import PROJECT_OPERATIONS
    from ._mount import mount_router
    from ._produced import produced

    outer = APIRouter()
    mount_router(outer, router)
    mount_router(outer, produced(ctx, [d for d in PROJECT_OPERATIONS if d.name == "cadence.reply"],
                                 _reply_answer, module=__name__, cadence_service=lambda: service))
    return outer
