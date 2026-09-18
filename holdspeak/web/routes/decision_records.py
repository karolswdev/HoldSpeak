"""Decision record transport adapters for the Desk Intelligence pullout.

A decision record is the mutable governing document for a decision (HS-127-01);
"Receipt" is reserved for immutable kernel evidence (Constitution Art. XI).
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, HTTPException, Request
from fastapi.responses import JSONResponse

from ...db import get_database, get_observer
from ...principals import UNAUTHENTICATED
from ...services.brief_carry import RightRequired
from ...services.decision_record_service import DecisionRecordService


def build_decision_records_router(ctx: Any) -> APIRouter:
    """Expose durable decision records through the web API."""
    del ctx
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
