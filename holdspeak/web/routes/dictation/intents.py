"""Intent-control routes (`/api/intents/*`) — HS-34-01 split of `dictation.py`."""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ....logging_config import get_logger
from ....web_requests import (
    _IntentOverrideRequest,
    _IntentPreviewRequest,
    _IntentProfileRequest,
)
from ...context import WebContext

log = get_logger("web.routes.dictation")


def build_intents_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    @router.get("/api/intents/control")
    async def api_get_intent_controls() -> Any:
        if ctx.on_get_intent_controls is None:
            return JSONResponse(
                {
                    "enabled": False,
                    "profile": "balanced",
                    "available_profiles": [],
                    "supported_intents": [],
                    "override_intents": [],
                }
            )
        try:
            payload = ctx.on_get_intent_controls()
        except Exception as e:
            log.error(f"on_get_intent_controls failed: {e}")
            return JSONResponse({"success": False, "error": str(e)}, status_code=500)
        return JSONResponse(payload if isinstance(payload, dict) else {"controls": payload})

    @router.put("/api/intents/profile")
    async def api_set_intent_profile(payload: _IntentProfileRequest) -> Any:
        if ctx.on_set_intent_profile is None:
            return JSONResponse(
                {"success": False, "error": "Intent profile updates not supported"},
                status_code=501,
            )
        try:
            result = ctx.on_set_intent_profile(payload.profile)
        except Exception as e:
            log.error(f"on_set_intent_profile failed: {e}")
            return JSONResponse({"success": False, "error": str(e)}, status_code=500)

        if isinstance(result, dict):
            ctx.broadcast("intent_controls_updated", result)
        return JSONResponse({"success": True, "controls": result})

    @router.put("/api/intents/override")
    async def api_set_intent_override(payload: _IntentOverrideRequest) -> Any:
        if ctx.on_set_intent_override is None:
            return JSONResponse(
                {"success": False, "error": "Intent override updates not supported"},
                status_code=501,
            )
        try:
            result = ctx.on_set_intent_override(payload.intents)
        except Exception as e:
            log.error(f"on_set_intent_override failed: {e}")
            return JSONResponse({"success": False, "error": str(e)}, status_code=500)

        if isinstance(result, dict):
            ctx.broadcast("intent_controls_updated", result)
        return JSONResponse({"success": True, "controls": result})

    @router.post("/api/intents/preview")
    async def api_preview_intent_route(payload: Optional[_IntentPreviewRequest] = None) -> Any:
        if ctx.on_route_preview is None:
            return JSONResponse(
                {"success": False, "error": "Intent route preview not supported"},
                status_code=501,
            )
        try:
            result = ctx.on_route_preview(
                profile=payload.profile if payload is not None else None,
                threshold=payload.threshold if payload is not None else None,
                intent_scores=payload.intent_scores if payload is not None else None,
                override_intents=payload.override_intents if payload is not None else None,
                previous_intents=payload.previous_intents if payload is not None else None,
                tags=payload.tags if payload is not None else None,
                transcript=payload.transcript if payload is not None else None,
            )
        except Exception as e:
            log.error(f"on_route_preview failed: {e}")
            return JSONResponse({"success": False, "error": str(e)}, status_code=500)
        return JSONResponse({"success": True, "route": result})

    return router
