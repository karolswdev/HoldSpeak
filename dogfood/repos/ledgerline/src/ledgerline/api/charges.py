"""POST /charges — the charge endpoint with idempotency handling.

The header ``Idempotency-Key`` makes a charge safe to retry. The
first success for a key is recorded; later requests with the same key
replay the stored result and post nothing new. This is the guard that
prevents the LL-118 double-post failure mode.
"""
from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from ..db.entries import EntriesRepo
from ..db.idempotency import IdempotencyStore
from .. import ledger

router = APIRouter()


class ChargeRequest(BaseModel):
    account: str = Field(..., description="customer account to debit")
    amount_minor: int = Field(..., gt=0, description="amount in minor units (cents)")
    currency: str = Field("USD", min_length=3, max_length=3)


class ChargeResponse(BaseModel):
    group_id: str
    amount_minor: int
    replayed: bool = False


def make_router(entries: EntriesRepo, idem: IdempotencyStore) -> APIRouter:
    @router.post("/charges", response_model=ChargeResponse)
    def create_charge(
        body: ChargeRequest,
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    ) -> ChargeResponse:
        if not idempotency_key:
            raise HTTPException(400, "Idempotency-Key header is required")

        # Atomic check-and-record: the store serializes concurrent
        # retries so two requests with the same key cannot both post.
        # (The race that caused LL-118 lived here.)
        with idem.lock(idempotency_key):
            existing = idem.get(idempotency_key)
            if existing is not None:
                return ChargeResponse(
                    group_id=existing["group_id"],
                    amount_minor=existing["amount_minor"],
                    replayed=True,
                )

            posting = ledger.post(
                entries,
                debit_account=body.account,
                credit_account=f"revenue:{body.currency.lower()}",
                amount_minor=body.amount_minor,
            )
            idem.record(
                idempotency_key,
                group_id=posting.group_id,
                amount_minor=posting.amount_minor,
            )
            return ChargeResponse(
                group_id=posting.group_id,
                amount_minor=posting.amount_minor,
                replayed=False,
            )

    return router
