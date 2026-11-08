"""PARKED 20261108 (subtraction day, Lane R): routes no client reads.

Parked from ``holdspeak/web/routes/cadence.py``: GET /audit, GET /brief, GET /closeout.
Not imported. Kept for history; restore with ``git revert`` of the parking commit.
"""
from __future__ import annotations
"""Cadence transport adapters; cadence state lives in the application service."""

from typing import Any

from fastapi import APIRouter, HTTPException, Request

from ....db import get_observer
from ....principals import UNAUTHENTICATED
from ....services.errors import ConflictError, NotFound, ServiceError
from ...context import WebContext


def _raise(exc: ServiceError) -> None:
    if isinstance(exc, NotFound):
        raise HTTPException(status_code=404, detail="loop not found") from exc
    if isinstance(exc, ConflictError):
        # The loop is answerable in principle; the world is not ready for it
        # (no live pane, delivery refused). Distinct from a malformed request.
        raise HTTPException(status_code=409, detail=exc.detail) from exc
    raise HTTPException(status_code=400, detail=exc.detail) from exc


def parked_build_cadence_router(ctx: WebContext) -> APIRouter:
    router = APIRouter(prefix="/api/cadence", tags=["cadence"])
    service = ctx.cadence_service
    if service is None:  # compatibility composition for isolated route fixtures
        from .... import db as hsdb
        from ....config import Config
        from ....services.cadence_service import CadenceService
        service = CadenceService(hsdb.get_database(), Config.load().cadence, observer=get_observer())
    principal = lambda request: getattr(request.state, "principal", UNAUTHENTICATED)

    @router.get("/brief")
    def brief(request: Request) -> dict[str, Any]:
        return service.brief(principal(request))

    @router.get("/closeout")
    def closeout(request: Request) -> dict[str, Any]:
        return service.closeout(principal(request))

    @router.get("/audit")
    def audit(request: Request) -> dict[str, Any]:
        return service.audit(principal(request))

    return router
