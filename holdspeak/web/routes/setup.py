"""First-run setup surface routes (HS-42-01)."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ...logging_config import get_logger
from ...services.errors import NotFound, ServiceError, ValidationError
from ..context import WebContext
from ..runtime_support import error_500

log = get_logger("web.routes.setup")


def _error(exc: ServiceError) -> JSONResponse:
    if isinstance(exc, NotFound):
        return JSONResponse({"success": False, "error": repr(exc.id)}, status_code=404)
    if isinstance(exc, ValidationError):
        return JSONResponse({"success": False, "error": exc.detail}, status_code=400)
    return JSONResponse({"success": False, "error": exc.detail}, status_code=int(exc.context.get("status") or 400))


def build_setup_router(ctx: WebContext) -> APIRouter:
    service = ctx.setup_service
    if service is None:
        raise RuntimeError("SetupService must be supplied at application composition")
    router = APIRouter()

    @router.get("/api/setup/status")
    async def api_setup_status(request: Request) -> Any:
        try:
            return service.status(request.state.principal)
        except ServiceError as exc:
            return _error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to build setup status")

    @router.get("/api/setup/hub-default-summary")
    async def api_hub_default_summary() -> Any:
        try:
            from ...config import Config
            runtime = Config.load().dictation.runtime
            backend = str(runtime.backend or "auto").strip().lower()
            candidates = {"mlx": str(runtime.mlx_model or "").strip(), "llama_cpp": str(runtime.llama_cpp_model_path or "").strip()}
            selected = [backend] if backend in candidates else ["mlx", "llama_cpp"] if backend == "auto" else []
            resolved = next(((engine, model_path) for engine in selected if (model_path := candidates[engine]) and Path(model_path).expanduser().exists()), None)
            if resolved is None:
                return {"engine": "", "model": "", "available": False}
            engine, model_path = resolved
            return {"engine": "llama.cpp" if engine == "llama_cpp" else engine, "model": Path(model_path).expanduser().stem, "available": True}
        except Exception as exc:
            return error_500(exc, log, "Failed to read hub default summary")

    @router.post("/api/setup/runtime-test")
    async def api_setup_runtime_test(request: Request) -> Any:
        try:
            return service.test_runtime(request.state.principal)
        except ServiceError as exc:
            return _error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to test runtime")

    @router.put("/api/setup/onboarding")
    async def api_onboarding_disposition(request: Request, payload: dict[str, Any]) -> Any:
        try:
            return service.set_onboarding_disposition(request.state.principal, payload or {})
        except ServiceError as exc:
            return _error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to update onboarding disposition")

    @router.post("/api/setup/first-value/start")
    async def api_first_value_start(request: Request, payload: dict[str, Any]) -> Any:
        try:
            return JSONResponse(service.start_first_value(request.state.principal, payload or {}), status_code=201)
        except ServiceError as exc:
            return _error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to start first-value receipt")

    @router.post("/api/setup/first-value/{attempt_id}/finish")
    async def api_first_value_finish(attempt_id: str, request: Request, payload: dict[str, Any]) -> Any:
        try:
            return service.finish_first_value(request.state.principal, attempt_id, payload or {})
        except ServiceError as exc:
            return _error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to finish first-value receipt")

    @router.post("/api/setup/first-value/{attempt_id}/event")
    async def api_first_value_event(attempt_id: str, payload: dict[str, Any]) -> Any:
        allowed = {"event_id", "kind"}
        if set(payload or {}).difference(allowed):
            return JSONResponse({"success": False, "error": "First-value events accept only event_id and kind."}, status_code=400)
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
        try:
            from ...setup_runtime import discover_local_models
            return discover_local_models()
        except Exception as exc:
            return error_500(exc, log, "Failed to discover local runtime models")

    @router.post("/api/setup/discover-models")
    async def api_discover_models(request: Request) -> Any:
        try:
            body = await request.json()
        except Exception:
            body = None
        if not isinstance(body, dict):
            return JSONResponse({"ok": False, "models": [], "detail": "Expected a JSON object."}, status_code=400)
        try:
            from ...intel.providers import profile_key_env
            from ...setup_runtime import discover_endpoint_models
            profile_id = str(body.get("profile_id") or "").strip()
            key = os.environ.get(profile_key_env(profile_id), "") if profile_id else ""
            result = discover_endpoint_models(
                str(body.get("base_url") or ""),
                api_key=key or os.environ.get("OPENAI_API_KEY") or None,
            )
            return JSONResponse(result, status_code=200 if result.get("ok") else 422)
        except Exception as exc:
            return error_500(exc, log, "Failed to discover endpoint models")

    return router
