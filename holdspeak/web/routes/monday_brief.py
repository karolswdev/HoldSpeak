"""Monday Brief read and generation transport adapters."""
from __future__ import annotations

from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, Request

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

    return router
