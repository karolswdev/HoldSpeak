"""HTTP adapters for activity project-rule operations."""
from __future__ import annotations
from typing import Any
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from ....db import get_database, get_observer
from ....principals import UNAUTHENTICATED
from ....services.activity_rules_service import ActivityRulesService
from ...context import WebContext
from ...runtime_support import error_500
from ....logging_config import get_logger
log=get_logger("web.routes.activity")
def _svc()->ActivityRulesService:return ActivityRulesService(get_database(), observer=get_observer())
def _principal(r:Request):return getattr(r.state,"principal",UNAUTHENTICATED)
def build_rules_router(ctx:WebContext)->APIRouter:
 router=APIRouter()
 @router.get("/api/activity/project-rules")
 def list_rules(request:Request,include_disabled:bool=True)->Any:
  try:return JSONResponse(_svc().list(_principal(request),include_disabled))
  except Exception as e:return error_500(e,log,"Failed to list activity project rules")
 @router.delete("/api/activity/project-rules/{rule_id}")
 def delete(request:Request,rule_id:str)->Any:
  try:return JSONResponse(_svc().delete(_principal(request),rule_id))
  except Exception as e:return error_500(e,log,"Failed to delete activity project rule")
 return router
