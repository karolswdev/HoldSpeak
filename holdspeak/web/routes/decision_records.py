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
from ...principals import UNAUTHENTICATED
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

    @router.post("/from-desk")
    def create_from_desk(request: Request, body: dict[str, Any] = Body(default={})) -> Any:
        """Admit one Desk decision, then return its canonical record.

        The admitted ``decision.create`` operation owns the retained source
        row and its canonical record.  This adapter only supplies the
        producer's About/Why context, the deciders and the tags that carry
        the meeting, the Project and the Person. The record writer
        (``DecisionRecordService.create``) files the record in the Project
        and writes the Person reference in the record's own transaction, so
        a caller makes one call.
        """
        title = str(body.get("decision_text") or body.get("title") or "").strip()
        if not title:
            raise HTTPException(status_code=400, detail="decision text is required")
        status = str(body.get("status") or "accepted").strip().lower()
        if status not in {"accepted", "proposed"}:
            raise HTTPException(status_code=400, detail="status must be accepted or proposed")
        project_id = str(body.get("project_id") or "").strip()
        project_name = str(body.get("project_name") or "").strip()
        about = str(body.get("about") or project_name or "").strip()
        why = str(body.get("why") or "").strip()
        if project_id and service().live_project([project_id]) is None:
            return JSONResponse({"error": f"Unknown Project: {project_id}"}, status_code=400)
        tags = [str(tag).strip() for tag in (body.get("tags") or []) if str(tag).strip()]
        if project_id and f"project:{project_id}" not in tags:
            tags.append(f"project:{project_id}")
        meeting_id = str(body.get("meeting_id") or "").strip()
        if meeting_id and f"meeting:{meeting_id}" not in tags:
            tags.append(f"meeting:{meeting_id}")
        owner_person_id = str(body.get("owner_person_id") or "").strip()
        if owner_person_id and f"person:{owner_person_id}" not in tags:
            tags.append(f"person:{owner_person_id}")
        raw_deciders = body.get("deciders") or []
        deciders = list(dict.fromkeys(
            str(name).strip() for name in (raw_deciders if isinstance(raw_deciders, list) else [])
            if str(name).strip()
        ))
        principal_value = principal(request)
        registry = operations.for_context(ctx, "primitive_service")
        args = {
            "title": title,
            "status": status,
            "deciders": deciders,
            "context_markdown": f"About: {about}" if about else "",
            "decision_markdown": title,
            "alternatives": [],
            "consequences_markdown": f"Why: {why}" if why else "",
            "tags": tags,
        }
        try:
            decision, kernel = registry.invoke_receipted(principal_value, "decision.create", args)
            records = service()
            matches = records.records_for_source(principal_value, "desk", str(decision["id"]))
            record = matches[0] if matches else None
            if record is None:
                raise HTTPException(status_code=500, detail="canonical decision record was not created")
            record = records.get(principal_value, record["id"]) or record
            return JSONResponse(
                {"decision": decision, "record": record, **_kernel_fields(kernel)}, status_code=201,
            )
        except operations.OperationRefused as exc:
            kernel = registry.refuse(principal_value, "decision.create", exc.code, body) or {}
            return JSONResponse({"error": str(exc), **kernel}, status_code=400)
        except ServiceError as exc:
            status_code = int(exc.context.get("status") or 409)
            return JSONResponse({"error": exc.code, "detail": exc.detail, **exc.context}, status_code=status_code)
        except ValueError as exc:
            return JSONResponse({"error": str(exc), **_refusal_kernel(exc)}, status_code=400)
        except HTTPException:
            raise
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
    mount_router(outer, produced(
        ctx, RECORD_OPERATIONS, _answer, module=__name__,
        decision_record_service=lambda: DecisionRecordService(get_database(), observer=get_observer()),
    ))
    mount_router(outer, router)
    return outer
