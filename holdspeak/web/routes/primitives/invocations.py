"""Read-only capability run receipts for retry, inspection, and return."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ....logging_config import get_logger
from ...context import WebContext
from ...runtime_support import error_500

log = get_logger("web.routes.primitives.invocations")


def build_invocations_router(ctx: WebContext) -> APIRouter:
    del ctx
    router = APIRouter()

    @router.get("/api/invocations")
    async def api_list_invocations(limit: int = 100) -> Any:
        try:
            from ....db import get_database
            rows = get_database().capability_invocations.list(limit=limit)
            return JSONResponse({"invocations": [row.to_dict() for row in rows]})
        except Exception as exc:
            return error_500(exc, log, "Failed to list capability invocations")

    @router.get("/api/invocations/{invocation_id}")
    async def api_get_invocation(invocation_id: str) -> Any:
        try:
            from ....db import get_database
            row = get_database().capability_invocations.get(invocation_id)
            if row is None:
                return JSONResponse({"error": f"Unknown invocation: {invocation_id}"}, status_code=404)
            return JSONResponse({"invocation": row.to_dict()})
        except Exception as exc:
            return error_500(exc, log, "Failed to get capability invocation")

    return router
