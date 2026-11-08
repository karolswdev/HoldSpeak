"""Sequence CRUD (the iPad syncs crews; the run routes are parked, 2026-11-08)."""
from __future__ import annotations
from typing import Any
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from ....principals import Principal, PrincipalKind
from ....services.errors import NotFound, ValidationError
from ....services.primitive_service import PrimitiveService
from ...context import WebContext
from ._shared import _json_body


def build_chains_router(ctx: WebContext) -> APIRouter:
    router=APIRouter()
    def _principal(request: Request) -> Any: return getattr(request.state,"principal",Principal(PrincipalKind.OWNER,"owner-session"))
    def _svc() -> PrimitiveService:
        # HS-200-45: the hub's ONE composed instance (on_changed -> the bus).
        if getattr(ctx, "primitive_service", None) is not None:
            return ctx.primitive_service
        from ....db import get_database,get_observer
        return PrimitiveService(get_database(),observer=get_observer())
    @router.get("/api/chains")
    def list_(request:Request): return JSONResponse({"chains":_svc().list_chains(_principal(request))})
    @router.post("/api/chains")
    async def create(request:Request):
        body=await _json_body(request)
        if body is None:return JSONResponse({"error":"expected a JSON object"},status_code=400)
        try:return JSONResponse({"chain":_svc().create_chain(_principal(request),chain_id=str(body.get("id") or "") or None,name=str(body.get("name") or ""),steps=list(body.get("steps") or []))},status_code=201)
        except (ValidationError,ValueError) as exc:return JSONResponse({"error":str(exc)},status_code=400)
    @router.get("/api/chains/{chain_id}")
    def get_(chain_id:str,request:Request):
        try:return JSONResponse({"chain":_svc().get_chain(_principal(request),chain_id)})
        except NotFound:return JSONResponse({"error":f"Unknown Sequence: {chain_id}"},status_code=404)
    @router.put("/api/chains/{chain_id}")
    async def update(chain_id:str,request:Request):
        body=await _json_body(request)
        if body is None:return JSONResponse({"error":"expected a JSON object"},status_code=400)
        try:return JSONResponse({"chain":_svc().update_chain(_principal(request),chain_id,name=body.get("name"),steps=body.get("steps"))})
        except NotFound:return JSONResponse({"error":f"Unknown Sequence: {chain_id}"},status_code=404)
    @router.delete("/api/chains/{chain_id}")
    def delete(chain_id:str,request:Request):
        try:_svc().delete_chain(_principal(request),chain_id);return JSONResponse({"success":True})
        except NotFound:return JSONResponse({"error":f"Unknown Sequence: {chain_id}"},status_code=404)
    return router
