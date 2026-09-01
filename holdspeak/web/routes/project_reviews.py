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

from ...logging_config import get_logger
from ...principals import UNAUTHENTICATED
from ...services.errors import ConflictError, NotFound, ServiceError, ValidationError
from ..context import WebContext
from ..runtime_support import error_500

log = get_logger("web.routes.project_reviews")


def build_project_reviews_router(ctx: WebContext) -> APIRouter:
    router = APIRouter(prefix="/api/projects", tags=["project-reviews"])

    def principal(request: Request) -> Any:
        return getattr(request.state, "principal", UNAUTHENTICATED)

    # ── POST /api/projects/{project_id}/reviews ─────────────────────

    @router.post("/{project_id}/reviews")
    async def open_review(project_id: str, request: Request) -> Any:
        try:
            result = ctx.project_delta_service.open_review(
                principal(request), project_id,
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
            # Verify project exists
            project = ctx.project_service._require_project(project_id)

            delta_svc = ctx.project_delta_service

            # Check for an open review
            open_review = delta_svc._find_open_review(project_id)
            if open_review is not None:
                window = delta_svc._load_frozen_window(open_review)
                return JSONResponse(window)

            # No open review: the honest empty state (WEB-STA-004).
            room_fields = ctx.project_service._db.projects.get_project_room_fields(
                project_id,
            )
            last_accepted_at = (room_fields or {}).get("last_review_at")

            # Source coverage: summarize configured sources
            source_coverage = None
            try:
                reviews = delta_svc._db.project_observations.list_reviews(
                    project_id, status="accepted", limit=1,
                )
                if reviews:
                    import json as _json
                    manifest_json = reviews[0].get("source_manifest_json", "{}")
                    if isinstance(manifest_json, str):
                        manifest = _json.loads(manifest_json)
                    else:
                        manifest = manifest_json
                    source_coverage = {
                        k: v.get("state", "unknown")
                        for k, v in manifest.items()
                    }
            except Exception:
                pass

            return JSONResponse({
                "open_review": None,
                "last_accepted_at": last_accepted_at,
                "source_coverage": source_coverage,
            })
        except NotFound as exc:
            return JSONResponse(
                {"code": exc.code, "message": exc.detail},
                status_code=404,
            )
        except Exception as exc:
            return error_500(exc, log, "Failed to get delta")

    # ── POST .../proposals/{proposal_id}/decide ─────────────────────

    @router.post("/{project_id}/reviews/{review_id}/proposals/{proposal_id}/decide")
    async def decide_proposal(
        project_id: str, review_id: str, proposal_id: str,
        request: Request,
    ) -> Any:
        try:
            body = await request.json()
            verb = body.get("verb", "")
            patch = body.get("patch")
            deferred_until = body.get("deferred_until")
            command_id = body.get("command_id")

            # Verify the proposal belongs to this review
            proposal = ctx.project_delta_service._db.project_observations.get_proposal(
                proposal_id,
            )
            if proposal is None:
                return JSONResponse(
                    {"code": "not_found",
                     "message": f"Proposal {proposal_id!r} not found"},
                    status_code=404,
                )
            if proposal.get("review_window_key") != review_id:
                return JSONResponse(
                    {"code": "not_found",
                     "message": (
                         f"Proposal {proposal_id!r} does not belong to "
                         f"review {review_id!r}"
                     )},
                    status_code=404,
                )

            result = ctx.project_delta_service.decide_proposal(
                principal(request),
                project_id,
                proposal_id,
                verb,
                patch=patch,
                deferred_until=deferred_until,
                command_id=command_id,
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
        except ConflictError as exc:
            return JSONResponse(
                {"code": exc.code, "message": exc.detail},
                status_code=409,
            )
        except Exception as exc:
            return error_500(exc, log, "Failed to decide proposal")

    # ── POST .../reviews/{review_id}/accept ─────────────────────────

    @router.post("/{project_id}/reviews/{review_id}/accept")
    async def accept_review(
        project_id: str, review_id: str, request: Request,
    ) -> Any:
        try:
            body = await request.json()
            command_id = body.get("command_id")

            result = ctx.project_delta_service.accept_review(
                principal(request),
                project_id,
                review_id,
                command_id=command_id,
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
        except ConflictError as exc:
            return JSONResponse(
                {"code": exc.code, "message": exc.detail},
                status_code=409,
            )
        except Exception as exc:
            return error_500(exc, log, "Failed to accept review")

    return router
