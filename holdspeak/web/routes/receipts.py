"""Decision receipt transport adapters for the Desk Intelligence pullout."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request

from ...db import get_database, get_observer
from ...principals import UNAUTHENTICATED
from ...services.decision_receipt_service import DecisionReceiptService


def build_receipts_router(ctx: Any) -> APIRouter:
    """Expose durable decision receipts through the web API."""
    del ctx
    router = APIRouter(prefix="/api/receipts", tags=["receipts"])

    def service() -> DecisionReceiptService:
        return DecisionReceiptService(get_database(), observer=get_observer())

    def principal(request: Request) -> Any:
        return getattr(request.state, "principal", UNAUTHENTICATED)

    @router.get("")
    async def list_receipts(
        request: Request, limit: int = 50, offset: int = 0
    ) -> list[dict[str, Any]]:
        return service().list_receipts(principal(request), limit=limit, offset=offset)

    # Declare search before the parameterized path so FastAPI does not regard
    # "search" as a receipt ID.
    @router.get("/search")
    async def search_receipts(
        request: Request, q: str = "", limit: int = 50
    ) -> list[dict[str, Any]]:
        return service().search(principal(request), q, limit=limit)

    @router.get("/{receipt_id}")
    async def get_receipt(receipt_id: str, request: Request) -> dict[str, Any]:
        receipt = service().get(principal(request), receipt_id)
        if receipt is None:
            raise HTTPException(status_code=404, detail="receipt not found")
        return receipt

    return router
