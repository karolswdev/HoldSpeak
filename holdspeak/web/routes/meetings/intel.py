"""Deferred-intelligence queue adapters."""
from __future__ import annotations
from typing import Any, Callable, Optional
from threading import Lock
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool
from .... import operations
from ....meeting_intel_operations import MEETING_INTEL_OPERATIONS, conflict_body, with_route
from ....logging_config import get_logger
from ....principals import UNAUTHENTICATED
from ....services.errors import ConflictError, NotFound, ValidationError
from ....services.meeting_intel_service import MeetingIntelService
from ....web_requests import _IntelProcessRequest
from ...context import WebContext
from ...operation_routes import operation_router
from ...runtime_support import error_500
from .._mount import mount_router
log = get_logger("web.routes.meetings")
_SERVICE_CACHE_LOCK = Lock()

def _principal(request: Request): return getattr(request.state, "principal", UNAUTHENTICATED)
def _svc(ctx: WebContext) -> MeetingIntelService:
    # PHILO-5-02 (gap C): the composed instance FIRST. The hub composes one
    # (with its runtime_queue notify); a factory is only a partial context's
    # stand-in (a route test), never a second instance beside the hub's.
    service = getattr(ctx, "meeting_intel_service", None)
    if isinstance(service, MeetingIntelService): return service
    factory = getattr(ctx, "meeting_intel_service_factory", None)
    if factory is not None: return factory()
    with _SERVICE_CACHE_LOCK:
        service = getattr(ctx, "meeting_intel_service", None)
        if isinstance(service, MeetingIntelService):
            return service
        from ....db import get_database, get_observer
        service = MeetingIntelService(get_database(), notify=lambda topic, value: ctx.broadcast(topic, value) if ctx.broadcast else None, observer=get_observer())  # _svc composition
        ctx.meeting_intel_service = service
        return service

async def _json_body(request: Request) -> dict[str, Any]:
    try:
        value = await request.json()
    except Exception:
        return {}
    return value if isinstance(value, dict) else {}

def _error(exc: Exception, action: str) -> JSONResponse:
    if isinstance(exc, operations.OperationOwnerRequired):
        return JSONResponse({"success": False, "error": exc.code}, status_code=403)
    if isinstance(exc, NotFound): return JSONResponse({"success": False, "error": "Meeting not found"}, status_code=404)
    if isinstance(exc, (ConflictError, ValidationError)): return JSONResponse({"success": False, "error": str(exc)}, status_code=400 if isinstance(exc, ValidationError) else 409)
    return error_500(exc, log, action)

def _conflict_response(service: MeetingIntelService, meeting_id: str, exc: ConflictError) -> JSONResponse:
    """Keep the route conflict contract identical across every run gesture (``meeting_intel_operations``)."""
    return JSONResponse(conflict_body(with_route(service, meeting_id, exc)), status_code=409)

#: The 500 words of each produced route; the run gestures answer a conflict with the route.
_FAILED = {"meeting.intel_summary": "Failed to load intel queue summary",
           "meeting.intel_process": "Failed to process intel jobs", "meeting.intel_jobs": "Failed to list intel jobs", "meeting.intel_retry": "Failed to retry intel job",
           "meeting.intel_recovery": "Failed to load Meeting intelligence recovery",
           "meeting.intel_recovery_retry": "Failed to retry Meeting intelligence",
           "meeting.intel_recovery_skip": "Failed to skip Meeting intelligence"}
_ROUTED = {"meeting.intel_retry", "meeting.intel_recovery_retry"}

def _answer(name: str) -> Callable[..., Any]:
    async def answer(fn: Callable[[], Any], *, status: int = 200) -> JSONResponse:
        try:
            return JSONResponse(await run_in_threadpool(fn), status_code=status)
        except ConflictError as exc:
            if name in _ROUTED:  # the call put the current route on it (with_route)
                return JSONResponse(conflict_body(exc), status_code=409)
            return _error(exc, _FAILED[name])
        except Exception as exc:
            return _error(exc, _FAILED[name])
    return answer

def build_intel_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()
    @router.post("/api/meetings/{meeting_id}/prepare")
    async def api_prepare_meeting_result(meeting_id: str, request: Request) -> Any:
        """Betterment capture C5b: Prepare… and Write again (one draft)."""
        try:
            body = await _json_body(request)
            result = await run_in_threadpool(
                operations.for_context(ctx, meeting_intel_service=lambda: _svc(ctx)).invoke,
                _principal(request), "meeting.result.prepare",
                {"meeting_id": meeting_id, "plugin_id": body.get("plugin_id"),
                 "expected_selection_hash": body.get("expected_selection_hash")},
            )
            return JSONResponse(result)
        except ConflictError as exc:
            return _conflict_response(_svc(ctx), meeting_id, exc)
        except Exception as exc:
            return _error(exc, "Failed to prepare the draft")
    @router.post("/api/meetings/{meeting_id}/intelligence/run")
    async def api_run_meeting_intelligence(meeting_id: str, request: Request) -> Any:
        """HS-170-04: enqueue a fresh intelligence job for a meeting.

        The face's Run intelligence verb. Returns {jobId, state, host}.
        409 with plainReason when the meeting has no transcript.
        """
        try:
            body = await _json_body(request)
            result = operations.for_context(ctx, meeting_intel_service=lambda: _svc(ctx)).invoke(
                _principal(request), "meeting.summary.run",
                {"meeting_id": meeting_id, "expected_selection_hash": body.get("expected_selection_hash")},
            )
            return JSONResponse(result)
        except ConflictError as exc:
            return _conflict_response(_svc(ctx), meeting_id, exc)
        except Exception as exc:
            return _error(exc, "Failed to run Meeting intelligence")

    registry = lambda: operations.for_context(ctx, meeting_intel_service=lambda: _svc(ctx))  # noqa: E731

    def process(descriptor: Any) -> Callable[..., Any]:
        async def api_process_intel_jobs(request: Request, payload: Optional[_IntelProcessRequest] = None) -> Any:
            args = payload.model_dump() if payload is not None else {}
            return await _answer(descriptor.name)(lambda: registry().invoke(_principal(request), descriptor.name, args))
        return api_process_intel_jobs

    def jobs(descriptor: Any) -> Callable[..., Any]:
        """Typed query parameters keep FastAPI's 422 for a malformed limit, as the hand-written route did."""
        async def api_list_intel_jobs(request: Request, status: str = "all", limit: int = 20, history_limit: int = 5) -> Any:
            args = {"status": status, "limit": limit, "history_limit": history_limit}
            return await _answer(descriptor.name)(lambda: registry().invoke(_principal(request), descriptor.name, args))
        return api_list_intel_jobs

    for descriptor in MEETING_INTEL_OPERATIONS:
        if descriptor.service == "meeting_intel_service":
            mount_router(router, operation_router([descriptor], registry, _answer(descriptor.name), module=__name__,
                                                  hand_written={"meeting.intel_jobs": jobs, "meeting.intel_process": process}))
    return router
