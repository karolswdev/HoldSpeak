"""HS-169-02: Project Door routes — the one-screen creation wire.

POST /api/projects/door/count   — snapshot counts for the Door UI
POST /api/projects/door         — create project + watches in one call

Parse-and-serialize ONLY: the ProjectDoorService docstring law.
Owner-scoped; typed errors → correct statuses.
"""
from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ... import operations
from ...logging_config import get_logger
from ...operations import OperationRefused
from ...principals import UNAUTHENTICATED
from ...services.errors import ServiceError, ValidationError
from ..context import WebContext
from ..runtime_support import error_500
from ._room_kernel import (
    body_or_refusal, exempt_form_right, kernel_fields, kernel_refusal, refuse_identifiable, refusal_fields,
)

log = get_logger("web.routes.project_door")


def build_project_door_router(ctx: WebContext) -> APIRouter:
    router = APIRouter(prefix="/api/projects/door", tags=["project-door"])

    def principal(request: Request) -> Any:
        return getattr(request.state, "principal", UNAUTHENTICATED)

    def _svc_error(exc: ServiceError) -> JSONResponse:
        status = int((exc.context or {}).get("status", 400))
        return JSONResponse(
            {"code": exc.code, "message": exc.detail, **refusal_fields(exc)},
            status_code=status,
        )

    def ops() -> Any:
        return operations.for_context(ctx)

    @router.post("/count")
    async def door_count(request: Request) -> Any:
        # PHILO-9-02: admitted on its route (egress: it reads GitHub/Jira, F21).
        p = principal(request)
        body, refused = await body_or_refusal(request, ops(), p, "project.door.count")
        if refused is not None:
            return refused
        try:
            if not body.get("provider") or not body.get("scope"):
                kernel = refuse_identifiable(ops(), p, "project.door.count", "invalid_arguments")
                return JSONResponse(
                    {"code": "validation", "message": "provider and scope are required", **kernel_fields(kernel)},
                    status_code=400,
                )
            if ctx.project_door_service is None:
                return JSONResponse(
                    {"code": "service_unavailable", "message": "Door service not configured"},
                    status_code=503,
                )
            result, kernel = ops().invoke_receipted(p, "project.door.count", {
                "provider": body.get("provider", ""), "scope": body.get("scope"),
                "watches": body.get("watches", []), "adjust": body.get("adjust"),
            })
            return JSONResponse({**result, **kernel_fields(kernel)} if isinstance(result, dict) else result)
        except OperationRefused as exc:
            return JSONResponse({"code": "validation", "message": exc.detail, **refusal_fields(exc)}, status_code=400)
        except ValidationError as exc:
            return JSONResponse(
                {"code": exc.code, "message": exc.detail, **refusal_fields(exc)},
                status_code=400,
            )
        except ServiceError as exc:
            if (refused := kernel_refusal(exc)) is not None:
                return refused
            return _svc_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to count door sources")

    @router.post("")
    async def door_create(request: Request) -> Any:
        # PHILO-9-02: conditional. With sources: admitted (armed watches read
        # GitHub/Jira: egress). Bare: exempt, and its previous edge right
        # (OWNER) is re-applied HERE, before any service call.
        p = principal(request)
        raw_bytes = await request.body()
        try:
            body = json.loads(raw_bytes) if raw_bytes.strip() else None
        except ValueError:
            body = None
        if not isinstance(body, dict):
            # Identifiable, but the exempt form cannot be proved: invalid_arguments, with its receipt.
            kernel = refuse_identifiable(ops(), p, "project.door.create", "invalid_arguments")
            return JSONResponse({"code": "validation", "message": "the body must be a JSON object",
                                 **kernel_fields(kernel)}, status_code=400)
        sources = body.get("sources", [])
        if not sources and (refused := exempt_form_right(p)) is not None:
            return refused
        try:
            outcome = body.get("outcome", "")
            if not outcome or not isinstance(outcome, str):
                kernel = (refuse_identifiable(ops(), p, "project.door.create", "invalid_arguments")
                          if sources else None)
                return JSONResponse(
                    {"code": "validation", "message": "outcome is required", **kernel_fields(kernel)},
                    status_code=400,
                )
            svc = ctx.project_door_service
            if svc is None:
                return JSONResponse(
                    {"code": "service_unavailable", "message": "Door service not configured"},
                    status_code=503,
                )
            # PHILO-9-01: the declared project.door.create, beside project.create.
            result, kernel = ops().invoke_receipted(p, "project.door.create", {
                "outcome": outcome, "sources": sources,
            })
            return JSONResponse({**result, **kernel_fields(kernel)} if isinstance(result, dict) else result)
        except OperationRefused as exc:
            return JSONResponse({"code": "validation", "message": exc.detail, **refusal_fields(exc)}, status_code=400)
        except ValidationError as exc:
            return JSONResponse(
                {"code": exc.code, "message": exc.detail, **refusal_fields(exc)},
                status_code=400,
            )
        except ServiceError as exc:
            if (refused := kernel_refusal(exc)) is not None:
                return refused
            return _svc_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to create project via door")

    return router
