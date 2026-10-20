"""Decision record transport adapters for the Desk Intelligence pullout.

A decision record is the mutable governing document for a decision (HS-127-01);
"Receipt" is reserved for immutable kernel evidence (Constitution Art. XI).
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, HTTPException, Request
from fastapi.responses import JSONResponse

from ... import operations
from ...db import get_database, get_observer
from ...logging_config import get_logger
from ...principals import UNAUTHENTICATED
from ...services.brief_carry import RightRequired
from ...services.decision_record_service import DecisionRecordService
from ...services.errors import ServiceError
from ...web.runtime_support import error_500
from .primitives._shared import _kernel_fields, _refusal_kernel

log = get_logger("web.routes.decision_records")


def build_decision_records_router(ctx: Any) -> APIRouter:
    """Expose durable decision records through the web API."""
    router = APIRouter(prefix="/api/decision-records", tags=["decision-records"])

    def service() -> DecisionRecordService:
        return DecisionRecordService(get_database(), observer=get_observer())

    def principal(request: Request) -> Any:
        return getattr(request.state, "principal", UNAUTHENTICATED)

    @router.get("")
    async def list_records(
        request: Request, limit: int = 50, offset: int = 0
    ) -> list[dict[str, Any]]:
        return service().list_records(principal(request), limit=limit, offset=offset)

    # Declare search before the parameterized path so FastAPI does not regard
    # "search" as a record ID.
    @router.get("/search")
    async def search_records(
        request: Request, q: str = "", limit: int = 50
    ) -> list[dict[str, Any]]:
        return service().search(principal(request), q, limit=limit)

    @router.get("/review")
    async def records_due_for_review(request: Request) -> list[dict[str, Any]]:
        return service().due_for_review(principal(request))

    @router.post("/from-desk")
    async def create_from_desk(request: Request, body: dict[str, Any] = Body(default={})) -> Any:
        """Admit one Desk decision, then return its canonical record.

        The admitted ``decision.create`` operation owns the retained source
        row and its canonical record.  This adapter only supplies the
        producer's About/Why context. The admitted producer also owns the
        record's meeting and Project links.
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
        tags = [str(tag).strip() for tag in (body.get("tags") or []) if str(tag).strip()]
        if project_id and f"project:{project_id}" not in tags:
            tags.append(f"project:{project_id}")
        meeting_id = str(body.get("meeting_id") or "").strip()
        if meeting_id and f"meeting:{meeting_id}" not in tags:
            tags.append(f"meeting:{meeting_id}")
        principal_value = principal(request)
        registry = operations.for_context(ctx, "primitive_service")
        args = {
            "title": title,
            "status": status,
            "deciders": [],
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

    @router.get("/source/{source_type}/{source_id}")
    async def records_for_source(
        source_type: str, source_id: str, request: Request
    ) -> list[dict[str, Any]]:
        return service().records_for_source(principal(request), source_type, source_id)

    @router.get("/work/{work_type}/{work_ref}")
    async def records_for_work(
        work_type: str, work_ref: str, request: Request
    ) -> list[dict[str, Any]]:
        return service().records_for_work(principal(request), work_type, work_ref)

    @router.get("/{record_id}")
    async def get_record(record_id: str, request: Request) -> dict[str, Any]:
        record = service().get(principal(request), record_id)
        if record is None:
            raise HTTPException(status_code=404, detail="decision record not found")
        return record

    # ── HS-200-13: the lifecycle verbs the recall chain needs ──────────

    @router.post("/{record_id}/supersede")
    async def supersede_record(
        record_id: str, request: Request, body: dict[str, Any] = Body(default={}),
    ) -> Any:
        """Seal ``record_id`` and name ``successor_id`` as what is current now."""
        try:
            return service().supersede(
                principal(request), record_id,
                str(body.get("successor_id") or ""), body.get("reason"),
            )
        except RightRequired as exc:
            return JSONResponse(exc.response, status_code=403)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=f"decision record not found: {exc}") from exc
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @router.post("/{record_id}/dispute")
    async def dispute_record(
        record_id: str, request: Request, body: dict[str, Any] = Body(default={}),
    ) -> Any:
        """Mark a record DISPUTED (discoverable, never presented as current)."""
        try:
            return service().dispute(principal(request), record_id, body.get("reason"))
        except RightRequired as exc:
            return JSONResponse(exc.response, status_code=403)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=f"decision record not found: {exc}") from exc
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @router.post("/{record_id}/carry")
    async def carry_record(
        record_id: str, request: Request, body: dict[str, Any] = Body(default={}),
    ) -> Any:
        """`Carry into brief`: queue the record, by reference, for its Project's
        next preparation (holdspeak/services/brief_carry.py)."""
        from ...services.brief_carry import carry_into_brief
        try:
            return carry_into_brief(
                get_database(), principal(request), record_id,
                project_id=body.get("project_id"),
            )
        except RightRequired as exc:
            return JSONResponse(exc.response, status_code=403)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=f"decision record not found: {exc}") from exc
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    return router
