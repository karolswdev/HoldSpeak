"""Authenticated application transport for the Apple admitted-attempt bridge."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ....services.apple_admitted_inference_service import AppleAdmittedInferenceService
from ....services.errors import ServiceError
from ...runtime_support import error_500
from ._shared import _json_body
from ....logging_config import get_logger

log = get_logger("web.routes.apple_admitted_inference")


def _service() -> AppleAdmittedInferenceService:
    # The coordinator belongs to the process broker.  Attaching this thin adapter
    # there keeps signed opaque tickets valid across the client's begin/reconcile
    # requests without creating a second resolver/controller composition.
    from ....kernel.runtime import _service as runtime_service

    coordinator = runtime_service().inference_adoption_service
    service = getattr(coordinator, "_apple_admitted_inference_service", None)
    if service is None:
        service = AppleAdmittedInferenceService(coordinator)
        setattr(coordinator, "_apple_admitted_inference_service", service)
    return service


def _error(exc: ServiceError) -> JSONResponse:
    status = 403 if exc.code == "apple_admitted_owner_required" else int(exc.context.get("status") or 400)
    return JSONResponse({"code": exc.code, "message": exc.detail}, status_code=status)


def build_apple_admitted_inference_router() -> APIRouter:
    router = APIRouter()

    @router.post("/api/inference/apple/attempts/admit")
    async def admit(request: Request) -> Any:
        body = await _json_body(request)
        if not isinstance(body, dict):
            return JSONResponse({"code": "apple_admitted_request_invalid", "message": "Expected a JSON object."}, status_code=400)
        allowed = {"command_id", "capability_id", "operation_id", "payload", "invocation_id", "subject_kind", "subject_id", "reserved_output_tokens"}
        if set(body) - allowed or not {"command_id", "capability_id", "operation_id", "payload"}.issubset(body) or not isinstance(body.get("payload"), dict):
            return JSONResponse({"code": "apple_admitted_request_invalid", "message": "Apple admission request is invalid."}, status_code=400)
        try:
            return _service().admit(
                request.state.principal,
                command_id=str(body["command_id"]), capability_id=str(body["capability_id"]),
                operation_id=str(body["operation_id"]), payload=body["payload"],
                invocation_id=str(body["invocation_id"]) if body.get("invocation_id") else None,
                subject_kind=str(body["subject_kind"]) if body.get("subject_kind") else None,
                subject_id=str(body["subject_id"]) if body.get("subject_id") else None,
                reserved_output_tokens=int(body.get("reserved_output_tokens") or 512),
            )
        except ServiceError as exc:
            return _error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to admit Apple inference attempt")

    @router.post("/api/inference/apple/attempts/begin")
    async def begin(request: Request) -> Any:
        body = await _json_body(request)
        if not isinstance(body, dict) or set(body) != {"authorization"}:
            return JSONResponse({"code": "apple_admitted_request_invalid", "message": "Apple begin request is invalid."}, status_code=400)
        try:
            return _service().begin(request.state.principal, authorization=str(body["authorization"]))
        except ServiceError as exc:
            return _error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to begin Apple inference attempt")

    @router.post("/api/inference/apple/attempts/reconcile")
    async def reconcile(request: Request) -> Any:
        body = await _json_body(request)
        if not isinstance(body, dict) or set(body) - {"authorization", "outcome", "result"} or not {"authorization", "outcome"}.issubset(body):
            return JSONResponse({"code": "apple_admitted_request_invalid", "message": "Apple reconciliation request is invalid."}, status_code=400)
        try:
            return _service().reconcile(
                request.state.principal, authorization=str(body["authorization"]),
                classified_outcome=str(body["outcome"]), result=body.get("result") if isinstance(body.get("result"), str) else None,
            )
        except ServiceError as exc:
            return _error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to reconcile Apple inference attempt")

    return router
