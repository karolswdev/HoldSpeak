"""Decision lifecycle transport adapters (HS-123-04)."""
from __future__ import annotations
from typing import Any, Optional
from fastapi import APIRouter, Body, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool
from ... import db as hsdb
from ... import operations
from ...db import get_observer

def _database() -> Any:
    return getattr(hsdb, "get_database")()
from ...services.decision_lifecycle_service import DecisionLifecycleService
from ._mount import mount_router
from ...services.errors import ServiceError, NotFound
from ...principals import UNAUTHENTICATED


def _kernel_service() -> Any:
    from ...kernel.runtime import _service
    return _service()


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
    # HS-132-12: a refusal names WHAT — carry the service detail (e.g. which
    # successor to promote) instead of answering with the bare code.
    if exc.detail and exc.detail != payload.get("error"):
        payload.setdefault("detail", exc.detail)
    return JSONResponse(payload,status_code=int(payload.pop("status",400 if exc.code == "validation_error" else 409)))

async def _answer(fn: Any, *, status: int = 200) -> JSONResponse:
    """The envelope of the produced routes (``decision_operations.py``): the
    service errors as this router answers them; a ValueError (Commit of a
    decision not accepted, an unknown one) is a 409 in words."""
    try:
        return JSONResponse(await run_in_threadpool(fn), status_code=status)
    except ServiceError as exc:
        return _error(exc)
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=409)


def build_decisions_router(ctx: Any) -> APIRouter:
    # 2026-11-08 (one contract): the ledger and Commit are produced from their
    # declared rows, mounted before ``/{decision_id}`` so ``ledger`` is no id.
    from ...decision_operations import COMMIT_DECISION, DECISION_LEDGER, LIFECYCLE_OPERATIONS
    from ..operation_routes import operation_router
    outer=APIRouter()
    registry=lambda: operations.for_context(ctx, decision_lifecycle_service=service)  # noqa: E731
    router=APIRouter(prefix="/api/decisions",tags=["decisions"])
    # PHILO-5-01: this router is included BEFORE the primitives router
    # (web_server.py), so in the hub it answers GET /api/decisions and
    # GET /api/decisions/{id}. Its desk-decision branches are the contract's
    # decision.list / decision.read, bound to the hub's one PrimitiveService.
    def desk_ops() -> Any: return operations.for_context(ctx, "primitive_service")
    # HS-131-13: the route holds no engine and no `run_prompt` callable. Drafting
    # is the admitted Decision promotion child inside the service (HS-131-07);
    # a second route-side model seam would be a second, unadmitted Decision path.
    def service() -> DecisionLifecycleService: return DecisionLifecycleService(_database(), kernel=_kernel_service(), observer=get_observer())
    @router.get("")
    def list_decisions(request: Request,project_id: Optional[str]=None,project_key: Optional[str]=None,meeting_id: Optional[str]=None,lifecycle: Optional[str]=None,limit: int=200,offset: int=0) -> Any:
        # Every decision on the desk (PHILO-17) is ``decision.ledger``:
        # ``GET /api/decisions/ledger`` (decision_operations.py).
        if not any((project_id, project_key, meeting_id, lifecycle)):
            return JSONResponse({"decisions": desk_ops().invoke(_principal(request), "decision.list", {"limit": limit})})
        try: return JSONResponse(service().list_decisions(_principal(request),project_id=project_id,project_key=project_key,meeting_id=meeting_id,lifecycle=lifecycle,limit=limit,offset=offset))
        except ServiceError as exc: return _error(exc)
    @router.get("/{decision_id}")
    def get_decision(decision_id: str,request: Request) -> Any:
        # Probe the two durable owners before invoking either service.  The
        # probes are repository reads, so they do not create observer rows;
        # the selected service is then called exactly once.  A genuinely
        # missing id takes the desk path once so its real NotFound remains an
        # honest, observable cause instead of falling through to a second
        # observer failure from the lifecycle service.
        db = _database()
        legacy_only = (
            db.desk_decisions.get(decision_id) is None
            and db.decisions.get(decision_id) is not None
        )
        try:
            if legacy_only:
                return JSONResponse(registry().invoke(_principal(request), "decision.lineage", {"decision_id": decision_id}))
            return JSONResponse({"decision": desk_ops().invoke(_principal(request), "decision.read", {"decision_id": decision_id})})
        except ServiceError as exc:
            return _error(exc)
    @router.post("/{decision_id}/supersede")
    def supersede_decision(decision_id: str,request: Request,payload: Any=Body(default=None)) -> Any:
        # PHILO-7-02: this router answers the path in the hub (it is included
        # before the primitives router). A DESK decision's supersede is the
        # contract's admitted decision.supersede on the hub's one
        # PrimitiveService (one operation, one receipt, the desk_changed
        # frames); before, this branch wrote both rows by hand, outside the
        # contract and without a frame. A meeting decision keeps the lifecycle.
        # Round two (Astra finding 2): an id that names NO decision is the
        # desk operation's too, so its NotFound leaves the refusal receipt MCP
        # already left; a non-object body on a desk decision is refused with
        # its receipt (FastAPI answered 422 before, with none).
        db = _database()
        if db.desk_decisions.get(decision_id) is not None or db.decisions.get(decision_id) is None:
            desk = desk_ops()
            if payload is not None and not isinstance(payload, dict):
                kernel = desk.refuse(_principal(request), "decision.supersede", "invalid_arguments",
                                         {"decision_id": decision_id}) or {}
                return JSONResponse({"detail": [{"type": "dict_type", "loc": ["body"],
                                                 "msg": "Input should be a valid dictionary"}], **kernel},
                                    status_code=422)
            try:
                decision, kernel = desk.invoke_receipted(
                    _principal(request), "decision.supersede", {"decision_id": decision_id})
                return JSONResponse({"decision": decision, **(kernel or {})}, status_code=201)
            except NotFound as exc:
                return JSONResponse({"error": "decision_not_found", **(getattr(exc, "kernel", None) or {})}, status_code=404)
            except ServiceError as exc:
                return _error(exc)
        if payload is not None and not isinstance(payload, dict):
            return JSONResponse({"detail": [{"type": "dict_type", "loc": ["body"],
                                             "msg": "Input should be a valid dictionary"}]}, status_code=422)
        try:
            result=registry().invoke(_principal(request),"decision.meeting_supersede",{**(payload or {}),"decision_id":decision_id})
            return JSONResponse({k:v for k,v in result.items() if k != "_status"},status_code=result.get("_status",200))
        except ServiceError as exc: return _error(exc)
    # 2026-11-09: the meeting decision's moment, accept and promote verbs too
    # (decision_operations.LIFECYCLE_OPERATIONS; the rows without a route are
    # invoked by the two branching handlers below).
    mount_router(outer, operation_router((DECISION_LEDGER, COMMIT_DECISION, *LIFECYCLE_OPERATIONS), registry, _answer, module=__name__))
    mount_router(outer, router)
    return outer
