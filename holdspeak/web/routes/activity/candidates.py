"""HTTP adapters for activity meeting candidates."""
from __future__ import annotations
from typing import Any, Optional
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from ....db import get_database, get_observer
from ....principals import UNAUTHENTICATED
from ....services.activity_meeting_candidate_service import ActivityMeetingCandidateService
from ....services.errors import NotFound, ValidationError
from ....web_requests import _ActivityMeetingCandidateRequest, _ActivityMeetingCandidateStatusRequest
from ...context import WebContext
from ...runtime_support import _meeting_callback_payload, error_500
from ....logging_config import get_logger
log=get_logger("web.routes.activity")
def _svc()->ActivityMeetingCandidateService:return ActivityMeetingCandidateService(get_database(), observer=get_observer())
def _principal(r:Request):return getattr(r.state,"principal",UNAUTHENTICATED)
def _err(e:Exception)->JSONResponse:return JSONResponse({"error":"activity meeting candidate not found" if isinstance(e,NotFound) else str(e)},status_code=404 if isinstance(e,NotFound) else 400)
def build_candidates_router(ctx:WebContext)->APIRouter:
 router=APIRouter()
 @router.get("/api/activity/meeting-candidates/preview")
 async def preview(request:Request,limit:int=50)->Any:
  try:return JSONResponse(_svc().preview(_principal(request),limit))
  except Exception as e:return error_500(e,log,"Failed to preview activity meeting candidates")
 @router.get("/api/activity/meeting-candidates")
 async def list_candidates(request:Request,source_connector_id:Optional[str]=None,status:Optional[str]=None,limit:int=100)->Any:
  try:return JSONResponse(_svc().list(_principal(request),source_connector_id,status,limit))
  except ValidationError as e:return _err(e)
  except Exception as e:return error_500(e,log,"Failed to list activity meeting candidates")
 @router.post("/api/activity/meeting-candidates")
 async def create(request:Request,payload:_ActivityMeetingCandidateRequest)->Any:
  try:return JSONResponse(_svc().create(_principal(request),payload.model_dump()))
  except ValidationError as e:return _err(e)
  except Exception as e:return error_500(e,log,"Failed to create activity meeting candidate")
 @router.put("/api/activity/meeting-candidates/{candidate_id}/status")
 async def update(request:Request,candidate_id:str,payload:_ActivityMeetingCandidateStatusRequest)->Any:
  try:return JSONResponse(_svc().update_status(_principal(request),candidate_id,payload.status))
  except (NotFound,ValidationError) as e:return _err(e)
  except Exception as e:return error_500(e,log,"Failed to update activity meeting candidate")
 @router.post("/api/activity/meeting-candidates/{candidate_id}/start")
 async def start(request:Request,candidate_id:str)->Any:
  if ctx.on_start is None:return JSONResponse({"success":False,"error":"Meeting start control not supported"},status_code=501)
  try:
   candidate=_svc().candidate_for_start(_principal(request),candidate_id)
   meeting=_meeting_callback_payload(ctx.on_start()); warning=None
   if ctx.on_update_meeting is not None and str(candidate["title"] or "").strip():
    try:
     updated=_meeting_callback_payload(ctx.on_update_meeting(title=candidate["title"],tags=None))
     if updated is not None:meeting=updated
    except Exception as e: warning=str(e);log.error(f"Failed to apply candidate title to started meeting: {e}")
   result=_svc().start(_principal(request),candidate_id,meeting,warning)
   if meeting is not None:ctx.broadcast("meeting_started",{**meeting,"activity_meeting_candidate_id":result["candidate"]["id"],"activity_meeting_candidate_title":result["candidate"]["title"],"activity_meeting_candidate_url":result["candidate"]["meeting_url"]})
   return JSONResponse(result)
  except NotFound as e:return _err(e)
  except ValidationError as e:return _err(e)
  except Exception as e:log.error(f"Failed to start activity meeting candidate: {e}");return JSONResponse({"success":False,"error":str(e)},status_code=500)
 @router.delete("/api/activity/meeting-candidates")
 async def delete(request:Request,source_connector_id:Optional[str]=None,status:Optional[str]=None)->Any:
  try:return JSONResponse(_svc().delete(_principal(request),source_connector_id,status))
  except ValidationError as e:return _err(e)
  except Exception as e:return error_500(e,log,"Failed to delete activity meeting candidates")
 return router
