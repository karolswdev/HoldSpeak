"""The Desk's contextual attention + receipt projection API (HS-92-09)."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ...logging_config import get_logger
from ..context import WebContext
from ..runtime_support import error_500

log = get_logger("web.routes.projections")


def build_projections_router(ctx: WebContext) -> APIRouter:
    del ctx
    router = APIRouter(prefix="/api/desk/projections", tags=["desk"])

    @router.get("")
    async def api_list_projections(
        q: str = "",
        kind: str | None = None,
        attention_state: str | None = None,
        subject_ref: str | None = None,
        include_dismissed: bool = False,
        offset: int = 0,
        limit: int = 50,
    ) -> Any:
        if kind not in {None, "attention", "receipt"}:
            return JSONResponse({"error": "kind must be attention or receipt"}, status_code=400)
        if attention_state not in {None, "unseen", "needs_attention", "acknowledged", "resolved"}:
            return JSONResponse({"error": "invalid attention_state"}, status_code=400)
        try:
            from ...db import get_database

            result = get_database().projections.list(
                search=q, projection_kind=kind, attention_state=attention_state,
                subject_ref=subject_ref, include_dismissed=include_dismissed,
                offset=offset, limit=limit,
            )
            return JSONResponse({"version": 1, **result})
        except (TypeError, ValueError) as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to project Desk attention and receipts")

    @router.put("/{projection_id}/presentation")
    async def api_set_projection_presentation(projection_id: str, request: Request) -> Any:
        try:
            body = await request.json()
        except Exception:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        if not isinstance(body, dict):
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            from ...db import get_database

            action = str(body.get("action") or "")
            if not get_database().projections.set_presentation(projection_id, action=action):
                return JSONResponse({"error": "Projection not found"}, status_code=404)
            return JSONResponse({
                "success": True, "projection_id": projection_id,
                "action": action, "subject_unchanged": True,
            })
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to update projection presentation")

    return router


__all__ = ["build_projections_router"]
