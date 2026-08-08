"""HTTP adapters for transport-neutral activity enrichment operations."""
from __future__ import annotations
from typing import Any, Optional
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from ....db import get_database, get_observer
from ....principals import UNAUTHENTICATED
from ....services.activity_enrichment_service import ActivityEnrichmentService
from ....services.errors import NotFound, ServiceError, ValidationError
from ....web_requests import _ActivityCliEnrichmentRunRequest, _ActivityEnrichmentConnectorRequest, _ActivityExtensionEventsRequest
from ...context import WebContext
from ...runtime_support import error_500
from ....logging_config import get_logger
log=get_logger("web.routes.activity")
def _svc()->ActivityEnrichmentService:return ActivityEnrichmentService(get_database(), observer=get_observer())
def _principal(r:Request):return getattr(r.state,"principal",UNAUTHENTICATED)
def _payload(p:Any)->dict[str,Any]:return p.model_dump() if p is not None else {}
def _err(e:ServiceError, *, github:bool=False)->JSONResponse:
 if e.code=="forbidden": return JSONResponse({"success":False,"error":str(e),**e.context},status_code=403)
 return JSONResponse({"error":str(e)},status_code=404 if isinstance(e,NotFound) else 400)
def build_enrichment_router(ctx:WebContext)->APIRouter:
 router=APIRouter()
 @router.get("/api/activity/enrichment/connectors")
 async def connectors(request:Request)->Any:
  try:return JSONResponse(_svc().list_connectors(_principal(request)))
  except Exception as e:return error_500(e,log,"Failed to list activity enrichment connectors")
 @router.put("/api/activity/enrichment/connectors/{connector_id}")
 async def update_connector(request:Request,connector_id:str,payload:_ActivityEnrichmentConnectorRequest)->Any:
  try:return JSONResponse(_svc().update_connector(_principal(request),connector_id,_payload(payload)))
  except ServiceError as e:return _err(e)
  except Exception as e:return error_500(e,log,"Failed to update activity enrichment connector")
 @router.post("/api/activity/extension/events")
 async def ingest(request:Request,payload:_ActivityExtensionEventsRequest)->Any:
  try:return JSONResponse(_svc().ingest_extension_events(_principal(request),payload.events))
  except ServiceError as e:return _err(e)
  except Exception as e:return error_500(e,log,"Failed to ingest activity extension events")
 @router.get("/api/activity/enrichment/connectors/{connector_id}/dry-run")
 async def dry_run(request:Request,connector_id:str,limit:int=25)->Any:
  try:return JSONResponse(_svc().dry_run(_principal(request),connector_id,limit))
  except ServiceError as e:return _err(e)
  except Exception as e:return error_500(e,log,"Failed to dry-run activity enrichment connector")
 @router.delete("/api/activity/enrichment/connectors/{connector_id}/annotations")
 async def clear_annotations(request:Request,connector_id:str)->Any:
  try:return JSONResponse(_svc().clear_annotations(_principal(request),connector_id))
  except ServiceError as e:return _err(e)
  except Exception as e:return error_500(e,log,"Failed to clear activity enrichment annotations")
 @router.delete("/api/activity/enrichment/connectors/{connector_id}/candidates")
 async def clear_candidates(request:Request,connector_id:str)->Any:
  try:return JSONResponse(_svc().clear_candidates(_principal(request),connector_id))
  except ServiceError as e:return _err(e)
  except Exception as e:return error_500(e,log,"Failed to clear activity enrichment candidates")
 @router.get("/api/activity/annotations")
 async def annotations(request:Request,source_connector_id:Optional[str]=None,annotation_type:Optional[str]=None,activity_record_id:Optional[int]=None,limit:int=100)->Any:
  try:return JSONResponse(_svc().list_annotations(_principal(request),source_connector_id,annotation_type,activity_record_id,limit))
  except Exception as e:return error_500(e,log,"Failed to list activity annotations")
 @router.get("/api/activity/briefing")
 async def briefing(request:Request)->Any:
  try:return JSONResponse(_svc().briefing(_principal(request)))
  except Exception as e:return error_500(e,log,"Failed to fetch activity briefing")
 @router.post("/api/activity/enrichment/pipelines/{pipeline_id}/run")
 async def pipeline(request:Request,pipeline_id:str)->Any:
  try:return JSONResponse(_svc().run_pipeline(_principal(request),pipeline_id))
  except ServiceError as e:return _err(e)
  except Exception as e:return error_500(e,log,f"Failed to run pipeline {pipeline_id}")
 @router.get("/api/activity/enrichment/connectors/{connector_id}/runs")
 async def runs(request:Request,connector_id:str,limit:int=10)->Any:
  try:return JSONResponse(_svc().list_runs(_principal(request),connector_id,limit))
  except ServiceError as e:return _err(e)
  except Exception as e:return error_500(e,log,"Failed to list connector runs")
 @router.get("/api/activity/enrichment/github/preview")
 async def github_preview(request:Request,limit:int=50)->Any:
  try:return JSONResponse(_svc().preview_github(_principal(request),limit))
  except Exception as e:return error_500(e,log,"Failed to preview GitHub activity enrichment")
 @router.post("/api/activity/enrichment/github/run")
 async def github_run(request:Request,payload:Optional[_ActivityCliEnrichmentRunRequest]=None)->Any:
  try:return JSONResponse(_svc().run_github(_principal(request),_payload(payload)))
  except ServiceError as e:return _err(e)
  except ValueError as e:return JSONResponse({"success":False,"error":str(e)},status_code=400)
  except Exception as e:log.error(f"Failed to run GitHub activity enrichment: {e}");return JSONResponse({"success":False,"error":str(e)},status_code=500)
 @router.get("/api/activity/enrichment/jira/preview")
 async def jira_preview(request:Request,limit:int=50)->Any:
  try:return JSONResponse(_svc().preview_jira(_principal(request),limit))
  except Exception as e:return error_500(e,log,"Failed to preview Jira activity enrichment")
 @router.post("/api/activity/enrichment/jira/run")
 async def jira_run(request:Request,payload:Optional[_ActivityCliEnrichmentRunRequest]=None)->Any:
  try:return JSONResponse(_svc().run_jira(_principal(request),_payload(payload)))
  except ServiceError as e:return _err(e)
  except ValueError as e:return JSONResponse({"success":False,"error":str(e)},status_code=400)
  except Exception as e:log.error(f"Failed to run Jira activity enrichment: {e}");return JSONResponse({"success":False,"error":str(e)},status_code=500)
 return router
