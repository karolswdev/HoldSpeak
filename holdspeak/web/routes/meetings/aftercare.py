"""Meeting aftercare and proposal adapters."""
from __future__ import annotations
from typing import Any, Callable
from threading import Lock
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool
from .... import operations
from ....meeting_intel_operations import MEETING_INTEL_OPERATIONS
from ....logging_config import get_logger
from ....principals import UNAUTHENTICATED
from ....services.errors import ConflictError, NotFound, ValidationError
from ....services.meeting_aftercare_service import MeetingAftercareService
from ....web_requests import _AftercareFileIssueRequest, _ProposalDecisionRequest
from ...context import WebContext
from ...operation_routes import operation_router
from ...runtime_support import error_500
from .._mount import mount_router
log = get_logger("web.routes.meetings")
_SERVICE_CACHE_LOCK = Lock()
def _principal(request: Request): return getattr(request.state, "principal", UNAUTHENTICATED)
def _svc(ctx: WebContext) -> MeetingAftercareService:
    factory = getattr(ctx, "meeting_aftercare_service_factory", None)
    if factory is not None: return factory()
    service = getattr(ctx, "meeting_aftercare_service", None)
    if isinstance(service, MeetingAftercareService): return service
    with _SERVICE_CACHE_LOCK:
        service = getattr(ctx, "meeting_aftercare_service", None)
        if isinstance(service, MeetingAftercareService):
            return service
        from ....db import get_database, get_observer
        service = MeetingAftercareService(get_database(), notify=lambda topic, value: ctx.broadcast(topic, value) if ctx.broadcast else None, observer=get_observer())  # _svc composition
        ctx.meeting_aftercare_service = service
        return service
def _error(exc: Exception, action: str) -> JSONResponse:
    if isinstance(exc, operations.OperationOwnerRequired):
        return JSONResponse({"success": False, "error": exc.code}, status_code=403)
    if isinstance(exc, NotFound): return JSONResponse({"error": "Meeting not found" if exc.kind == "meeting" else "Proposal not found" if exc.kind == "proposal" else "Action item not found", "success": False}, status_code=404)
    if isinstance(exc, ConflictError): return JSONResponse({"success": False, "error": str(exc)}, status_code=409)
    if isinstance(exc, ValidationError): return JSONResponse({"success": False, "error": str(exc)}, status_code=400)
    return error_500(exc, log, action)
#: The 500 words of each produced route.
_FAILED = {"meeting.followup_draft": "Failed to build meeting follow-up draft",
           "meeting.aftercare_file_issue": "Failed to file aftercare issue", "meeting.aftercare": "Failed to load meeting aftercare", "meeting.aftercare_proposals": "Failed to load meeting proposals",
           "meeting.aftercare_decide": "Failed to decide meeting proposal"}
def _answer(name: str) -> Callable[..., Any]:
    async def answer(fn: Callable[[], Any], *, status: int = 200) -> JSONResponse:
        try: return JSONResponse(await run_in_threadpool(fn), status_code=status)
        except Exception as exc: return _error(exc, _FAILED.get(name, "Slack export is parked"))
    return answer
def build_aftercare_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()
    registry = lambda: operations.for_context(ctx, meeting_aftercare_service=lambda: _svc(ctx))  # noqa: E731

    def file_issue(descriptor: Any) -> Callable[..., Any]:
        async def api_aftercare_file_issue(meeting_id: str, payload: _AftercareFileIssueRequest, request: Request) -> Any:
            args = {**payload.model_dump(), "meeting_id": meeting_id}
            return await _answer(descriptor.name)(
                lambda: registry().invoke(_principal(request), descriptor.name, args, shape="web"))
        return api_aftercare_file_issue

    def decide(descriptor: Any) -> Callable[..., Any]:
        """The body model keeps FastAPI's 422 for a malformed decision, as the hand-written route did."""
        async def api_decide_meeting_proposal(meeting_id: str, proposal_id: str, payload: _ProposalDecisionRequest,
                                              request: Request) -> Any:
            args = {**payload.model_dump(), "meeting_id": meeting_id, "proposal_id": proposal_id}
            return await _answer(descriptor.name)(
                lambda: registry().invoke(_principal(request), descriptor.name, args, shape="web"))
        return api_decide_meeting_proposal

    def slack_export(descriptor: Any) -> Any:
        async def api_export_meeting_to_slack(meeting_id: str, request: Request) -> Any:
            return await _answer(descriptor.name)(lambda: registry().invoke(
                _principal(request), descriptor.name, {"meeting_id": meeting_id}))
        return api_export_meeting_to_slack

    from ....parity_operations import PARITY_OPERATIONS
    for descriptor in (*MEETING_INTEL_OPERATIONS, *PARITY_OPERATIONS):
        if descriptor.service == "meeting_aftercare_service":
            mount_router(router, operation_router([descriptor], registry, _answer(descriptor.name), module=__name__,
                                                  hand_written={"meeting.slack_export": slack_export, "meeting.aftercare_decide": decide, "meeting.aftercare_file_issue": file_issue}))
    return router
