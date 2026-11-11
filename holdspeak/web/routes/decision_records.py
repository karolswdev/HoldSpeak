"""Decision record transport adapters for the Desk Intelligence pullout.

A decision record is the mutable governing document for a decision (HS-127-01);
"Receipt" is reserved for immutable kernel evidence (Constitution Art. XI).
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from ... import operations
from ...db import get_database, get_observer
from ...logging_config import get_logger
from ...principals import PrincipalKind, UNAUTHENTICATED
from ...services.brief_carry import RightRequired
from ...decision_operations import RECORD_OPERATIONS
from ...services.decision_record_service import DecisionRecordService
from ...services.errors import NotFound, ServiceError
from ...web.runtime_support import error_500
from ..operation_routes import ContractRefusal
from ._mount import mount_router
from ._produced import produced
from .primitives._shared import _kernel_fields, _refusal_kernel

log = get_logger("web.routes.decision_records")


async def _answer(fn: Any, *, status: int = 200) -> JSONResponse:
    """The produced routes' envelope: Carry's refusals as the hand-written
    handler answered them (403 the right, 404 an unknown record, 409 a record
    that is not current); the reads' errors through the shared envelope."""
    try:
        return JSONResponse(await run_in_threadpool(fn), status_code=status)
    except RightRequired as exc:
        return JSONResponse(exc.response, status_code=403)
    except NotFound as exc:
        if exc.kind == "decision_record":
            return JSONResponse({"detail": f"decision record not found: {exc.id!r}"}, status_code=404)
        return JSONResponse({"error": exc.detail, "error_code": exc.code}, status_code=404)
    except ContractRefusal as exc:
        return JSONResponse({"error": exc.detail, "code": exc.code}, status_code=400)
    except ServiceError as exc:
        status = int(exc.context.get("status") or (404 if isinstance(exc, NotFound) else 400))
        return JSONResponse({"error": exc.detail, "error_code": exc.code}, status_code=status)
    except ValueError as exc:
        return JSONResponse({"detail": str(exc)}, status_code=409)
    except Exception as exc:
        return error_500(exc, log, "Failed to read decision records")


def build_decision_records_router(ctx: Any) -> APIRouter:
    """Expose durable decision records through the web API."""
    router = APIRouter(prefix="/api/decision-records", tags=["decision-records"])

    def service() -> DecisionRecordService:
        return DecisionRecordService(get_database(), observer=get_observer())

    def principal(request: Request) -> Any:
        return getattr(request.state, "principal", UNAUTHENTICATED)

    # Declare search before the parameterized path so FastAPI does not regard
    # "search" as a record ID.
    @router.get("/search")
    def search_records(
        request: Request, q: str = "", limit: int = 50
    ) -> list[dict[str, Any]]:
        return service().search(principal(request), q, limit=limit)

    def create_from_desk(request: Request, body: dict[str, Any] = Body(default={})) -> Any:
        registry = operations.for_context(ctx, "primitive_service", decision_record_service=service)
        who = principal(request)
        try:
            status, result = registry.invoke(who, "decision_record.create_desk_command", {"body": body},
                                            held={"registry_factory": lambda: registry})
            return JSONResponse(result, status_code=status)
        except operations.OperationRefused as exc:
            kernel = registry.refuse(who, "decision.create", exc.code, body) or {}
            return JSONResponse({"error": str(exc), **kernel}, status_code=400)
        except operations.OperationOwnerRequired as exc:
            if who.kind is PrincipalKind.NONE:
                return JSONResponse({"error": "decision.create is admitted under Article XI and needs the transport's authenticated principal"}, status_code=400)
            return JSONResponse({"error": exc.code, "detail": exc.detail}, status_code=403)
        except ServiceError as exc:
            return JSONResponse({"error": exc.code, "detail": exc.detail, **exc.context},
                                status_code=int(exc.context.get("status") or 409))
        except ValueError as exc:
            return JSONResponse({"error": str(exc), **_refusal_kernel(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to create canonical decision")

    @router.get("/work/{work_type}/{work_ref}")
    def records_for_work(
        work_type: str, work_ref: str, request: Request
    ) -> list[dict[str, Any]]:
        return service().records_for_work(principal(request), work_type, work_ref)

    @router.get("/{record_id}")
    def get_record(record_id: str, request: Request) -> dict[str, Any]:
        record = service().get(principal(request), record_id)
        if record is None:
            raise HTTPException(status_code=404, detail="decision record not found")
        return record

    # 2026-11-09 (ops/projects): the review list, the records of one source and
    # Carry are produced from their declared rows (decision_operations.py),
    # mounted before ``/{record_id}`` so ``review`` is no id. The ledger list
    # (``GET /api/decision-records``) had no web caller: parked; MCP keeps
    # decision_record.list.
    outer = APIRouter()
    from ...parity_operations import PARITY_OPERATIONS
    from ..operation_routes import operation_router
    mount_router(outer, operation_router(
        [d for d in PARITY_OPERATIONS if d.name == "decision_record.create_desk_command"], lambda: None, _answer,
        module=__name__, hand_written={"decision_record.create_desk_command": lambda d: create_from_desk}))
    mount_router(outer, produced(
        ctx, RECORD_OPERATIONS, _answer, module=__name__,
        decision_record_service=lambda: DecisionRecordService(get_database(), observer=get_observer()),
    ))
    mount_router(outer, router)
    return outer
