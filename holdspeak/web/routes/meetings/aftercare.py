"""Meeting aftercare and proposal adapters."""
from __future__ import annotations
from typing import Any, Optional
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from ....logging_config import get_logger
from ....principals import UNAUTHENTICATED
from ....services.errors import ConflictError, NotFound, ValidationError
from ....services.meeting_aftercare_service import MeetingAftercareService
from ....web_requests import _AftercareFileIssueRequest, _ProposalDecisionRequest, _SlackExportRequest
from ...context import WebContext
from ...runtime_support import error_500
log = get_logger("web.routes.meetings")
def _principal(request: Request): return getattr(request.state, "principal", UNAUTHENTICATED)
def _svc(ctx: WebContext) -> MeetingAftercareService:
    factory = getattr(ctx, "meeting_aftercare_service_factory", None)
    if factory is not None: return factory()
    service = getattr(ctx, "meeting_aftercare_service", None)
    if isinstance(service, MeetingAftercareService): return service
    from ....db import get_database, get_observer
    service = MeetingAftercareService(get_database(), notify=lambda topic, value: ctx.broadcast(topic, value) if ctx.broadcast else None, observer=get_observer())  # _svc composition
    ctx.meeting_aftercare_service = service
    return service
def _error(exc: Exception, action: str) -> JSONResponse:
    if isinstance(exc, NotFound): return JSONResponse({"error": "Meeting not found" if exc.kind == "meeting" else "Proposal not found" if exc.kind == "proposal" else "Action item not found", "success": False}, status_code=404)
    if isinstance(exc, ConflictError): return JSONResponse({"success": False, "error": str(exc)}, status_code=409)
    if isinstance(exc, ValidationError): return JSONResponse({"success": False, "error": str(exc)}, status_code=400)
    return error_500(exc, log, action)
def build_aftercare_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()
    @router.get("/api/meetings/{meeting_id}/aftercare")
    async def api_get_meeting_aftercare(meeting_id: str, request: Request) -> Any:
        try: return JSONResponse(_svc(ctx).get_aftercare(_principal(request), meeting_id))
        except Exception as exc: return _error(exc, "Failed to load meeting aftercare")
    @router.get("/api/meetings/{meeting_id}/followup-draft")
    async def api_get_meeting_followup_draft(meeting_id: str, request: Request) -> Any:
        try: return JSONResponse(_svc(ctx).get_followup_draft(_principal(request), meeting_id))
        except Exception as exc: return _error(exc, "Failed to build meeting follow-up draft")
    @router.get("/api/meetings/{meeting_id}/proposals")
    async def api_get_meeting_proposals(meeting_id: str, request: Request, status: Optional[str] = None) -> Any:
        try: return JSONResponse(_svc(ctx).list_proposals(_principal(request), meeting_id, status))
        except Exception as exc: return _error(exc, "Failed to load meeting proposals")
    @router.post("/api/meetings/{meeting_id}/proposals/{proposal_id}/decision")
    async def api_decide_meeting_proposal(meeting_id: str, proposal_id: str, payload: _ProposalDecisionRequest, request: Request) -> Any:
        try: return JSONResponse(_svc(ctx).decide_proposal(_principal(request), meeting_id, proposal_id, payload.model_dump()))
        except Exception as exc: return _error(exc, "Failed to decide meeting proposal")
    @router.post("/api/meetings/{meeting_id}/aftercare/file-issue")
    async def api_aftercare_file_issue(meeting_id: str, payload: _AftercareFileIssueRequest, request: Request) -> Any:
        try: return JSONResponse(_svc(ctx).file_issue(_principal(request), meeting_id, payload.model_dump()))
        except Exception as exc: return _error(exc, "Failed to file aftercare issue")
    @router.post("/api/meetings/{meeting_id}/export/slack")
    async def api_export_meeting_to_slack(meeting_id: str, payload: _SlackExportRequest, request: Request) -> Any:
        try: return JSONResponse(_svc(ctx).export_slack(_principal(request), meeting_id, payload.model_dump()))
        except Exception as exc: return _error(exc, "Failed to propose Slack export")
    return router
