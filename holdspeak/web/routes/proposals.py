"""HS-172-03: Follow-through proposal transport adapters.

Routes:
  GET  /api/meetings/{id}/follow-through-proposals - list proposals for a meeting
  GET  /api/meetings/{id}/outcome-review  - HS-200-12: the review face's projection
  GET  /api/projects/{id}/proposals       - list proposals for a project
  POST /api/proposals/{id}/confirm        - confirm a proposal (idempotent)
  POST /api/proposals/{id}/edit           - HS-200-12: amend a proposed row in place
  POST /api/meetings/{id}/proposals/accept-reviewed - HS-200-12: confirm the eligible rows
  POST /api/proposals/{id}/dismiss        - dismiss a proposal (idempotent)
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Body, Request
from fastapi.responses import JSONResponse

from ...logging_config import get_logger
from ...principals import UNAUTHENTICATED
from ...services.proposal_bridge_service import ProposalBridgeService
from ..context import WebContext
from ..runtime_support import error_500

log = get_logger("web.routes.proposals")


def _principal(request: Request):
    return getattr(request.state, "principal", UNAUTHENTICATED)


def _service(ctx: WebContext) -> ProposalBridgeService:
    service = getattr(ctx, "proposal_bridge_service", None)
    if service is not None:
        return service
    from ...db import get_database
    service = ProposalBridgeService(get_database())
    ctx.proposal_bridge_service = service  # type: ignore[attr-defined]
    return service


def _status(result: dict[str, Any]) -> int:
    """404 for a missing proposal; 409 for one already decided the other way."""
    return 409 if result.get("code") in {"confirmed", "dismissed", "meeting_deleted"} else 404


def build_proposal_router(ctx: WebContext) -> APIRouter:
    router = APIRouter(tags=["proposals"])

    @router.get("/api/meetings/{meeting_id}/follow-through-proposals")
    async def api_meeting_proposals(
        meeting_id: str,
        request: Request,
        state: Optional[str] = None,
    ) -> Any:
        try:
            proposals = _service(ctx).list_meeting_proposals(meeting_id, state=state)
            return JSONResponse({"meeting_id": meeting_id, "proposals": proposals})
        except Exception as exc:
            return error_500(exc, log, "Failed to list meeting proposals")

    @router.get("/api/meetings/{meeting_id}/outcome-review")
    async def api_meeting_outcome_review(meeting_id: str, request: Request) -> Any:
        try:
            review = _service(ctx).meeting_review(meeting_id)
            if "error" in review:
                return JSONResponse({"success": False, "error": review["error"]}, status_code=404)
            return JSONResponse(review)
        except Exception as exc:
            return error_500(exc, log, "Failed to read the meeting review")

    @router.post("/api/meetings/{meeting_id}/proposals/accept-reviewed")
    async def api_accept_reviewed(meeting_id: str, request: Request) -> Any:
        try:
            result = _service(ctx).accept_reviewed(_principal(request), meeting_id)
            if "error" in result:
                return JSONResponse({"success": False, **result}, status_code=404)
            return JSONResponse({"success": True, **result})
        except Exception as exc:
            return error_500(exc, log, "Failed to accept the reviewed proposals")

    @router.get("/api/projects/{project_id}/proposals")
    async def api_project_proposals(
        project_id: str,
        request: Request,
        state: Optional[str] = None,
    ) -> Any:
        try:
            proposals = _service(ctx).list_project_proposals(project_id, state=state)
            return JSONResponse({"project_id": project_id, "proposals": proposals})
        except Exception as exc:
            return error_500(exc, log, "Failed to list project proposals")

    @router.post("/api/proposals/{proposal_id}/confirm")
    async def api_confirm_proposal(
        proposal_id: str,
        request: Request,
        body: dict[str, Any] = Body(default={}),
    ) -> Any:
        try:
            result = _service(ctx).confirm_proposal(
                _principal(request),
                proposal_id,
                text=body.get("text"),
                owner=body.get("owner"),
                due=body.get("due"),
            )
            if "error" in result:
                return JSONResponse({"success": False, **result}, status_code=_status(result))
            return JSONResponse({"success": True, **result})
        except Exception as exc:
            return error_500(exc, log, "Failed to confirm proposal")

    @router.post("/api/proposals/{proposal_id}/edit")
    async def api_edit_proposal(
        proposal_id: str,
        request: Request,
        body: dict[str, Any] = Body(default={}),
    ) -> Any:
        """HS-200-12: edit in place (edit-then-confirm, ruling R5)."""
        try:
            result = _service(ctx).edit_proposal(
                _principal(request),
                proposal_id,
                text=body.get("text"),
                owner=body.get("owner"),
                due=body.get("due"),
            )
            if "error" in result:
                return JSONResponse({"success": False, **result}, status_code=_status(result))
            return JSONResponse(result)
        except Exception as exc:
            return error_500(exc, log, "Failed to edit proposal")

    @router.post("/api/proposals/{proposal_id}/dismiss")
    async def api_dismiss_proposal(
        proposal_id: str,
        request: Request,
    ) -> Any:
        try:
            result = _service(ctx).dismiss_proposal(_principal(request), proposal_id)
            if "error" in result:
                return JSONResponse({"success": False, **result}, status_code=_status(result))
            return JSONResponse({"success": True, **result})
        except Exception as exc:
            return error_500(exc, log, "Failed to dismiss proposal")

    return router
