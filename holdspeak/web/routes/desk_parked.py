"""PHILO-15 04 (gap 14): ``GET /api/desk/parked``, the Parked drawer's one read.

A thin adapter over ``services/parked_service.py``: every parked meeting,
Workbench item and Project, composed from the per-kind reads. A read under
``/api/`` with no narrower right in ``principals.required_right``, so the edge
gate admits the OWNER only. Restore stays on each kind's own route.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from ...logging_config import get_logger
from ...services.parked_service import parked_collection
from ..context import WebContext
from ..runtime_support import error_500

log = get_logger("web.routes.desk_parked")


def build_desk_parked_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    def _services() -> dict[str, Any]:
        # The hub's composed instances (one composition root). A context that
        # lacks one names that kind NOT READ; nothing is built here.
        return {name: getattr(ctx, name, None)
                for name in ("meeting_service", "workbench_service", "project_service")}

    @router.get("/api/desk/parked")
    async def api_desk_parked(request: Request) -> Any:
        principal = getattr(request.state, "principal", None)
        try:
            return JSONResponse(await run_in_threadpool(lambda: parked_collection(principal, **_services())))
        except Exception as exc:
            return error_500(exc, log, "Failed to read the parked objects")

    return router
