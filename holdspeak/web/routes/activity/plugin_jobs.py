"""HTTP adapters for deferred plugin-job operations."""
from __future__ import annotations
from typing import Any, Optional
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from ....db import get_database
from ....principals import UNAUTHENTICATED
from ....services.plugin_job_service import PluginJobService
from ....services.errors import ConflictError, NotFound
from ....web_requests import _PluginJobProcessRequest
from ...context import WebContext
from ...runtime_support import error_500
from ....logging_config import get_logger
log=get_logger("web.routes.activity")
def _svc()->PluginJobService:return PluginJobService(get_database())
def _principal(r:Request):return getattr(r.state,"principal",UNAUTHENTICATED)
def _err(e:Exception)->JSONResponse:return JSONResponse({"success":False,"error":"Plugin job not found" if isinstance(e,NotFound) else str(e)},status_code=404 if isinstance(e,NotFound) else 409)
def build_plugin_jobs_router(ctx:WebContext)->APIRouter:
 router=APIRouter()
 @router.get("/api/plugin-jobs")
 async def list_jobs(request:Request,status:str="all",meeting_id:Optional[str]=None,limit:int=200)->Any:
  try:return JSONResponse(_svc().list(_principal(request),status,meeting_id,limit))
  except Exception as e:return error_500(e,log,"Failed to list deferred plugin jobs")
 @router.get("/api/plugin-jobs/summary")
 async def summary(request:Request)->Any:
  try:return JSONResponse(_svc().summary(_principal(request)))
  except Exception as e:return error_500(e,log,"Failed to load deferred plugin-job summary")
 @router.post("/api/plugin-jobs/process")
 async def process(payload:Optional[_PluginJobProcessRequest]=None)->Any:
  if ctx.on_process_plugin_jobs is None:return JSONResponse({"success":False,"error":"Deferred plugin queue processing not supported"},status_code=501)
  max_jobs=payload.max_jobs if payload else None
  if max_jobs is not None and int(max_jobs)<=0:return JSONResponse({"success":False,"error":"max_jobs must be greater than 0"},status_code=400)
  mode=(payload.mode if payload else None) or "respect_backoff";mode=str(mode).strip().lower()
  if mode not in {"respect_backoff","retry_now"}:return JSONResponse({"success":False,"error":"mode must be respect_backoff or retry_now"},status_code=400)
  try:
   data=ctx.on_process_plugin_jobs(max_jobs=max_jobs,include_scheduled=mode=="retry_now"); out=dict(data) if isinstance(data,dict) else {"processed":int(data)};out.update(mode=mode,success=True);ctx.broadcast("plugin_jobs_processed",out);return JSONResponse(out)
  except Exception as e:log.error(f"Failed to process deferred plugin jobs: {e}");return JSONResponse({"success":False,"error":str(e)},status_code=500)
 @router.post("/api/plugin-jobs/{job_id}/retry-now")
 async def retry(request:Request,job_id:int)->Any:
  try:return JSONResponse(_svc().retry(_principal(request),job_id))
  except (NotFound,ConflictError) as e:return _err(e)
  except Exception as e:log.error(f"Failed to retry deferred plugin job {job_id}: {e}");return JSONResponse({"success":False,"error":str(e)},status_code=500)
 @router.post("/api/plugin-jobs/{job_id}/cancel")
 async def cancel(request:Request,job_id:int)->Any:
  try:return JSONResponse(_svc().cancel(_principal(request),job_id))
  except (NotFound,ConflictError) as e:return _err(e)
  except Exception as e:log.error(f"Failed to cancel deferred plugin job {job_id}: {e}");return JSONResponse({"success":False,"error":str(e)},status_code=500)
 return router
