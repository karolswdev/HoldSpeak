"""Monday Brief read and generation transport adapters."""
from __future__ import annotations

from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, Body, HTTPException, Request

from ...db import get_database, get_observer
from ...principals import UNAUTHENTICATED
from ...services.monday_brief_service import MondayBriefService
from ..context import WebContext


def build_monday_brief_router(ctx: WebContext) -> APIRouter:
    """Expose the durable Monday Brief through the web API."""
    del ctx
    router = APIRouter(prefix="/api/brief", tags=["monday-brief"])
    service = MondayBriefService(get_database(), observer=get_observer())
    principal = lambda request: getattr(request.state, "principal", UNAUTHENTICATED)

    @router.get("/latest")
    async def latest(request: Request) -> dict[str, Any] | None:
        brief = service.get_latest(principal(request))
        return asdict(brief) if brief is not None else None

    @router.post("/generate")
    async def generate(request: Request) -> dict[str, Any]:
        return asdict(service.generate(principal(request)))

    # HS-132-08 — brief triage is a durable owner verb, not React state.
    @router.get("/shelf")
    async def read_shelf(request: Request) -> dict[str, str]:
        return service.shelf(principal(request))

    @router.post("/items/{item_id}/shelf")
    async def write_shelf(
        request: Request,
        item_id: str,
        body: dict[str, Any] = Body(default_factory=dict),
    ) -> dict[str, Any]:
        state = body.get("state")
        if state is not None and not isinstance(state, str):
            raise HTTPException(status_code=422, detail="state must be a string")
        try:
            return service.shelve(principal(request), item_id, state)
        except LookupError as unknown_item:
            raise HTTPException(status_code=404, detail=str(unknown_item)) from unknown_item
        except ValueError as unknown_state:
            raise HTTPException(status_code=422, detail=str(unknown_state)) from unknown_state

    return router
