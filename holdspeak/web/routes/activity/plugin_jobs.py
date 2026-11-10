"""HTTP adapters for deferred plugin-job operations."""
from __future__ import annotations
from typing import Any, Optional
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from ....db import get_database, get_observer
from ....principals import UNAUTHENTICATED
from ....services.plugin_job_service import PluginJobService
from ....services.errors import ConflictError, NotFound
from ...context import WebContext
from ...runtime_support import error_500
from ....logging_config import get_logger
log=get_logger("web.routes.activity")
def _svc()->PluginJobService:return PluginJobService(get_database(), observer=get_observer())
def _principal(r:Request):return getattr(r.state,"principal",UNAUTHENTICATED)
def _err(e:Exception)->JSONResponse:return JSONResponse({"success":False,"error":"Plugin job not found" if isinstance(e,NotFound) else str(e)},status_code=404 if isinstance(e,NotFound) else 409)
def build_plugin_jobs_router(ctx:WebContext)->APIRouter:
 router=APIRouter()
 @router.get("/api/plugin-jobs")
 def list_jobs(request:Request,status:str="all",meeting_id:Optional[str]=None,limit:int=200)->Any:
  try:return JSONResponse(_svc().list(_principal(request),status,meeting_id,limit))
  except Exception as e:return error_500(e,log,"Failed to list deferred plugin jobs")
 @router.get("/api/plugin-jobs/summary")
 def summary(request:Request)->Any:
  try:return JSONResponse(_svc().summary(_principal(request)))
  except Exception as e:return error_500(e,log,"Failed to load deferred plugin-job summary")
 from .... import operations
 from ....system_operations import SYSTEM_OPERATIONS, system_service
 from ...operation_routes import operation_router
 from .._mount import mount_router
 from ..system.health import _answer
 mount_router(router, operation_router(
  [d for d in SYSTEM_OPERATIONS if d.name == "system.plugin_jobs.process"],
  lambda: operations.for_context(ctx, system_service=lambda: system_service(ctx)), _answer, module=__name__,
 ))
 @router.post("/api/plugin-jobs/{job_id}/retry-now")
 def retry(request:Request,job_id:int)->Any:
  try:return JSONResponse(_svc().retry(_principal(request),job_id))
  except (NotFound,ConflictError) as e:return _err(e)
  except Exception as e:log.error(f"Failed to retry deferred plugin job {job_id}: {e}");return JSONResponse({"success":False,"error":str(e)},status_code=500)
 return router
