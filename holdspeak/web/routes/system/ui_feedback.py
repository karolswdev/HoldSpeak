"""Owner-local Desk UI feedback routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ....logging_config import get_logger
from ....services.ui_feedback import UIFeedbackConflict, UIFeedbackError
from ....services.ui_feedback import enabled as feedback_enabled
from ....services.ui_feedback import save_feedback

log = get_logger("web.routes.system")


def build_ui_feedback_router() -> APIRouter:
    router = APIRouter()

    @router.get("/api/ui-feedback/status")
    async def api_ui_feedback_status() -> dict[str, bool]:
        return {"enabled": feedback_enabled()}

    @router.post("/api/ui-feedback")
    async def api_ui_feedback(request: Request) -> Any:
        if not feedback_enabled():
            return JSONResponse(
                {"success": False, "error": "UI feedback is disabled."}, status_code=404
            )
        try:
            payload = await request.json()
        except Exception:
            return JSONResponse(
                {"success": False, "error": "A JSON object is required."}, status_code=400
            )
        try:
            return JSONResponse(save_feedback(payload))
        except UIFeedbackConflict as exc:
            return JSONResponse({"success": False, "error": str(exc)}, status_code=409)
        except UIFeedbackError as exc:
            return JSONResponse({"success": False, "error": str(exc)}, status_code=400)
        except Exception as exc:  # pragma: no cover - filesystem-specific failures
            log.exception("Failed to save local UI feedback: %s", exc)
            return JSONResponse(
                {"success": False, "error": "The local feedback bundle could not be saved."},
                status_code=500,
            )

    return router


__all__ = ["build_ui_feedback_router"]
