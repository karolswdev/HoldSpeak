"""Workflow CRUD and admitted native-run routes."""
from __future__ import annotations
from typing import Any
from fastapi import APIRouter,Request
from fastapi.responses import JSONResponse
from ....logging_config import get_logger
from ....principals import Principal,PrincipalKind
from ....services.errors import NotFound,ValidationError,ServiceError
from ....services.primitive_service import PrimitiveService
from ....services.sequence_workflow_service import SequenceWorkflowService
from ...context import WebContext
from ...runtime_support import error_500
from ._shared import _json_body,_run_frame
log=get_logger("web.routes.primitives")

def build_workflows_router(ctx:WebContext)->APIRouter:
 router=APIRouter()
 def p(request:Request)->Any:return getattr(request.state,"principal",Principal(PrincipalKind.OWNER,"owner-session"))
 def svc()->PrimitiveService:
  from ....db import get_database,get_observer
  return PrimitiveService(get_database(),observer=get_observer())
 @router.get("/api/workflows")
 async def list_(request:Request):return JSONResponse({"workflows":svc().list_workflows(p(request))})
 @router.post("/api/workflows")
 async def create(request:Request):
  body=await _json_body(request)
  if body is None:return JSONResponse({"error":"expected a JSON object"},status_code=400)
  try:return JSONResponse({"workflow":svc().create_workflow(p(request),workflow_id=str(body.get("id") or "") or None,name=str(body.get("name") or ""),prompt=str(body.get("prompt") or ""),graph_json=dict(body.get("graph_json") or {}))},status_code=201)
  except (ValidationError,ValueError) as exc:return JSONResponse({"error":str(exc)},status_code=400)
 @router.get("/api/workflows/{workflow_id}")
 async def get_(workflow_id:str,request:Request):
  try:return JSONResponse({"workflow":svc().get_workflow(p(request),workflow_id)})
  except NotFound:return JSONResponse({"error":f"Unknown workflow: {workflow_id}"},status_code=404)
 @router.put("/api/workflows/{workflow_id}")
 async def update(workflow_id:str,request:Request):
  body=await _json_body(request)
  if body is None:return JSONResponse({"error":"expected a JSON object"},status_code=400)
  try:return JSONResponse({"workflow":svc().update_workflow(p(request),workflow_id,name=body.get("name"),prompt=body.get("prompt"),graph_json=body.get("graph_json"))})
  except NotFound:return JSONResponse({"error":f"Unknown workflow: {workflow_id}"},status_code=404)
 @router.delete("/api/workflows/{workflow_id}")
 async def delete(workflow_id:str,request:Request):
  try:svc().delete_workflow(p(request),workflow_id);return JSONResponse({"success":True})
  except NotFound:return JSONResponse({"error":f"Unknown workflow: {workflow_id}"},status_code=404)
 @router.post("/api/workflows/{workflow_id}/run")
 async def run(workflow_id:str,request:Request):
  body=await _json_body(request) or {}; principal=p(request)
  if principal is None or principal.kind is PrincipalKind.NONE:return JSONResponse({"error":"principal authentication required"},status_code=401)
  try:
   from ....db import get_database
   from ....kernel.runtime import _configure
   db=get_database()
   workflow=db.workflows.get(workflow_id)
   name=(workflow.name if workflow else "") or workflow_id
   _run_frame(ctx,"running",kind="workflow",ref=workflow_id,name=name)
   try:
    result=await SequenceWorkflowService(db,_configure(db)).run_workflow(principal,workflow_id,body)
   except ServiceError:
    _run_frame(ctx,"error",kind="workflow",ref=workflow_id,name=name,error="failed")
    raise
   _run_frame(ctx,"ready",kind="workflow",ref=workflow_id,name=name)
   return JSONResponse(result)
  except ServiceError as exc:return JSONResponse({"error":str(exc),**dict(exc.context or {})},status_code=int((exc.context or {}).get("status",500)))
  except Exception as exc:return error_500(exc,log,"Failed to run workflow")
 @router.post("/api/workflows/runs/{parent_operation_id}/cancel")
 async def cancel(parent_operation_id:str,request:Request):
  try:
   from ....db import get_database
   from ....kernel.runtime import _configure
   db=get_database(); broker=_configure(db)
   disposition=broker.parent_run_controller.cancel_by_operation_id(p(request),parent_operation_id)
   return JSONResponse({"parent_operation_id":parent_operation_id,"disposition":disposition})
  except Exception as exc:return error_500(exc,log,"Failed to cancel workflow")
 return router
