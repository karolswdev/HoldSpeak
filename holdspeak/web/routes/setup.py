"""First-run setup surface routes (HS-42-01)."""
from __future__ import annotations

import os
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


def _inference_error(exc: ServiceError) -> JSONResponse:
    body: dict[str, Any] = {
        "code": exc.code,
        "message": exc.detail,
        "recovery": exc.context.get("recovery"),
    }
    if "current" in exc.context:
        body["current"] = exc.context["current"]
    return JSONResponse(body, status_code=int(exc.context.get("status") or 400))


def build_setup_router(ctx: WebContext) -> APIRouter:
    service = ctx.setup_service
    if service is None:
        raise RuntimeError("SetupService must be supplied at application composition")
    inference_setup = ctx.inference_setup_service
    if inference_setup is None:
        raise RuntimeError("InferenceSetupApplicationService must be supplied at application composition")
    inference_acquisition = ctx.inference_acquisition_service
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
            from ...inference_targets import this_machine_target

            target = this_machine_target()
            if not target.ready:
                return {"engine": "", "model": "", "available": False}
            return {
                "engine": "llama.cpp",
                "model": target.model,
                "available": True,
            }
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
    async def api_first_value_event(attempt_id: str, request: Request, payload: dict[str, Any]) -> Any:
        allowed = {"event_id", "kind"}
        if set(payload or {}).difference(allowed):
            return JSONResponse({"success": False, "error": "First-value events accept only event_id and kind."}, status_code=400)
        try:
            return JSONResponse(
                service.record_event(request.state.principal, attempt_id, payload or {}),
                status_code=201,
            )
        except ServiceError as exc:
            return _error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to record first-value event")

    @router.get("/api/setup/runtime-options")
    async def api_runtime_options() -> Any:
        try:
            from ...setup_runtime import discover_local_models
            return discover_local_models()
        except Exception as exc:
            return error_500(exc, log, "Failed to discover local runtime models")

    @router.get("/api/inference/setup")
    async def api_inference_setup(request: Request) -> Any:
        try:
            return {"setup": inference_setup.get_inference_setup(request.state.principal)}
        except ServiceError as exc:
            return _error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to read inference setup")

    @router.post("/api/inference/acquisitions/download-and-use")
    async def api_inference_download_and_use(request: Request) -> Any:
        try:
            if inference_acquisition is None:
                raise ServiceError("inference_acquisition_unavailable", "Model downloads are unavailable on this hub.", context={"status": 503})
            body = await request.json()
            if not isinstance(body, dict):
                raise ServiceError("inference_acquisition_request_invalid", "Expected a JSON object.", context={"status": 400})
            return JSONResponse(
                inference_acquisition.download_and_use(request.state.principal, body),
                status_code=202,
            )
        except ServiceError as exc:
            return _inference_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to start model acquisition")

    @router.post("/api/inference/acquisitions/use-existing")
    async def api_inference_use_existing(request: Request) -> Any:
        try:
            if inference_acquisition is None:
                raise ServiceError("inference_acquisition_unavailable", "Local model setup is unavailable on this hub.", context={"status": 503})
            body = await request.json()
            if not isinstance(body, dict):
                raise ServiceError("inference_existing_request_invalid", "Expected a JSON object.", context={"status": 400})
            return JSONResponse(
                inference_acquisition.use_existing(request.state.principal, body),
                status_code=202,
            )
        except ServiceError as exc:
            return _inference_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to use existing local model")

    @router.get("/api/inference/acquisitions/{job_id}")
    async def api_inference_acquisition(job_id: str, request: Request) -> Any:
        try:
            if inference_acquisition is None:
                raise ServiceError("inference_acquisition_unavailable", "Model downloads are unavailable on this hub.", context={"status": 503})
            return inference_acquisition.get_acquisition(request.state.principal, job_id)
        except ServiceError as exc:
            return _inference_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to read model acquisition")

    @router.post("/api/inference/acquisitions/{job_id}/cancel")
    async def api_inference_cancel(job_id: str, request: Request) -> Any:
        try:
            if inference_acquisition is None:
                raise ServiceError("inference_acquisition_unavailable", "Model downloads are unavailable on this hub.", context={"status": 503})
            body = await request.json()
            if not isinstance(body, dict):
                raise ServiceError("inference_cancel_invalid", "Expected a JSON object.", context={"status": 400})
            return inference_acquisition.cancel(request.state.principal, job_id, body)
        except ServiceError as exc:
            return _inference_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to cancel model acquisition")

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
            from ...profile_key_store import ProfileKeyStoreError, resolve_profile_key
            from ...setup_runtime import discover_endpoint_models
            profile_id = str(body.get("profile_id") or "").strip()
            try:
                key = resolve_profile_key(profile_key_env(profile_id)) if profile_id else ""
            except ProfileKeyStoreError:
                key = ""
            fallback_key = os.environ.get("OPENAI_API_KEY") or None
            result = discover_endpoint_models(
                str(body.get("base_url") or ""),
                api_key=key if profile_id else fallback_key,
            )
            return JSONResponse(result, status_code=200 if result.get("ok") else 422)
        except Exception as exc:
            return error_500(exc, log, "Failed to discover endpoint models")

    return router
