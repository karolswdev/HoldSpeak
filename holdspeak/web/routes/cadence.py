"""Cadence transport adapters; cadence state lives in the application service."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Body, HTTPException, Request

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
    async def status(request: Request) -> dict[str, Any]:
        return service.status(principal(request))

    @router.get("/loops")
    async def loops(request: Request, all: bool = False) -> dict[str, Any]:
        return service.list_loops(principal(request), include_terminal=all)

    @router.get("/brief")
    async def brief(request: Request) -> dict[str, Any]:
        return service.brief(principal(request))

    @router.get("/closeout")
    async def closeout(request: Request) -> dict[str, Any]:
        return service.closeout(principal(request))

    @router.post("/closeout/apply")
    async def closeout_apply(request: Request, body: dict = Body(default={})) -> dict[str, Any]:
        return service.apply_closeout(principal(request), body)

    @router.get("/history")
    async def history(request: Request, limit: int = 50) -> dict[str, Any]:
        return service.history(principal(request), limit=limit)

    @router.get("/audit")
    async def audit(request: Request) -> dict[str, Any]:
        return service.audit(principal(request))

    @router.get("/loops/{loop_id}")
    async def loop_detail(request: Request, loop_id: str) -> dict[str, Any]:
        try:
            return await service.get_loop(principal(request), loop_id)
        except ServiceError as exc:
            _raise(exc)

    # These existing lifecycle actions remain local-only. They delegate through
    # the same service-owned database rather than reopening a route database seam.
    @router.post("/loops/{loop_id}/snooze")
    async def snooze(request: Request, loop_id: str, body: dict = Body(default={})) -> dict[str, Any]:
        return service.snooze(principal(request), loop_id, body)

    @router.post("/loops/{loop_id}/kill")
    async def kill(request: Request, loop_id: str) -> dict[str, Any]:
        return service.set_status(principal(request), loop_id, "killed")

    @router.post("/loops/{loop_id}/close")
    async def close(request: Request, loop_id: str) -> dict[str, Any]:
        return service.set_status(principal(request), loop_id, "closed")

    @router.post("/loops/{loop_id}/reply")
    async def reply(request: Request, loop_id: str, body: dict = Body(default={})) -> dict[str, Any]:
        """Answer a waiting agent from the desk. Refuses by name; never guesses text."""
        try:
            return await asyncio.to_thread(service.reply, principal(request), loop_id, body)
        except ServiceError as exc:
            _raise(exc)

    @router.post("/run-now")
    async def run_now(request: Request) -> dict[str, Any]:
        return service.run_now(principal(request))

    return router
