"""Decision record transport adapters for the Desk Intelligence pullout.

A decision record is the mutable governing document for a decision (HS-127-01);
"Receipt" is reserved for immutable kernel evidence (Constitution Art. XI).
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request

from ...db import get_database, get_observer
from ...principals import UNAUTHENTICATED
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

    return router
