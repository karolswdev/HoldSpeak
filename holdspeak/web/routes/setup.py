"""First-run setup surface routes (HS-42-01).

`GET /api/setup/status` returns the composed setup-state snapshot (the adapter over
the doctor + readiness + egress + presence — see `holdspeak.setup_status`). It is a
cheap read: no large-model load, no default network call.
"""
from __future__ import annotations

from typing import Any

import os

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ...logging_config import get_logger
from ..context import WebContext
from ..runtime_support import error_500

log = get_logger("web.routes.setup")


def build_setup_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    @router.get("/api/setup/status")
    async def api_setup_status() -> Any:
        """One UI-friendly first-run readiness snapshot (HS-42-01)."""
        try:
            from ...setup_status import build_setup_status

            database = None
            try:
                from ...db import get_database

                database = get_database()
            except Exception as exc:  # never block the status read on the DB
                log.warning(f"setup status: database unavailable ({exc})")

            return build_setup_status(database=database)
        except Exception as exc:  # pragma: no cover - defensive
            return error_500(exc, log, "Failed to build setup status")

    @router.post("/api/setup/runtime-test")
    async def api_setup_runtime_test() -> Any:
        """Test the configured dictation (intelligent-typing) runtime (HS-42-06).

        Local backends → resolve + model-path-exists; an OpenAI-compatible endpoint
        → a time-boxed HTTP preflight. Reads the current config; opt-in (the
        caller decides when to run it)."""
        try:
            from ...config import Config
            from ...setup_runtime import probe_runtime

            return probe_runtime(Config.load().dictation)
        except Exception as exc:  # pragma: no cover - defensive
            return error_500(exc, log, "Failed to test runtime")

    @router.get("/api/setup/runtime-options")
    async def api_runtime_options() -> Any:
        """Real local model choices plus human-friendly context presets."""
        try:
            from ...setup_runtime import discover_local_models

            return discover_local_models()
        except Exception as exc:  # pragma: no cover - defensive
            return error_500(exc, log, "Failed to discover local runtime models")

    @router.post("/api/setup/discover-models")
    async def api_discover_models(request: Request) -> Any:
        """Proxy OpenAI-compatible model discovery from the trusted local hub."""
        try:
            body = await request.json()
        except Exception:
            return JSONResponse({"ok": False, "models": [], "detail": "Expected a JSON object."}, status_code=400)
        if not isinstance(body, dict):
            return JSONResponse({"ok": False, "models": [], "detail": "Expected a JSON object."}, status_code=400)
        try:
            from ...intel.providers import profile_key_env
            from ...setup_runtime import discover_endpoint_models

            profile_id = str(body.get("profile_id") or "").strip()
            key = ""
            if profile_id:
                key = os.environ.get(profile_key_env(profile_id), "")
            if not key:
                key = os.environ.get("OPENAI_API_KEY", "")
            result = discover_endpoint_models(
                str(body.get("base_url") or ""), api_key=key or None
            )
            return JSONResponse(result, status_code=200 if result.get("ok") else 422)
        except Exception as exc:  # pragma: no cover - defensive
            return error_500(exc, log, "Failed to discover endpoint models")

    return router
