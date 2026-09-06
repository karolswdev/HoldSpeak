"""Deferred-intelligence queue adapters."""
from __future__ import annotations
from typing import Any, Optional
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from ....logging_config import get_logger
from ....principals import UNAUTHENTICATED
from ....services.errors import ConflictError, NotFound, ValidationError
from ....services.meeting_intel_service import MeetingIntelService
from ....web_requests import _IntelProcessRequest
from ...context import WebContext
from ...runtime_support import error_500
log = get_logger("web.routes.meetings")

def _principal(request: Request): return getattr(request.state, "principal", UNAUTHENTICATED)
def _svc(ctx: WebContext) -> MeetingIntelService:
    factory = getattr(ctx, "meeting_intel_service_factory", None)
    if factory is not None: return factory()
    service = getattr(ctx, "meeting_intel_service", None)
    if isinstance(service, MeetingIntelService): return service
    from ....db import get_database, get_observer
    service = MeetingIntelService(get_database(), notify=lambda topic, value: ctx.broadcast(topic, value) if ctx.broadcast else None, observer=get_observer())  # _svc composition
    ctx.meeting_intel_service = service
    return service

def _error(exc: Exception, action: str) -> JSONResponse:
    if isinstance(exc, NotFound): return JSONResponse({"success": False, "error": "Meeting not found"}, status_code=404)
    if isinstance(exc, (ConflictError, ValidationError)): return JSONResponse({"success": False, "error": str(exc)}, status_code=400 if isinstance(exc, ValidationError) else 409)
    return error_500(exc, log, action)

def build_intel_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()
    @router.get("/api/intel/jobs")
    async def api_list_intel_jobs(request: Request, status: str = "all", limit: int = 20, history_limit: int = 5) -> Any:
        try: return JSONResponse(_svc(ctx).list_jobs(_principal(request), {"status": status, "limit": limit, "history_limit": history_limit}))
        except Exception as exc: return _error(exc, "Failed to list intel jobs")
    @router.get("/api/intel/summary")
    async def api_intel_queue_summary(request: Request) -> Any:
        try: return JSONResponse(_svc(ctx).queue_summary(_principal(request)))
        except Exception as exc: return _error(exc, "Failed to load intel queue summary")
    @router.post("/api/intel/process")
    async def api_process_intel_jobs(request: Request, payload: Optional[_IntelProcessRequest] = None) -> Any:
        try:
            body = payload.model_dump() if payload is not None else {}
            return JSONResponse(_svc(ctx).process_jobs(_principal(request), body))
        except Exception as exc: return _error(exc, "Failed to process intel jobs")
    @router.post("/api/intel/retry/{meeting_id}")
    async def api_retry_intel_job(meeting_id: str, request: Request) -> Any:
        try: return JSONResponse(_svc(ctx).retry_job(_principal(request), meeting_id))
        except Exception as exc: return _error(exc, "Failed to retry intel job")
    @router.post("/api/meetings/{meeting_id}/intelligence/run")
    async def api_run_meeting_intelligence(meeting_id: str, request: Request) -> Any:
        """HS-170-04: enqueue a fresh intelligence job for a meeting.

        The face's Run intelligence verb. Returns {jobId, state, host}.
        409 with plainReason when the meeting has no transcript.
        """
        try:
            result = _svc(ctx).run_intelligence(_principal(request), meeting_id)
            return JSONResponse(result)
        except ConflictError as exc:
            return JSONResponse({"plainReason": str(exc)}, status_code=409)
        except Exception as exc:
            return _error(exc, "Failed to run Meeting intelligence")

    @router.get("/api/meetings/{meeting_id}/intel-recovery")
    async def api_get_meeting_intel_recovery(meeting_id: str, request: Request) -> Any:
        try: return JSONResponse(_svc(ctx).get_recovery(_principal(request), meeting_id))
        except Exception as exc: return _error(exc, "Failed to load Meeting intelligence recovery")
    @router.post("/api/meetings/{meeting_id}/intel-recovery/retry")
    async def api_retry_meeting_intel_recovery(meeting_id: str, request: Request) -> Any:
        try: return JSONResponse(_svc(ctx).retry_recovery(_principal(request), meeting_id))
        except Exception as exc: return _error(exc, "Failed to retry Meeting intelligence")
    @router.post("/api/meetings/{meeting_id}/intel-recovery/skip")
    async def api_skip_meeting_intel_recovery(meeting_id: str, request: Request) -> Any:
        try: return JSONResponse(_svc(ctx).skip_recovery(_principal(request), meeting_id))
        except Exception as exc: return _error(exc, "Failed to skip Meeting intelligence")
    return router
