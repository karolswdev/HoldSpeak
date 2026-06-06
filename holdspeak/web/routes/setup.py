"""First-run setup surface routes (HS-42-01).

`GET /api/setup/status` returns the composed setup-state snapshot (the adapter over
the doctor + readiness + egress + presence — see `holdspeak.setup_status`). It is a
cheap read: no large-model load, no default network call.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter

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

    return router
