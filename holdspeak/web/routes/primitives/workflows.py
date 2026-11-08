"""Workflow CRUD (the iPad syncs workflows; the run routes are parked, 2026-11-08)."""
from __future__ import annotations
from typing import Any
from fastapi import APIRouter,Request
from fastapi.responses import JSONResponse
from ....principals import Principal,PrincipalKind
from ....services.errors import NotFound,ValidationError
from ....services.primitive_service import PrimitiveService
from ...context import WebContext
from ._shared import _json_body

def build_workflows_router(ctx:WebContext)->APIRouter:
 router=APIRouter()
 def p(request:Request)->Any:return getattr(request.state,"principal",Principal(PrincipalKind.OWNER,"owner-session"))
 def svc()->PrimitiveService:
  # HS-200-45: the hub's ONE composed instance (on_changed -> the bus).
  if getattr(ctx,"primitive_service",None) is not None: return ctx.primitive_service
  from ....db import get_database,get_observer
  return PrimitiveService(get_database(),observer=get_observer())
 @router.get("/api/workflows")
 def list_(request:Request):return JSONResponse({"workflows":svc().list_workflows(p(request))})
 @router.post("/api/workflows")
 async def create(request:Request):
  body=await _json_body(request)
  if body is None:return JSONResponse({"error":"expected a JSON object"},status_code=400)
  try:return JSONResponse({"workflow":svc().create_workflow(p(request),workflow_id=str(body.get("id") or "") or None,name=str(body.get("name") or ""),prompt=str(body.get("prompt") or ""),graph_json=dict(body.get("graph_json") or {}))},status_code=201)
  except (ValidationError,ValueError) as exc:return JSONResponse({"error":str(exc)},status_code=400)
 @router.get("/api/workflows/{workflow_id}")
 def get_(workflow_id:str,request:Request):
  try:return JSONResponse({"workflow":svc().get_workflow(p(request),workflow_id)})
  except NotFound:return JSONResponse({"error":f"Unknown workflow: {workflow_id}"},status_code=404)
 @router.put("/api/workflows/{workflow_id}")
 async def update(workflow_id:str,request:Request):
  body=await _json_body(request)
  if body is None:return JSONResponse({"error":"expected a JSON object"},status_code=400)
  try:return JSONResponse({"workflow":svc().update_workflow(p(request),workflow_id,name=body.get("name"),prompt=body.get("prompt"),graph_json=body.get("graph_json"))})
  except NotFound:return JSONResponse({"error":f"Unknown workflow: {workflow_id}"},status_code=404)
 @router.delete("/api/workflows/{workflow_id}")
 def delete(workflow_id:str,request:Request):
  try:svc().delete_workflow(p(request),workflow_id);return JSONResponse({"success":True})
  except NotFound:return JSONResponse({"error":f"Unknown workflow: {workflow_id}"},status_code=404)
 return router
