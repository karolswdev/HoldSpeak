"""PARKED 20261109 (ops/projects): POST /api/project-setups -- no client reads it.

The web never calls it; MCP starts a setup through project.setup.start. Not imported.
Kept for history; restore with ``git revert`` of the parking commit.
"""
"""HS-159-04: Project Setup routes -- the interview on the wire.

POST /api/project-setups                              -- start

Parse-and-serialize ONLY: the ProjectSetupService docstring law.
Owner-scoped; typed errors -> correct statuses.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ...logging_config import get_logger
from ...principals import UNAUTHENTICATED
from ...services.errors import ServiceError
from ..context import WebContext
from ..runtime_support import error_500

log = get_logger("web.routes.project_setup")


def build_project_setup_router(ctx: WebContext) -> APIRouter:
    router = APIRouter(prefix="/api/project-setups", tags=["project-setup"])

    def principal(request: Request) -> Any:
        return getattr(request.state, "principal", UNAUTHENTICATED)

    def _svc_error(exc: ServiceError) -> JSONResponse:
        status = int((exc.context or {}).get("status", 400))
        return JSONResponse(
            {"code": exc.code, "message": exc.detail},
            status_code=status,
        )

    # ── POST /api/project-setups ─────────────────────────────────

    @router.post("")
    def start_setup(request: Request) -> Any:
        try:
            session = ctx.project_setup_service.start_setup(principal(request))
            return JSONResponse(session)
        except ServiceError as exc:
            return _svc_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to start setup")

    # ── GET /api/project-setups/{session_id} ─────────────────────

    # ── POST /api/project-setups/{session_id}/answers ────────────

    # ── POST /api/project-setups/{session_id}/suggest ────────────

    # ── POST /api/project-setups/{sid}/proposals/{pid}/select ────

    # ── POST /api/project-setups/{sid}/proposals/{pid}/deselect ──

    # ── POST /api/project-setups/{sid}/proposals/{pid}/clarify ───

    # ── POST /api/project-setups/{sid}/proposals/{pid}/clarify-scope

    # ── POST /api/project-setups/{sid}/proposals/{pid}/clarify-jira-scope

    # ── POST /api/project-setups/{sid}/proposals/{pid}/test ──────

    # ── POST /api/project-setups/{session_id}/finalize ───────────

    # ── POST /api/project-setups/{session_id}/abandon ────────────

    return router
