# PARKED 20261108 (evening, the unreached-routes census): routes no client calls.
#
# Parked whole from ``holdspeak/web/routes/system/agent_capabilities.py``: GET /api/agents/capabilities.
# Not imported. Kept for history; restore with ``git revert`` of the parking commit.
#
"""The one read API over the agent capability ledger (HS-104-01)."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ....agent_capabilities import capabilities_payload


def build_agent_capabilities_router() -> APIRouter:
    router = APIRouter()

    @router.get("/api/agents/capabilities")
    def api_agent_capabilities() -> Any:
        return JSONResponse(capabilities_payload())

    return router
