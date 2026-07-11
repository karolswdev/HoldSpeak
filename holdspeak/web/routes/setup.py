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

    @router.put("/api/setup/onboarding")
    async def api_onboarding_disposition(payload: dict[str, Any]) -> Any:
        """Persist completed/dismissed/needs-help independently of success."""
        try:
            from ...db import get_database

            state = get_database().onboarding.set_disposition(
                str((payload or {}).get("disposition") or "")
            )
            return {"success": True, "onboarding": state}
        except ValueError as exc:
            return JSONResponse({"success": False, "error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to update onboarding disposition")

    @router.post("/api/setup/first-value/start")
    async def api_first_value_start(payload: dict[str, Any]) -> Any:
        """Start local, content-free first-value measurement."""
        forbidden = {"text", "phrase", "transcript", "content", "audio"}
        if forbidden.intersection(payload or {}):
            return JSONResponse(
                {"success": False, "error": "First-value receipts never accept phrase content."},
                status_code=400,
            )
        try:
            from ...db import get_database

            attempt = get_database().onboarding.start_attempt(
                destination=str((payload or {}).get("destination") or "this_machine")
            )
            return JSONResponse({"success": True, "attempt": attempt}, status_code=201)
        except ValueError as exc:
            return JSONResponse({"success": False, "error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to start first-value receipt")

    @router.post("/api/setup/first-value/{attempt_id}/finish")
    async def api_first_value_finish(attempt_id: str, payload: dict[str, Any]) -> Any:
        """Finish one measurement and close onboarding on verified success."""
        forbidden = {"text", "phrase", "transcript", "content", "audio"}
        if forbidden.intersection(payload or {}):
            return JSONResponse(
                {"success": False, "error": "First-value receipts never accept phrase content."},
                status_code=400,
            )
        try:
            from ...db import FIRST_DICTATION_SUCCESS, get_database

            database = get_database()
            outcome = str((payload or {}).get("outcome") or "")
            attempt = database.onboarding.finish_attempt(
                attempt_id,
                outcome=outcome,
                # The repository derives these from its content-free event
                # ledger. Legacy counters are accepted at the wire boundary
                # but cannot overwrite observed mechanics.
                steps=(payload or {}).get("steps"),
                decisions=(payload or {}).get("decisions"),
                destination=str((payload or {}).get("destination") or "this_machine"),
                failure_category=(payload or {}).get("failure_category"),
            )
            # `finish_attempt` is idempotent: a repeated request returns the
            # stored terminal receipt. Only that receipt may promote success;
            # a late/replayed "success" must never overwrite a prior failure.
            if attempt.get("succeeded_at"):
                database.milestones.mark(FIRST_DICTATION_SUCCESS)
                database.onboarding.set_disposition("completed")
            return {"success": True, "attempt": attempt}
        except KeyError as exc:
            return JSONResponse({"success": False, "error": str(exc)}, status_code=404)
        except (TypeError, ValueError) as exc:
            return JSONResponse({"success": False, "error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to finish first-value receipt")

    @router.post("/api/setup/first-value/{attempt_id}/event")
    async def api_first_value_event(attempt_id: str, payload: dict[str, Any]) -> Any:
        """Record one bounded interaction event without accepting owner content."""
        allowed = {"event_id", "kind"}
        extra = set(payload or {}).difference(allowed)
        if extra:
            return JSONResponse(
                {
                    "success": False,
                    "error": "First-value events accept only event_id and kind.",
                },
                status_code=400,
            )
        try:
            from ...db import get_database

            event = get_database().onboarding.record_event(
                attempt_id,
                event_id=str((payload or {}).get("event_id") or ""),
                kind=str((payload or {}).get("kind") or ""),
            )
            return JSONResponse({"success": True, "event": event}, status_code=201)
        except KeyError as exc:
            return JSONResponse({"success": False, "error": str(exc)}, status_code=404)
        except ValueError as exc:
            return JSONResponse({"success": False, "error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to record first-value event")

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
