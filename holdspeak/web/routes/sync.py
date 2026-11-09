"""Sync transport adapters; merge and serialization live in :mod:`holdspeak.services.sync_service`.

The three routes are produced from ``holdspeak/device_operations.py`` (2026-11-09, one contract).
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from ... import operations
from ...db import get_observer
from ...services.errors import ConflictError, NotFound, ServiceError, ValidationError
from ...services.sync_service import (  # noqa: F401 (re-exported for the sync tests)
    SYNC_KINDS,
    _MERGEABLE,
    _artifact_value,
    _hub_model_name,
    _iso,
    meeting_state_from_sync_value,
)
from ..context import WebContext
from ..operation_routes import operation_router
from ._mount import mount_router


def _error(exc: ServiceError) -> JSONResponse:
    payload = {"success": False, "error": exc.code, "detail": exc.detail, **exc.context}
    if isinstance(exc, NotFound):
        return JSONResponse(payload, status_code=404)
    if isinstance(exc, ConflictError):
        return JSONResponse(payload, status_code=409)
    return JSONResponse(payload, status_code=422 if isinstance(exc, ValidationError) else 400)


async def _answer(fn: Any, *, status: int = 200) -> Any:
    try:
        return JSONResponse(await run_in_threadpool(fn), status_code=status)
    except ServiceError as exc:
        return _error(exc)


def build_sync_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    def fallback() -> Any:  # compatibility composition for isolated route fixtures
        from ... import db as hsdb
        from ...services.sync_service import SyncService

        return SyncService(hsdb.get_database(), hub_model_name=lambda: _hub_model_name(None), observer=get_observer())

    def registry() -> operations.OperationRegistry:
        return operations.for_context(ctx, sync_service=fallback)

    by_name = {d.name: d for d in operations.DEVICE_OPERATIONS}
    mount_router(router, operation_router([by_name[name] for name in ("sync.artifact.get", "sync.pull", "sync.push")],
                                          registry, _answer, module=__name__))
    return router
