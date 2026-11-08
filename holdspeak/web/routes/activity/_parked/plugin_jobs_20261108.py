"""PARKED 20261108 (subtraction day, Lane R): routes no client reads.

Parked from ``holdspeak/web/routes/activity/plugin_jobs.py``: POST /api/plugin-jobs/{job_id}/cancel.
Not imported. Kept for history; restore with ``git revert`` of the parking commit.
"""
from __future__ import annotations
"""HTTP adapters for deferred plugin-job operations."""
from typing import Any
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from .....db import get_database, get_observer
from .....principals import UNAUTHENTICATED
from .....services.plugin_job_service import PluginJobService
from .....services.errors import ConflictError, NotFound
from ....context import WebContext
from .....logging_config import get_logger
log=get_logger("web.routes.activity")
def _svc()->PluginJobService:return PluginJobService(get_database(), observer=get_observer())
def _principal(r:Request):return getattr(r.state,"principal",UNAUTHENTICATED)
def _err(e:Exception)->JSONResponse:return JSONResponse({"success":False,"error":"Plugin job not found" if isinstance(e,NotFound) else str(e)},status_code=404 if isinstance(e,NotFound) else 409)
def parked_build_plugin_jobs_router(ctx:WebContext)->APIRouter:
 router=APIRouter()
 @router.post("/api/plugin-jobs/{job_id}/cancel")
 def cancel(request:Request,job_id:int)->Any:
  try:return JSONResponse(_svc().cancel(_principal(request),job_id))
  except (NotFound,ConflictError) as e:return _err(e)
  except Exception as e:log.error(f"Failed to cancel deferred plugin job {job_id}: {e}");return JSONResponse({"success":False,"error":str(e)},status_code=500)
 return router
