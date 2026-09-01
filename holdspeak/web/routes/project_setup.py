"""HS-159-04: Project Setup routes -- the interview on the wire.

POST /api/project-setups                              -- start
GET  /api/project-setups/{session_id}                 -- resume read
POST /api/project-setups/{session_id}/answers         -- answer
POST /api/project-setups/{session_id}/suggest         -- suggest
POST /api/project-setups/{session_id}/proposals/{id}/select
POST /api/project-setups/{session_id}/proposals/{id}/deselect
POST /api/project-setups/{session_id}/proposals/{id}/clarify
POST /api/project-setups/{session_id}/proposals/{id}/test
POST /api/project-setups/{session_id}/finalize        -- finalize
POST /api/project-setups/{session_id}/abandon         -- abandon

Parse-and-serialize ONLY: the ProjectSetupService docstring law.
Owner-scoped; typed errors -> correct statuses.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ...logging_config import get_logger
from ...principals import UNAUTHENTICATED
from ...services.errors import ConflictError, NotFound, ServiceError, ValidationError
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
    async def start_setup(request: Request) -> Any:
        try:
            session = ctx.project_setup_service.start_setup(principal(request))
            return JSONResponse(session)
        except ServiceError as exc:
            return _svc_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to start setup")

    # ── GET /api/project-setups/{session_id} ─────────────────────

    @router.get("/{session_id}")
    async def get_setup(session_id: str, request: Request) -> Any:
        try:
            return JSONResponse(
                ctx.project_setup_service.get_setup(session_id),
            )
        except NotFound as exc:
            return JSONResponse(
                {"code": exc.code, "message": exc.detail},
                status_code=404,
            )
        except ServiceError as exc:
            return _svc_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to get setup")

    # ── POST /api/project-setups/{session_id}/answers ────────────

    @router.post("/{session_id}/answers")
    async def answer(session_id: str, request: Request) -> Any:
        try:
            body = await request.json()
            question_id = body.get("question_id", "")
            payload = body.get("payload", {})
            result = ctx.project_setup_service.answer(
                principal(request), session_id, question_id, payload,
            )
            return JSONResponse(result)
        except NotFound as exc:
            return JSONResponse(
                {"code": exc.code, "message": exc.detail},
                status_code=404,
            )
        except ValidationError as exc:
            return JSONResponse(
                {"code": exc.code, "message": exc.detail},
                status_code=400,
            )
        except ServiceError as exc:
            return _svc_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to answer setup question")

    # ── POST /api/project-setups/{session_id}/suggest ────────────

    @router.post("/{session_id}/suggest")
    async def suggest(session_id: str, request: Request) -> Any:
        try:
            proposals = ctx.project_setup_service.suggest(
                principal(request), session_id,
            )
            return JSONResponse({"proposals": proposals})
        except NotFound as exc:
            return JSONResponse(
                {"code": exc.code, "message": exc.detail},
                status_code=404,
            )
        except ServiceError as exc:
            return _svc_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to generate suggestions")

    # ── POST /api/project-setups/{sid}/proposals/{pid}/select ────

    @router.post("/{session_id}/proposals/{proposal_id}/select")
    async def select_proposal(
        session_id: str, proposal_id: str, request: Request,
    ) -> Any:
        try:
            result = ctx.project_setup_service.select_proposal(
                principal(request), session_id, proposal_id,
            )
            return JSONResponse(result)
        except NotFound as exc:
            return JSONResponse(
                {"code": exc.code, "message": exc.detail},
                status_code=404,
            )
        except ValidationError as exc:
            return JSONResponse(
                {"code": exc.code, "message": exc.detail},
                status_code=400,
            )
        except ServiceError as exc:
            return _svc_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to select proposal")

    # ── POST /api/project-setups/{sid}/proposals/{pid}/deselect ──

    @router.post("/{session_id}/proposals/{proposal_id}/deselect")
    async def deselect_proposal(
        session_id: str, proposal_id: str, request: Request,
    ) -> Any:
        try:
            result = ctx.project_setup_service.deselect_proposal(
                principal(request), session_id, proposal_id,
            )
            return JSONResponse(result)
        except NotFound as exc:
            return JSONResponse(
                {"code": exc.code, "message": exc.detail},
                status_code=404,
            )
        except ValidationError as exc:
            return JSONResponse(
                {"code": exc.code, "message": exc.detail},
                status_code=400,
            )
        except ServiceError as exc:
            return _svc_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to deselect proposal")

    # ── POST /api/project-setups/{sid}/proposals/{pid}/clarify ───

    @router.post("/{session_id}/proposals/{proposal_id}/clarify")
    async def clarify_proposal(
        session_id: str, proposal_id: str, request: Request,
    ) -> Any:
        try:
            body = await request.json()
            patch = body.get("patch", body)
            result = ctx.project_setup_service.clarify_proposal(
                principal(request), session_id, proposal_id, patch,
            )
            return JSONResponse(result)
        except NotFound as exc:
            return JSONResponse(
                {"code": exc.code, "message": exc.detail},
                status_code=404,
            )
        except ValidationError as exc:
            return JSONResponse(
                {"code": exc.code, "message": exc.detail},
                status_code=400,
            )
        except ServiceError as exc:
            return _svc_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to clarify proposal")

    # ── POST /api/project-setups/{sid}/proposals/{pid}/test ──────

    @router.post("/{session_id}/proposals/{proposal_id}/test")
    async def test_proposal(
        session_id: str, proposal_id: str, request: Request,
    ) -> Any:
        try:
            result = ctx.project_setup_service.test_proposal(
                principal(request), session_id, proposal_id,
            )
            return JSONResponse(result)
        except NotFound as exc:
            return JSONResponse(
                {"code": exc.code, "message": exc.detail},
                status_code=404,
            )
        except ServiceError as exc:
            return _svc_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to test proposal")

    # ── POST /api/project-setups/{session_id}/finalize ───────────

    @router.post("/{session_id}/finalize")
    async def finalize(session_id: str, request: Request) -> Any:
        try:
            body = await request.json()
            cmd_id = body.get("command_id")
            result = ctx.project_setup_service.finalize(
                principal(request), session_id, command_id=cmd_id,
            )
            return JSONResponse(result)
        except NotFound as exc:
            return JSONResponse(
                {"code": exc.code, "message": exc.detail},
                status_code=404,
            )
        except ConflictError as exc:
            return JSONResponse(
                {"code": exc.code, "message": exc.detail},
                status_code=409,
            )
        except ServiceError as exc:
            return _svc_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to finalize setup")

    # ── POST /api/project-setups/{session_id}/abandon ────────────

    @router.post("/{session_id}/abandon")
    async def abandon(session_id: str, request: Request) -> Any:
        try:
            result = ctx.project_setup_service.abandon(
                principal(request), session_id,
            )
            return JSONResponse(result)
        except NotFound as exc:
            return JSONResponse(
                {"code": exc.code, "message": exc.detail},
                status_code=404,
            )
        except ServiceError as exc:
            return _svc_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to abandon setup")

    return router
