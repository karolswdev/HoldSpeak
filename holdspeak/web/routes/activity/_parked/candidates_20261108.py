"""PARKED 20261108 (subtraction day, Lane R): routes no client reads.

Parked from ``holdspeak/web/routes/activity/candidates.py``: GET /api/activity/meeting-candidates/preview, PUT /api/activity/meeting-candidates/{candidate_id}/status.
Not imported. Kept for history; restore with ``git revert`` of the parking commit.
"""
from __future__ import annotations
"""HTTP adapters for activity meeting candidates."""
from typing import Any
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from .....db import get_database, get_observer
from .....principals import UNAUTHENTICATED
from .....services.activity_meeting_candidate_service import ActivityMeetingCandidateService
from .....services.errors import NotFound, ValidationError
from .....web_requests import _ActivityMeetingCandidateStatusRequest
from ....context import WebContext
from ....runtime_support import error_500
from .....logging_config import get_logger
log=get_logger("web.routes.activity")
def _svc()->ActivityMeetingCandidateService:return ActivityMeetingCandidateService(get_database(), observer=get_observer())
def _principal(r:Request):return getattr(r.state,"principal",UNAUTHENTICATED)
def _start_with_principal(on_start:Any,principal:Any)->Any:
 # HS-131-08: capture start carries the authenticated caller, because live
 # meeting intelligence is admitted under exactly that principal.
 from .....services.meeting_service import _accepts_principal
 return on_start(principal=principal) if _accepts_principal(on_start) else on_start()
def _err(e:Exception)->JSONResponse:return JSONResponse({"error":"activity meeting candidate not found" if isinstance(e,NotFound) else str(e)},status_code=404 if isinstance(e,NotFound) else 400)
def parked_build_candidates_router(ctx:WebContext)->APIRouter:
 router=APIRouter()
 @router.get("/api/activity/meeting-candidates/preview")
 def preview(request:Request,limit:int=50)->Any:
  try:return JSONResponse(_svc().preview(_principal(request),limit))
  except Exception as e:return error_500(e,log,"Failed to preview activity meeting candidates")
 @router.put("/api/activity/meeting-candidates/{candidate_id}/status")
 def update(request:Request,candidate_id:str,payload:_ActivityMeetingCandidateStatusRequest)->Any:
  try:return JSONResponse(_svc().update_status(_principal(request),candidate_id,payload.status))
  except (NotFound,ValidationError) as e:return _err(e)
  except Exception as e:return error_500(e,log,"Failed to update activity meeting candidate")
 return router
