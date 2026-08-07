"""Sync transport adapters; merge and serialization live in :mod:`holdspeak.services.sync_service`."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ...principals import UNAUTHENTICATED
from ...services.errors import ConflictError, ServiceError, ValidationError
from ...services.sync_service import (
    SYNC_KINDS,
    _MERGEABLE,
    _artifact_value,
    _hub_model_name,
    _iso,
    meeting_state_from_sync_value,
)
from ..context import WebContext


def _error(exc: ServiceError) -> JSONResponse:
    payload = {"success": False, "error": exc.detail, **exc.context}
    if isinstance(exc, ConflictError):
        return JSONResponse(payload, status_code=409)
    return JSONResponse(payload, status_code=422 if isinstance(exc, ValidationError) else 400)


def build_sync_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()
    service = ctx.sync_service
    if service is None:  # compatibility composition for isolated route fixtures
        from ... import db as hsdb
        from ...services.sync_service import SyncService
        service = SyncService(hsdb.get_database(), hub_model_name=lambda: _hub_model_name(None))

    @router.get("/api/sync/pull")
    async def api_sync_pull(request: Request, limit: int = 50) -> Any:
        try:
            return JSONResponse(service.pull(getattr(request.state, "principal", UNAUTHENTICATED), limit=limit))
        except ServiceError as exc:
            return _error(exc)

    @router.post("/api/sync/push")
    async def api_sync_push(request: Request) -> Any:
        try:
            body = await request.json()
        except Exception:
            return JSONResponse({"success": False, "error": "invalid JSON"}, status_code=400)
        try:
            return JSONResponse(service.push(getattr(request.state, "principal", UNAUTHENTICATED), body))
        except ServiceError as exc:
            return _error(exc)

    return router
