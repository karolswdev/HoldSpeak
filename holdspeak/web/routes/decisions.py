"""Decision lifecycle transport adapters (HS-123-04)."""
from __future__ import annotations
from typing import Any, Optional
from fastapi import APIRouter, Body, Request
from fastapi.responses import JSONResponse
from ... import db as hsdb
from ...db import get_observer

def _database() -> Any:
    return getattr(hsdb, "get_database")()
from ...services.decision_lifecycle_service import DecisionLifecycleService
from ...services.errors import ServiceError, NotFound
from ...principals import UNAUTHENTICATED


def _kernel_service() -> Any:
    from ...kernel.runtime import _service
    return _service()


async def _generate_with_model(db: Any, target: Any, prompt: str) -> tuple[str, Any]:
    from ...inference_targets import build_intel_for_target
    intel = build_intel_for_target(target, db)
    output = await __import__("asyncio").to_thread(
        intel.run_prompt,
        system_prompt="Draft one concise artifact from the accepted decision. Preserve the decision's meaning. Return Markdown only and do not invent approval.",
        user_prompt=prompt, max_tokens=1200,
    )
    return str(output or "").strip(), intel


def _principal(request: Request) -> Any:
    return getattr(request.state, "principal", UNAUTHENTICATED)

def _error(exc: ServiceError) -> JSONResponse:
    payload=dict(exc.context)
    if isinstance(exc,NotFound):
        if exc.kind == "decision": payload={"error":"decision_not_found"}
        elif exc.kind == "decision_moment": payload={"error":"decision_moment_unavailable","decision_id":exc.id}
        else: payload={"error":exc.code}
        return JSONResponse(payload,status_code=404)
    payload.setdefault("error",exc.code if exc.code != "validation_error" else exc.detail)
    return JSONResponse(payload,status_code=int(payload.pop("status",400 if exc.code == "validation_error" else 409)))

def build_decisions_router(ctx: Any) -> APIRouter:
    del ctx
    router=APIRouter(prefix="/api/decisions",tags=["decisions"])
    def service() -> DecisionLifecycleService: return DecisionLifecycleService(_database(), kernel=_kernel_service(), model_generator=_generate_with_model, observer=get_observer())
    @router.get("")
    async def list_decisions(request: Request,project_id: Optional[str]=None,project_key: Optional[str]=None,meeting_id: Optional[str]=None,lifecycle: Optional[str]=None,limit: int=200,offset: int=0) -> Any:
        try: return JSONResponse(service().list_decisions(_principal(request),project_id=project_id,project_key=project_key,meeting_id=meeting_id,lifecycle=lifecycle,limit=limit,offset=offset))
        except ServiceError as exc: return _error(exc)
    @router.get("/{decision_id}")
    async def get_decision(decision_id: str,request: Request) -> Any:
        try: return JSONResponse(service().get_decision(_principal(request),decision_id))
        except ServiceError as exc: return _error(exc)
    @router.get("/{decision_id}/moment")
    async def get_decision_moment(decision_id: str,request: Request) -> Any:
        try: return JSONResponse(service().get_moment(_principal(request),decision_id))
        except ServiceError as exc: return _error(exc)
    @router.post("/{decision_id}/accept")
    async def accept_decision(decision_id: str,request: Request) -> Any:
        try: return JSONResponse(service().transition(_principal(request),decision_id,"accept",{}))
        except ServiceError as exc: return _error(exc)
    @router.post("/{decision_id}/reject")
    async def reject_decision(decision_id: str,request: Request) -> Any:
        try: return JSONResponse(service().transition(_principal(request),decision_id,"reject",{}))
        except ServiceError as exc: return _error(exc)
    @router.post("/{decision_id}/supersede")
    async def supersede_decision(decision_id: str,request: Request,payload: dict[str,Any]=Body(default={})) -> Any:
        try:
            result=service().supersede(_principal(request),decision_id,payload)
            return JSONResponse({k:v for k,v in result.items() if k != "_status"},status_code=result.get("_status",200))
        except ServiceError as exc: return _error(exc)
    @router.post("/{decision_id}/promote/{artifact_type}")
    async def promote_decision(decision_id: str,artifact_type: str,request: Request) -> Any:
        try: return JSONResponse(service().promote(_principal(request),decision_id,artifact_type,{}))
        except ServiceError as exc: return _error(exc)
    @router.post("/{decision_id}/promote/{artifact_type}/draft-with-model")
    async def draft_promoted_decision_with_model(decision_id: str,artifact_type: str,request: Request,payload: dict[str,Any]=Body(default={})) -> Any:
        try: return JSONResponse(await service().draft_promoted_with_model(_principal(request),decision_id,artifact_type,payload))
        except ServiceError as exc: return _error(exc)
    return router
