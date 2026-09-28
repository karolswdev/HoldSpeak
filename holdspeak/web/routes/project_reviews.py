"""HS-160-05: Project Review routes -- the Delta wire.

POST /api/projects/{project_id}/reviews                              -- open_review
GET  /api/projects/{project_id}/reviews/{review_id}                  -- frozen window
GET  /api/projects/{project_id}/delta                                -- open window or honest empty
POST /api/projects/{project_id}/reviews/{review_id}/proposals/{proposal_id}/decide
POST /api/projects/{project_id}/reviews/{review_id}/accept

Parse-and-serialize ONLY: the ProjectDeltaService docstring law.
Owner-scoped; typed errors -> correct statuses.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ... import operations
from ...logging_config import get_logger
from ...operations import OperationRefused
from ...principals import UNAUTHENTICATED
from ...services.errors import ConflictError, NotFound, ServiceError, ValidationError
from ..context import WebContext
from ..runtime_support import error_500
from ._room_kernel import body_or_refusal, kernel_fields, kernel_refusal, refusal_fields

log = get_logger("web.routes.project_reviews")


def build_project_reviews_router(ctx: WebContext) -> APIRouter:
    router = APIRouter(prefix="/api/projects", tags=["project-reviews"])

    def principal(request: Request) -> Any:
        return getattr(request.state, "principal", UNAUTHENTICATED)

    def ops() -> Any:
        """PHILO-9-01: the Room's declared operations, bound to the hub's services."""
        return operations.for_context(ctx)

    # ── POST /api/projects/{project_id}/reviews ─────────────────────

    @router.post("/{project_id}/reviews")
    async def open_review(project_id: str, request: Request) -> Any:
        try:
            result = ops().invoke(principal(request), "project.open_review", {"project_id": project_id})
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
        except ConflictError as exc:
            return JSONResponse(
                {"code": exc.code, "message": exc.detail},
                status_code=409,
            )
        except Exception as exc:
            return error_500(exc, log, "Failed to open review")

    # ── GET /api/projects/{project_id}/reviews/{review_id} ──────────

    @router.get("/{project_id}/reviews/{review_id}")
    async def get_review(
        project_id: str, review_id: str, request: Request,
    ) -> Any:
        try:
            review = ctx.project_delta_service._db.project_observations.get_review(
                review_id,
            )
            if review is None:
                return JSONResponse(
                    {"code": "not_found", "message": f"Review {review_id!r} not found"},
                    status_code=404,
                )
            if review["project_id"] != project_id:
                return JSONResponse(
                    {"code": "not_found",
                     "message": f"Review {review_id!r} does not belong to project {project_id!r}"},
                    status_code=404,
                )
            window = ctx.project_delta_service._load_frozen_window(review)
            return JSONResponse(window)
        except Exception as exc:
            return error_500(exc, log, "Failed to get review")

    # ── GET /api/projects/{project_id}/delta ─────────────────────────

    @router.get("/{project_id}/delta")
    async def get_delta(project_id: str, request: Request) -> Any:
        try:
            # PHILO-9-01: the declared project.get_delta (the open window, or
            # the honest empty state, WEB-STA-004), the read MCP reaches too.
            return JSONResponse(ops().invoke(principal(request), "project.get_delta", {"project_id": project_id}))
        except NotFound as exc:
            return JSONResponse(
                {"code": exc.code, "message": exc.detail},
                status_code=404,
            )
        except Exception as exc:
            return error_500(exc, log, "Failed to get delta")

    # ── POST .../proposals/{proposal_id}/decide ─────────────────────
    # PHILO-9-02: admitted, all four verbs (each decides): one operation and
    # one receipt; an agent is refused project_delegation_required with one.

    def _refusal(exc: ServiceError) -> JSONResponse:
        if (refused := kernel_refusal(exc)) is not None:
            return refused
        status = 404 if isinstance(exc, NotFound) else 400 if isinstance(exc, ValidationError) else 409
        return JSONResponse({"code": exc.code, "message": exc.detail, **refusal_fields(exc)}, status_code=status)

    @router.post("/{project_id}/reviews/{review_id}/proposals/{proposal_id}/decide")
    async def decide_proposal(
        project_id: str, review_id: str, proposal_id: str,
        request: Request,
    ) -> Any:
        body, refused = await body_or_refusal(request, ops(), principal(request), "project.decide_proposal")
        if refused is not None:
            return refused
        try:
            # PHILO-9-01: the declared project.decide_proposal; the service
            # checks the proposal belongs to this review first (review_id).
            result, kernel = ops().invoke_receipted(principal(request), "project.decide_proposal", {
                "project_id": project_id, "review_id": review_id, "proposal_id": proposal_id,
                "verb": body.get("verb", ""), "patch": body.get("patch"),
                "deferred_until": body.get("deferred_until"), "command_id": body.get("command_id"),
            })
            return JSONResponse({**result, **kernel_fields(kernel)} if isinstance(result, dict) else result)
        except OperationRefused as exc:
            return JSONResponse({"code": "validation", "message": exc.detail, **refusal_fields(exc)}, status_code=400)
        except ServiceError as exc:
            return _refusal(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to decide proposal")

    # ── POST .../reviews/{review_id}/accept ─────────────────────────

    @router.post("/{project_id}/reviews/{review_id}/accept")
    async def accept_review(
        project_id: str, review_id: str, request: Request,
    ) -> Any:
        body, refused = await body_or_refusal(request, ops(), principal(request), "project.accept_review",
                                              optional=True)
        if refused is not None:
            return refused
        try:
            result, kernel = ops().invoke_receipted(principal(request), "project.accept_review", {
                "project_id": project_id, "review_id": review_id, "command_id": body.get("command_id"),
            })
            return JSONResponse({**result, **kernel_fields(kernel)} if isinstance(result, dict) else result)
        except OperationRefused as exc:
            return JSONResponse({"code": "validation", "message": exc.detail, **refusal_fields(exc)}, status_code=400)
        except ServiceError as exc:
            return _refusal(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to accept review")

    return router
