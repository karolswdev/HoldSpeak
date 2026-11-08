"""PARKED 20261108 (subtraction day, Lane R): routes no client reads.

Parked from ``holdspeak/web/routes/activity/rules.py``: POST /api/activity/project-rules/apply.
Not imported. Kept for history; restore with ``git revert`` of the parking commit.
"""
from __future__ import annotations
"""HTTP adapters for activity project-rule operations."""
from typing import Any, Optional
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from .....db import get_database, get_observer
from .....principals import UNAUTHENTICATED
from .....services.activity_rules_service import ActivityRulesService
from .....services.errors import NotFound
from ....context import WebContext
from ....runtime_support import error_500
from .....logging_config import get_logger
log=get_logger("web.routes.activity")
def _svc()->ActivityRulesService:return ActivityRulesService(get_database(), observer=get_observer())
def _principal(r:Request):return getattr(r.state,"principal",UNAUTHENTICATED)
def _fields(model:Any)->dict[str,Any]:
 present=getattr(model,"model_fields_set",getattr(model,"__fields_set__",set()))
 return {key:getattr(model,key) for key in ("project_id","name","enabled","priority","match_type","pattern","entity_type") if key in present}
def _err(e:Exception)->JSONResponse:
 return JSONResponse({"error": "activity project rule not found" if isinstance(e,NotFound) else str(e)},status_code=404 if isinstance(e,NotFound) else 400)
def parked_build_rules_router(ctx:WebContext)->APIRouter:
 router=APIRouter()
 @router.post("/api/activity/project-rules/apply")
 def apply(request:Request,limit:Optional[int]=None)->Any:
  try:return JSONResponse(_svc().apply(_principal(request),limit))
  except Exception as e:return error_500(e,log,"Failed to apply activity project rules")
 return router
