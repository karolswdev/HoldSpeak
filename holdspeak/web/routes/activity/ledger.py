"""HTTP adapters for the transport-neutral activity ledger service."""
from __future__ import annotations
from typing import Any, Optional
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from ....db import get_database, get_observer
from ....principals import UNAUTHENTICATED
from ....services.activity_ledger_service import ActivityLedgerService
from ....services.errors import ValidationError
from ....web_requests import _ActivityDomainRuleRequest, _ActivitySettingsRequest
from ...context import WebContext
from ...runtime_support import error_500
from ....logging_config import get_logger
log = get_logger("web.routes.activity")
def _principal(request: Request): return getattr(request.state, "principal", UNAUTHENTICATED)
def _svc() -> ActivityLedgerService: return ActivityLedgerService(get_database(), observer=get_observer())
def build_ledger_router(ctx: WebContext) -> APIRouter:
 router=APIRouter()
 @router.get("/api/activity/status")
 async def status(request: Request)->Any:
  try:return JSONResponse(_svc().status(_principal(request)))
  except Exception as e:return error_500(e,log,"Failed to read activity status")
 @router.get("/api/activity/records")
 async def records(request:Request,project_id:Optional[str]=None,domain:Optional[str]=None,entity_type:Optional[str]=None,limit:int=100)->Any:
  try:return JSONResponse(_svc().list_records(_principal(request),project_id,domain,entity_type,limit))
  except Exception as e:return error_500(e,log,"Failed to read activity records")
 @router.post("/api/activity/refresh")
 async def refresh(request:Request)->Any:
  try:return JSONResponse(_svc().refresh(_principal(request)))
  except Exception as e:return error_500(e,log,"Failed to refresh activity")
 @router.put("/api/activity/settings")
 async def settings(request:Request,payload:_ActivitySettingsRequest)->Any:
  try:return JSONResponse(_svc().update_settings(_principal(request),payload.model_dump()))
  except Exception as e:return error_500(e,log,"Failed to update activity settings")
 @router.post("/api/activity/domains")
 async def domain(request:Request,payload:_ActivityDomainRuleRequest)->Any:
  try:return JSONResponse(_svc().upsert_domain_rule(_principal(request),payload.domain,payload.action))
  except ValidationError as e:return JSONResponse({"error":str(e)},status_code=400)
  except Exception as e:return error_500(e,log,"Failed to update activity domain rule")
 @router.delete("/api/activity/domains/{domain}")
 async def delete_domain(request:Request,domain:str)->Any:
  try:return JSONResponse(_svc().delete_domain_rule(_principal(request),domain))
  except Exception as e:return error_500(e,log,"Failed to delete activity domain rule")
 @router.delete("/api/activity/records")
 async def delete_records(request:Request,domain:Optional[str]=None,project_id:Optional[str]=None)->Any:
  try:return JSONResponse(_svc().delete_records(_principal(request),domain,project_id))
  except Exception as e:return error_500(e,log,"Failed to delete activity records")
 return router
