"""Ask transport adapters; orchestration belongs to :mod:`holdspeak.services.ask_service`."""
from __future__ import annotations
from typing import Any
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from .... import db as hsdb
from ....db import get_observer

def _database() -> Any:
    return getattr(hsdb, "get_database")()
from ....grounding_rails import hydrate_rails_refs
from ....services.ask_service import AskService
from ....services.errors import ServiceError
from ....principals import UNAUTHENTICATED
from ...context import WebContext
from ...runtime_support import error_500
from ._shared import _json_body, _run_frame
from ....logging_config import get_logger
log=get_logger("web.routes.primitives")

def _error(exc: ServiceError) -> JSONResponse:
    payload=dict(exc.context); payload.setdefault("error",exc.detail)
    if exc.code == "grounding_not_found": return JSONResponse(payload,status_code=400)
    return JSONResponse(payload,status_code=int(payload.pop("status", 400 if exc.code == "validation_error" else 409)))

def build_ask_router(ctx: WebContext) -> APIRouter:
    router=APIRouter()
    def service() -> AskService:
        from ..sync import _hub_model_name
        return AskService(_database(),hub_model=lambda: _hub_model_name(ctx),broadcast=lambda state, **frame: _run_frame(ctx,state,**frame),rails_hydrator=lambda refs,principal: hydrate_rails_refs(refs,principal=principal),observer=get_observer())
    @router.get("/api/models")
    async def api_list_models(request: Request) -> Any:
        try: return JSONResponse({"models":service().list_models(getattr(request.state, "principal", UNAUTHENTICATED))})
        except Exception as exc: return error_500(exc,log,"Failed to list models")
    @router.post("/api/grounding/resolve")
    async def api_resolve_grounding(request: Request) -> Any:
        body=await _json_body(request)
        if body is None: return JSONResponse({"error":"expected a JSON object"},status_code=400)
        try: return JSONResponse(service().resolve_grounding(getattr(request.state, "principal", UNAUTHENTICATED),body.get("refs") if isinstance(body.get("refs"),list) else []))
        except ServiceError as exc: return _error(exc)
        except Exception as exc: return error_500(exc,log,"Failed to resolve grounding")
    @router.post("/api/ask")
    async def api_ask(request: Request) -> Any:
        body=await _json_body(request)
        if body is None: return JSONResponse({"error":"expected a JSON object"},status_code=400)
        try:
            result=await service().ask(getattr(request.state, "principal", UNAUTHENTICATED),str(body.get("prompt") or ""),body.get("grounding"),lens=str(body.get("lens") or "Ask"),context=body.get("context") if isinstance(body.get("context"),list) else [],model=body.get("model"),inference_target_id=body.get("inference_target_id"),profile_id=body.get("profile_id"),max_tokens=body.get("max_tokens"),temperature=body.get("temperature"))
            return JSONResponse(result)
        except ServiceError as exc: return _error(exc)
        except Exception as exc: return error_500(exc,log,"Failed to run ask")
    @router.post("/api/ask/keep")
    async def api_ask_keep(request: Request) -> Any:
        body=await _json_body(request)
        if body is None: return JSONResponse({"error":"expected a JSON object"},status_code=400)
        try:
            result=service().keep(getattr(request.state, "principal", UNAUTHENTICATED),str(body.get("output") or ""),body.get("context") if isinstance(body.get("context"),list) else [],lens=str(body.get("lens") or "Ask"),prompt=str(body.get("prompt") or ""),grounding=body.get("grounding"))
            return JSONResponse(result,status_code=201)
        except ServiceError as exc: return _error(exc)
        except Exception as exc: return error_500(exc,log,"Failed to keep ask")
    return router
