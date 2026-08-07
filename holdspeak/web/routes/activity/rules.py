"""HTTP adapters for activity project-rule operations."""
from __future__ import annotations
from typing import Any, Optional
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from ....db import get_database, get_observer
from ....principals import UNAUTHENTICATED
from ....services.activity_rules_service import ActivityRulesService
from ....services.errors import NotFound, ValidationError
from ....web_requests import _ActivityProjectRuleRequest
from ...context import WebContext
from ...runtime_support import error_500
from ....logging_config import get_logger
log=get_logger("web.routes.activity")
def _svc()->ActivityRulesService:return ActivityRulesService(get_database(), observer=get_observer())
def _principal(r:Request):return getattr(r.state,"principal",UNAUTHENTICATED)
def _fields(model:Any)->dict[str,Any]:
 present=getattr(model,"model_fields_set",getattr(model,"__fields_set__",set()))
 return {key:getattr(model,key) for key in ("project_id","name","enabled","priority","match_type","pattern","entity_type") if key in present}
def _err(e:Exception)->JSONResponse:
 return JSONResponse({"error": "activity project rule not found" if isinstance(e,NotFound) else str(e)},status_code=404 if isinstance(e,NotFound) else 400)
def build_rules_router(ctx:WebContext)->APIRouter:
 router=APIRouter()
 @router.get("/api/activity/project-rules")
 async def list_rules(request:Request,include_disabled:bool=True)->Any:
  try:return JSONResponse(_svc().list(_principal(request),include_disabled))
  except Exception as e:return error_500(e,log,"Failed to list activity project rules")
 @router.post("/api/activity/project-rules")
 async def create(request:Request,payload:_ActivityProjectRuleRequest)->Any:
  try:return JSONResponse(_svc().create(_principal(request),payload.model_dump()))
  except ValidationError as e:return _err(e)
  except Exception as e:return error_500(e,log,"Failed to create activity project rule")
 @router.put("/api/activity/project-rules/{rule_id}")
 async def update(request:Request,rule_id:str,payload:_ActivityProjectRuleRequest)->Any:
  try:return JSONResponse(_svc().update(_principal(request),rule_id,_fields(payload)))
  except (NotFound,ValidationError) as e:return _err(e)
  except Exception as e:return error_500(e,log,"Failed to update activity project rule")
 @router.delete("/api/activity/project-rules/{rule_id}")
 async def delete(request:Request,rule_id:str)->Any:
  try:return JSONResponse(_svc().delete(_principal(request),rule_id))
  except Exception as e:return error_500(e,log,"Failed to delete activity project rule")
 @router.post("/api/activity/project-rules/preview")
 async def preview(request:Request,payload:_ActivityProjectRuleRequest)->Any:
  try:return JSONResponse(_svc().preview(_principal(request),payload.model_dump(),None))
  except ValidationError as e:return _err(e)
  except Exception as e:return error_500(e,log,"Failed to preview activity project rule")
 @router.post("/api/activity/project-rules/apply")
 async def apply(request:Request,limit:Optional[int]=None)->Any:
  try:return JSONResponse(_svc().apply(_principal(request),limit))
  except Exception as e:return error_500(e,log,"Failed to apply activity project rules")
 return router
