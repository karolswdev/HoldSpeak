"""The one read API over the agent capability ledger (HS-104-01)."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ....agent_capabilities import capabilities_payload


def build_agent_capabilities_router() -> APIRouter:
    router = APIRouter()

    @router.get("/api/agents/capabilities")
    async def api_agent_capabilities() -> Any:
        return JSONResponse(capabilities_payload())

    return router
