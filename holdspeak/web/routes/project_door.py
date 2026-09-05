"""HS-169-02: Project Door routes — the one-screen creation wire.

POST /api/projects/door/count   — snapshot counts for the Door UI
POST /api/projects/door         — create project + watches in one call

Parse-and-serialize ONLY: the ProjectDoorService docstring law.
Owner-scoped; typed errors → correct statuses.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ...logging_config import get_logger
from ...principals import UNAUTHENTICATED
from ...services.errors import ServiceError, ValidationError
from ..context import WebContext
from ..runtime_support import error_500

log = get_logger("web.routes.project_door")


def build_project_door_router(ctx: WebContext) -> APIRouter:
    router = APIRouter(prefix="/api/projects/door", tags=["project-door"])

    def principal(request: Request) -> Any:
        return getattr(request.state, "principal", UNAUTHENTICATED)

    def _svc_error(exc: ServiceError) -> JSONResponse:
        status = int((exc.context or {}).get("status", 400))
        return JSONResponse(
            {"code": exc.code, "message": exc.detail},
            status_code=status,
        )

    @router.post("/count")
    async def door_count(request: Request) -> Any:
        try:
            body = await request.json()
            provider = body.get("provider", "")
            scope = body.get("scope")
            watches = body.get("watches", [])
            adjust = body.get("adjust")
            if not provider or not scope:
                return JSONResponse(
                    {"code": "validation", "message": "provider and scope are required"},
                    status_code=400,
                )
            svc = ctx.project_door_service
            if svc is None:
                return JSONResponse(
                    {"code": "service_unavailable", "message": "Door service not configured"},
                    status_code=503,
                )
            result = svc.count(principal(request), provider, scope, watches, adjust)
            return JSONResponse(result)
        except ValidationError as exc:
            return JSONResponse(
                {"code": exc.code, "message": exc.detail},
                status_code=400,
            )
        except ServiceError as exc:
            return _svc_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to count door sources")

    @router.post("")
    async def door_create(request: Request) -> Any:
        try:
            body = await request.json()
            outcome = body.get("outcome", "")
            sources = body.get("sources", [])
            if not outcome or not isinstance(outcome, str):
                return JSONResponse(
                    {"code": "validation", "message": "outcome is required"},
                    status_code=400,
                )
            svc = ctx.project_door_service
            if svc is None:
                return JSONResponse(
                    {"code": "service_unavailable", "message": "Door service not configured"},
                    status_code=503,
                )
            result = svc.create(principal(request), outcome, sources)
            return JSONResponse(result)
        except ValidationError as exc:
            return JSONResponse(
                {"code": exc.code, "message": exc.detail},
                status_code=400,
            )
        except ServiceError as exc:
            return _svc_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to create project via door")

    return router
