"""PARKED 20261109 (ops/programs-work): hand-written desk-state routes, now produced.

GET /api/desk/projections, PUT /api/desk/projections/{id}/presentation,
GET /api/today/since-morning, GET /health, POST /api/desk/seed and
POST /api/desk/reset are rows in ``holdspeak/desk_state_operations.py``: each
produces its route (same method, path and answer) and its MCP tool. Kept here
as they stood in ``web/routes/projections.py``, ``today.py``, ``desk_seed.py``
and ``core.py``.

Not imported. Restore with git revert of the parking commit.
"""
# ruff: noqa
# fmt: off
PARKED = True

'''
# ---- projections.py ----
"""Thin HTTP adapters for durable Desk projections (HS-123-05)."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from ...logging_config import get_logger
from ...principals import UNAUTHENTICATED
from ...services.errors import NotFound, ValidationError
from ...services.projection_service import ProjectionService
from ..context import WebContext
from ..runtime_support import error_500

log = get_logger("web.routes.projections")


def build_projections_router(ctx: WebContext) -> APIRouter:
    router = APIRouter(prefix="/api/desk/projections", tags=["desk"])
    service: ProjectionService = ctx.projection_service

    def principal(request: Request) -> Any:
        return getattr(request.state, "principal", UNAUTHENTICATED)

    @router.get("")
    async def api_list_projections(
        request: Request, q: str = "", kind: str | None = None,
        attention_state: str | None = None, subject_ref: str | None = None,
        include_dismissed: bool = False, offset: int = 0, limit: int = 50,
    ) -> Any:
        try:
            result = await run_in_threadpool(service.list, principal(request), {"q": q, "kind": kind,
                "attention_state": attention_state, "subject_ref": subject_ref,
                "include_dismissed": include_dismissed, "offset": offset, "limit": limit})
            return JSONResponse({"version": 1, **result})
        except ValidationError as exc:
            return JSONResponse({"error": exc.detail}, status_code=400)
        except (TypeError, ValueError) as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to project Desk attention and receipts")

    @router.put("/{projection_id}/presentation")
    async def api_set_projection_presentation(projection_id: str, request: Request) -> Any:
        try:
            body = await request.json()
        except Exception:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            return JSONResponse(service.set_presentation(principal(request), projection_id, body))
        except NotFound:
            return JSONResponse({"error": "Projection not found"}, status_code=404)
        except ValidationError as exc:
            return JSONResponse({"error": exc.detail}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to update projection presentation")

    return router


__all__ = ["build_projections_router"]

# ---- today.py ----
"""Today's own reads (DELIGHT slice 5, 2026-10-28).

``GET /api/today/since-morning``: what got done today (tasks ticked,
decisions recorded, notes filed, sends sent, meetings held), newest first.
Today draws it after 17:00 as Since this morning; its ``programs`` block (PG18)
feeds the Programs line at any hour. The read goes through the
one Today service; the router builds a service only when the context has
none (a route test)."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from ...db import get_database
from ...logging_config import get_logger
from ...principals import UNAUTHENTICATED
from ...services.today_service import TodayService
from ..context import WebContext
from ..runtime_support import error_500

log = get_logger("web.routes.today")


def build_today_router(ctx: WebContext) -> APIRouter:
    router = APIRouter(prefix="/api/today", tags=["today"])

    def service() -> TodayService:
        return getattr(ctx, "today_service", None) or TodayService(get_database())

    @router.get("/since-morning")
    async def since_morning(request: Request) -> Any:
        principal = getattr(request.state, "principal", UNAUTHENTICATED)
        try:
            return JSONResponse(await run_in_threadpool(service().since_morning, principal))
        except Exception as exc:
            return error_500(exc, log, "Failed to read what got done today")

    return router

# ---- desk_seed.py ----
"""The architect's desk — seed + reset routes (HS-112-03).

Thin wrappers over ``holdspeak.db.seed`` (the same repositories the
primitive routes wrap). Both are POSTs under ``/api/`` with no narrower
right named in ``principals.required_right``, so the centralized edge
gate requires the OWNER principal — reset is the desk's first
destructive act and belongs to the owner alone.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ...logging_config import get_logger
from ...services.desk_service import DeskService
from ..context import WebContext
from ..runtime_support import error_500

log = get_logger("web.routes.desk_seed")


def build_desk_seed_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    def _svc() -> DeskService:
        from ...db import get_database, get_observer

        return DeskService(get_database(), observer=get_observer())

    @router.post("/api/desk/seed")
    def api_desk_seed(request: Request) -> Any:
        try:
            return JSONResponse(_svc().seed(getattr(request.state, "principal", None)))
        except Exception as exc:
            return error_500(exc, log, "Failed to seed the desk")

    @router.post("/api/desk/reset")
    def api_desk_reset(request: Request) -> Any:
        try:
            return JSONResponse(_svc().reset(getattr(request.state, "principal", None)))
        except Exception as exc:
            return error_500(exc, log, "Failed to reset the desk")

    return router

# ---- core.py (/health) ----
    @router.get("/health")
    def health() -> Any:
        from ...db import get_database, get_observer

        return JSONResponse(DeskService(get_database(), observer=get_observer()).health())

'''
