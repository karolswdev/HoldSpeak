"""Sequence CRUD and admitted native-run routes."""
from __future__ import annotations
from typing import Any
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from ....logging_config import get_logger
from ....principals import Principal, PrincipalKind
from ....services.errors import NotFound, ValidationError, ServiceError
from ....services.primitive_service import PrimitiveService
from ....services.sequence_workflow_service import SequenceWorkflowService
from ...context import WebContext
from ...runtime_support import error_500
from ._shared import _json_body, _run_frame
log = get_logger("web.routes.primitives")


def build_chains_router(ctx: WebContext) -> APIRouter:
    router=APIRouter()
    def _principal(request: Request) -> Any: return getattr(request.state,"principal",Principal(PrincipalKind.OWNER,"owner-session"))
    def _svc() -> PrimitiveService:
        from ....db import get_database,get_observer
        return PrimitiveService(get_database(),observer=get_observer())
    @router.get("/api/chains")
    async def list_(request:Request): return JSONResponse({"chains":_svc().list_chains(_principal(request))})
    @router.post("/api/chains")
    async def create(request:Request):
        body=await _json_body(request)
        if body is None:return JSONResponse({"error":"expected a JSON object"},status_code=400)
        try:return JSONResponse({"chain":_svc().create_chain(_principal(request),chain_id=str(body.get("id") or "") or None,name=str(body.get("name") or ""),steps=list(body.get("steps") or []))},status_code=201)
        except (ValidationError,ValueError) as exc:return JSONResponse({"error":str(exc)},status_code=400)
    @router.get("/api/chains/{chain_id}")
    async def get_(chain_id:str,request:Request):
        try:return JSONResponse({"chain":_svc().get_chain(_principal(request),chain_id)})
        except NotFound:return JSONResponse({"error":f"Unknown Sequence: {chain_id}"},status_code=404)
    @router.put("/api/chains/{chain_id}")
    async def update(chain_id:str,request:Request):
        body=await _json_body(request)
        if body is None:return JSONResponse({"error":"expected a JSON object"},status_code=400)
        try:return JSONResponse({"chain":_svc().update_chain(_principal(request),chain_id,name=body.get("name"),steps=body.get("steps"))})
        except NotFound:return JSONResponse({"error":f"Unknown Sequence: {chain_id}"},status_code=404)
    @router.delete("/api/chains/{chain_id}")
    async def delete(chain_id:str,request:Request):
        try:_svc().delete_chain(_principal(request),chain_id);return JSONResponse({"success":True})
        except NotFound:return JSONResponse({"error":f"Unknown Sequence: {chain_id}"},status_code=404)
    @router.post("/api/chains/{chain_id}/run")
    async def run(chain_id:str,request:Request):
        body=await _json_body(request) or {}; principal=_principal(request)
        if principal is None or principal.kind is PrincipalKind.NONE:return JSONResponse({"error":"principal authentication required"},status_code=401)
        try:
            from ....db import get_database
            from ....kernel.runtime import _configure
            db=get_database()
            chain=db.chains.get(chain_id)
            name=(chain.name if chain else "") or chain_id
            _run_frame(ctx,"running",kind="chain",ref=chain_id,name=name)
            try:
                result=await SequenceWorkflowService(db,_configure(db)).run_sequence(principal,chain_id,body)
            except ServiceError:
                _run_frame(ctx,"error",kind="chain",ref=chain_id,name=name,error="failed")
                raise
            _run_frame(ctx,"ready",kind="chain",ref=chain_id,name=name)
            return JSONResponse(result)
        except ServiceError as exc:return JSONResponse({"error":str(exc),**dict(exc.context or {})},status_code=int((exc.context or {}).get("status",500)))
        except Exception as exc:return error_500(exc,log,"Failed to run chain")
    @router.post("/api/chains/runs/{parent_operation_id}/cancel")
    async def cancel(parent_operation_id:str,request:Request):
        principal=_principal(request)
        try:
            from ....db import get_database
            from ....kernel.runtime import _configure
            broker=_configure(get_database())
            disposition=broker.parent_run_controller.cancel_by_operation_id(principal,parent_operation_id)
            return JSONResponse({"parent_operation_id":parent_operation_id,"disposition":disposition})
        except Exception as exc:return error_500(exc,log,"Failed to cancel chain")
    return router
