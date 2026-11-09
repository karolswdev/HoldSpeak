# PARKED 2026-11-09 (ops/programs-work): the hand-written constitutional-context router, kept verbatim.
# GET/PUT /api/constitutional-context and GET .../history are rows in
# holdspeak/desk_state_operations.py now (constitutional_context.read / update / history),
# over ConstitutionalContextService (holdspeak/constitutional_context.py); each produces
# its route (same method, path and answer) and its MCP tool. The update is the owner's.
# Not mounted, not imported. Restore with git revert of the parking commit.
# ruff: noqa
"""Constitutional context routes (HS-116-03, hardened HS-116-13).

GET/PUT the owner's always-on context that every agent run receives.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ...logging_config import get_logger
from ...constitutional_context import (
    CHAR_LIMIT,
    get_constitutional_context,
    get_constitutional_history,
    update_constitutional_context,
)
from ..runtime_support import error_500

log = get_logger("web.routes.constitutional")


def build_constitutional_router() -> APIRouter:
    router = APIRouter()

    @router.get("/api/constitutional-context")
    def api_get_context() -> Any:
        try:
            ctx = get_constitutional_context()
            ctx["char_limit"] = CHAR_LIMIT
            return JSONResponse({"context": ctx})
        except Exception as exc:
            return error_500(exc, log, "Failed to read constitutional context")

    @router.put("/api/constitutional-context")
    async def api_update_context(request: Request) -> Any:
        try:
            body = await request.json()
        except Exception:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        content = body.get("content")
        if content is None:
            return JSONResponse({"error": "content field is required"}, status_code=400)
        try:
            ctx = update_constitutional_context(str(content))
            ctx["char_limit"] = CHAR_LIMIT
            return JSONResponse({"context": ctx})
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to update constitutional context")

    @router.get("/api/constitutional-context/history")
    def api_context_history() -> Any:
        try:
            revisions = get_constitutional_history()
            return JSONResponse({"revisions": revisions})
        except Exception as exc:
            return error_500(exc, log, "Failed to read context history")

    return router
