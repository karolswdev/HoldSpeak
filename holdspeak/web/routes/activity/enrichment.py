"""HTTP adapters for transport-neutral activity enrichment operations."""
from __future__ import annotations
from typing import Any
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from ....db import get_database, get_observer
from ....principals import UNAUTHENTICATED
from ....services.activity_enrichment_service import ActivityEnrichmentService
from ....services.errors import NotFound, ServiceError
from ....web_requests import _ActivityExtensionEventsRequest
from ...context import WebContext
from ...runtime_support import error_500
from ....logging_config import get_logger
log=get_logger("web.routes.activity")
def _svc()->ActivityEnrichmentService:return ActivityEnrichmentService(get_database(), observer=get_observer())
def _principal(r:Request):return getattr(r.state,"principal",UNAUTHENTICATED)
def _err(e:ServiceError, *, github:bool=False)->JSONResponse:
 if e.code=="forbidden": return JSONResponse({"success":False,"error":str(e),**e.context},status_code=403)
 return JSONResponse({"error":str(e)},status_code=404 if isinstance(e,NotFound) else 400)
def build_enrichment_router(ctx:WebContext)->APIRouter:
 router=APIRouter()
 @router.get("/api/activity/enrichment/connectors")
 def connectors(request:Request)->Any:
  try:return JSONResponse(_svc().list_connectors(_principal(request)))
  except Exception as e:return error_500(e,log,"Failed to list activity enrichment connectors")
 @router.post("/api/activity/extension/events")
 def ingest(request:Request,payload:_ActivityExtensionEventsRequest)->Any:
  try:return JSONResponse(_svc().ingest_extension_events(_principal(request),payload.events))
  except ServiceError as e:return _err(e)
  except Exception as e:return error_500(e,log,"Failed to ingest activity extension events")
 @router.get("/api/activity/enrichment/connectors/{connector_id}/dry-run")
 def dry_run(request:Request,connector_id:str,limit:int=25)->Any:
  try:return JSONResponse(_svc().dry_run(_principal(request),connector_id,limit))
  except ServiceError as e:return _err(e)
  except Exception as e:return error_500(e,log,"Failed to dry-run activity enrichment connector")
 @router.get("/api/activity/briefing")
 def briefing(request:Request)->Any:
  try:return JSONResponse(_svc().briefing(_principal(request)))
  except Exception as e:return error_500(e,log,"Failed to fetch activity briefing")
 return router
