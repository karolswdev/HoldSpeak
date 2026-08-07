"""HTTP adapters for activity nudge operations."""
from __future__ import annotations
from typing import Any, Optional
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from ....db import get_database
from ....principals import UNAUTHENTICATED
from ....services.activity_nudge_service import ActivityNudgeService
from ....services.errors import ValidationError
from ...context import WebContext
from ...runtime_support import error_500
from ....logging_config import get_logger
log=get_logger("web.routes.activity.nudges")
def _svc()->ActivityNudgeService:return ActivityNudgeService(get_database())
def _principal(r:Request):return getattr(r.state,"principal",UNAUTHENTICATED)
def build_nudges_router(ctx:WebContext)->APIRouter:
 router=APIRouter()
 @router.get("/api/activity/nudges")
 async def list_nudges(request:Request,project_id:Optional[str]=None,limit:int=3)->Any:
  try:return JSONResponse(_svc().list(_principal(request),project_id,limit))
  except Exception as e:return error_500(e,log,"Failed to compute activity nudges")
 @router.post("/api/activity/nudges/{nudge_id}/dismiss")
 async def dismiss(request:Request,nudge_id:str)->Any:
  try:return JSONResponse(_svc().dismiss(_principal(request),nudge_id))
  except ValidationError as e:return JSONResponse({"error":str(e)},status_code=400)
  except Exception as e:return error_500(e,log,"Failed to dismiss activity nudge")
 @router.post("/api/activity/nudges/select")
 async def select(request:Request,payload:dict[str,Any])->Any:
  try:return JSONResponse(_svc().select(_principal(request),payload.get("record_id") if isinstance(payload,dict) else None))
  except ValidationError as e:return JSONResponse({"error":str(e)},status_code=400)
  except Exception as e:return error_500(e,log,"Failed to select activity record for dictation")
 @router.post("/api/activity/nudges/select/clear")
 async def clear()->Any:
  try:
   from ....dictation_selection import clear_selected_record
   clear_selected_record();return JSONResponse({"cleared":True})
  except Exception as e:return error_500(e,log,"Failed to clear activity selection")
 return router
