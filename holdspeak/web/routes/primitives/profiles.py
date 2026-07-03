"""Runtime profiles CRUD (the key never rides the wire).

Bodies moved verbatim from routes/primitives.py (HS-79-03, the Phase-63 discipline).
"""
from __future__ import annotations

import uuid
from typing import Any, Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ....logging_config import get_logger
from ...context import WebContext
from ...runtime_support import error_500

log = get_logger("web.routes.primitives")
from ._shared import _json_body, _new_id


def build_profiles_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    def _profile_fields(body: dict[str, Any], existing=None) -> dict[str, Any]:
        def pick(key: str, default: Any) -> Any:
            return body[key] if key in body else default
        return {
            "name": str(pick("name", existing.name if existing else "")),
            "kind": str(pick("kind", existing.kind if existing else "onDevice")),
            "model_file": str(pick("model_file", existing.model_file if existing else "")),
            "base_url": str(pick("base_url", existing.base_url if existing else "")),
            "model": str(pick("model", existing.model if existing else "")),
            "context_limit": int(pick("context_limit", existing.context_limit if existing else 16384)),
            "requires_key": bool(pick("requires_key", existing.requires_key if existing else False)),
        }

    @router.get("/api/profiles")
    async def api_list_profiles() -> Any:
        try:
            from ....db import get_database
            return JSONResponse({"profiles": [p.to_dict() for p in get_database().profiles.list()]})
        except Exception as exc:
            return error_500(exc, log, "Failed to list profiles")

    @router.post("/api/profiles")
    async def api_create_profile(request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        if not str(body.get("name") or "").strip():
            return JSONResponse({"error": "profile name is required"}, status_code=400)
        try:
            from ....db import get_database
            profile = get_database().profiles.upsert(
                profile_id=str(body.get("id") or _new_id("profile")),
                **_profile_fields(body),
            )
            return JSONResponse({"profile": profile.to_dict()}, status_code=201)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to create profile")

    @router.get("/api/profiles/{profile_id}")
    async def api_get_profile(profile_id: str) -> Any:
        try:
            from ....db import get_database
            profile = get_database().profiles.get(profile_id)
            if profile is None:
                return JSONResponse({"error": f"Unknown profile: {profile_id}"}, status_code=404)
            return JSONResponse({"profile": profile.to_dict()})
        except Exception as exc:
            return error_500(exc, log, "Failed to get profile")

    @router.put("/api/profiles/{profile_id}")
    async def api_update_profile(profile_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            from ....db import get_database
            db = get_database()
            existing = db.profiles.get(profile_id)
            if existing is None:
                return JSONResponse({"error": f"Unknown profile: {profile_id}"}, status_code=404)
            profile = db.profiles.upsert(profile_id=profile_id, **_profile_fields(body, existing))
            return JSONResponse({"profile": profile.to_dict()})
        except Exception as exc:
            return error_500(exc, log, "Failed to update profile")

    @router.delete("/api/profiles/{profile_id}")
    async def api_delete_profile(profile_id: str) -> Any:
        try:
            from ....db import get_database
            if not get_database().profiles.delete(profile_id):
                return JSONResponse({"error": f"Unknown profile: {profile_id}"}, status_code=404)
            return JSONResponse({"success": True})
        except Exception as exc:
            return error_500(exc, log, "Failed to delete profile")

    # ── KBs (knowledge bases) ─────────────────────────────────────────────

    return router
