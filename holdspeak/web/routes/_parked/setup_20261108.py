"""PARKED 20261108 (subtraction day, Lane R): routes no client reads.

Parked from ``holdspeak/web/routes/setup.py``: POST /api/inference/acquisitions/{job_id}/cancel, GET /api/inference/capabilities, GET /api/inference/capabilities/{capability_id}, GET /api/inference/setup, GET /api/setup/hub-default-summary, GET /api/setup/runtime-options.
Not imported. Kept for history; restore with ``git revert`` of the parking commit.
"""
from __future__ import annotations
"""First-run setup surface routes (HS-42-01)."""

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from .... import operations
from ....logging_config import get_logger
from ....operations import OperationRefused
from ....principals import UNAUTHENTICATED
from ....services.errors import NotFound, ServiceError, ValidationError
from ...context import WebContext
from ...runtime_support import error_500
from .._room_kernel import kernel_refusal, refusal_fields, service_refusal

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


def parked_build_setup_router(ctx: WebContext) -> APIRouter:
    service = ctx.setup_service
    if service is None:
        raise RuntimeError("SetupService must be supplied at application composition")
    inference_setup = ctx.inference_setup_service
    if inference_setup is None:
        raise RuntimeError("InferenceSetupApplicationService must be supplied at application composition")
    inference_acquisition = ctx.inference_acquisition_service
    inference_capabilities = ctx.inference_capability_service
    router = APIRouter()

    def _ops() -> operations.OperationRegistry:
        return operations.for_context(ctx)

    def _principal(request: Request) -> Any:
        return getattr(request.state, "principal", UNAUTHENTICATED)

    def _contract_error(exc: OperationRefused) -> JSONResponse:
        return JSONResponse(
            {"success": False, "code": exc.code, "error_code": exc.code,
             "message": exc.detail, **refusal_fields(exc)},
            status_code=400,
        )

    def _service_error(exc: ServiceError) -> JSONResponse:
        if (refused := kernel_refusal(exc)) is not None:
            return refused
        return service_refusal(exc)

    @router.get("/api/setup/hub-default-summary")
    def api_hub_default_summary() -> Any:
        try:
            from ....inference_targets import this_machine_target

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

    def _local_ai() -> Any:
        local_ai = ctx.local_ai_setup_service
        if local_ai is None:
            raise ServiceError("local_ai_unavailable", "Set up local AI is not available on this hub.", context={"status": 503})
        return local_ai

    @router.get("/api/setup/runtime-options")
    async def api_runtime_options() -> Any:
        try:
            from ....setup_runtime import discover_local_models
            return await run_in_threadpool(discover_local_models)
        except Exception as exc:
            return error_500(exc, log, "Failed to discover local runtime models")

    @router.get("/api/inference/setup")
    def api_inference_setup(request: Request) -> Any:
        try:
            return {"setup": inference_setup.get_inference_setup(request.state.principal)}
        except ServiceError as exc:
            return _error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to read inference setup")

    @router.get("/api/inference/capabilities")
    def api_inference_capabilities(request: Request) -> Any:
        try:
            if inference_capabilities is None:
                raise RuntimeError("InferenceCapabilityApplicationService must be supplied at application composition")
            return {"capabilities": inference_capabilities.get_capabilities(request.state.principal)}
        except ServiceError as exc:
            return _inference_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to read inference capabilities")

    @router.get("/api/inference/capabilities/{capability_id}")
    def api_inference_capability(capability_id: str, request: Request) -> Any:
        try:
            if inference_capabilities is None:
                raise RuntimeError("InferenceCapabilityApplicationService must be supplied at application composition")
            return {"capability": inference_capabilities.get_capability(request.state.principal, capability_id)}
        except ServiceError as exc:
            return _inference_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to read inference capability")

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

    return router
