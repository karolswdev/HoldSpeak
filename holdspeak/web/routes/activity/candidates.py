"""The activity meeting-candidate routes (2026-11-09: on ``holdspeak/activity_operations.py``).

The list is produced from its declared row. The start keeps a hand-written
route: it starts the live capture through the hub's callbacks
(``ctx.on_start``, ``ctx.on_update_meeting``, ``ctx.broadcast``), which no
declared call holds; its two service steps are the declared
``activity.meeting_candidate.get`` and ``activity.meeting_candidate.start``.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from .... import operations
from ....db import get_database, get_observer
from ....logging_config import get_logger
from ....principals import UNAUTHENTICATED
from ....services.activity_meeting_candidate_service import ActivityMeetingCandidateService
from ....services.errors import NotFound, ValidationError
from ...context import WebContext
from ...runtime_support import _meeting_callback_payload
from .._mount import mount_router
from .._produced import envelope, produced

log = get_logger("web.routes.activity")


def _bare() -> ActivityMeetingCandidateService:
    return ActivityMeetingCandidateService(get_database(), observer=get_observer())


def _principal(r: Request) -> Any:
    return getattr(r.state, "principal", UNAUTHENTICATED)


def _start_with_principal(on_start: Any, principal: Any) -> Any:
    # HS-131-08: capture start carries the authenticated caller, because live
    # meeting intelligence is admitted under exactly that principal.
    from ....services.meeting_service import _accepts_principal
    return on_start(principal=principal) if _accepts_principal(on_start) else on_start()


def _err(e: Exception) -> JSONResponse:
    found = isinstance(e, NotFound)
    return JSONResponse({"error": "activity meeting candidate not found" if found else str(e)},
                        status_code=404 if found else 400)


def build_candidates_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()
    rows = [op for op in operations.ACTIVITY_OPERATIONS if op.name == "activity.meeting_candidate.list"]
    mount_router(router, produced(
        ctx, rows, envelope(log, "Failed to list activity meeting candidates",
                            not_found=lambda exc: {"error": "activity meeting candidate not found"}),
        module=__name__, activity_meeting_candidate_service=_bare))

    def ops() -> operations.OperationRegistry:
        return operations.for_context(ctx, activity_meeting_candidate_service=_bare)

    @router.post("/api/activity/meeting-candidates/{candidate_id}/start")
    def start(request: Request, candidate_id: str) -> Any:
        if ctx.on_start is None:
            return JSONResponse({"success": False, "error": "Meeting start control not supported"}, status_code=501)
        who = _principal(request)
        try:
            candidate = ops().invoke(who, "activity.meeting_candidate.get", {"candidate_id": candidate_id})
            meeting = _meeting_callback_payload(_start_with_principal(ctx.on_start, who))
            warning = None
            if ctx.on_update_meeting is not None and str(candidate["title"] or "").strip():
                try:
                    updated = _meeting_callback_payload(ctx.on_update_meeting(title=candidate["title"], tags=None))
                    if updated is not None:
                        meeting = updated
                except Exception as e:
                    warning = str(e)
                    log.error(f"Failed to apply candidate title to started meeting: {e}")
            result = ops().invoke(who, "activity.meeting_candidate.start",
                                  {"candidate_id": candidate_id, "meeting": meeting, "warning": warning})
            if meeting is not None:
                ctx.broadcast("meeting_started", {
                    **meeting, "activity_meeting_candidate_id": result["candidate"]["id"],
                    "activity_meeting_candidate_title": result["candidate"]["title"],
                    "activity_meeting_candidate_url": result["candidate"]["meeting_url"]})
            return JSONResponse(result)
        except (NotFound, ValidationError) as e:
            return _err(e)
        except Exception as e:
            log.error(f"Failed to start activity meeting candidate: {e}")
            return JSONResponse({"success": False, "error": str(e)}, status_code=500)

    return router
