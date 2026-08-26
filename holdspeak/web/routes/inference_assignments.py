"""Narrow owner-only HTTP transport for assignment editor projections."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ...logging_config import get_logger
from ...services.errors import ConflictError, NotFound, ServiceError
from ..context import WebContext
from ..runtime_support import error_500

log = get_logger("web.routes.inference_assignments")


def _safe_error(exc: ServiceError) -> JSONResponse:
    """Map public domain failures without returning context or request bodies."""
    status = int(exc.context.get("status") or 0)
    if not status:
        status = 409 if isinstance(exc, ConflictError) else 404 if isinstance(exc, NotFound) else 400
    if status not in {400, 403, 404, 409, 503}:
        status = 400
    return JSONResponse({"code": exc.code, "message": exc.detail}, status_code=status)


def build_inference_assignments_router(ctx: WebContext) -> APIRouter:
    service = ctx.inference_assignment_service
    if service is None:
        raise RuntimeError("InferenceAssignmentService must be supplied at application composition")
    router = APIRouter()

    def _owner(request: Request) -> None:
        # This guard must stay before request.json(): unauthorised request bodies
        # are not parsed or retained by this owner-only seam.
        service._require_owner(getattr(request.state, "principal", None))

    async def _json(request: Request) -> dict[str, Any]:
        _owner(request)
        try:
            body = await request.json()
        except Exception as exc:
            raise ServiceError(
                "inference_assignment_request_invalid", "Expected a JSON object.", context={"status": 400}
            ) from exc
        if not isinstance(body, dict):
            raise ServiceError(
                "inference_assignment_request_invalid", "Expected a JSON object.", context={"status": 400}
            )
        return body

    @router.get("/api/inference/assignments")
    async def get_assignments(request: Request) -> Any:
        try:
            _owner(request)
            return service.assignment_summary(request.state.principal)
        except ServiceError as exc:
            return _safe_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to read Assignments")

    @router.post("/api/inference/assignments/editor")
    async def editor_projection(request: Request) -> Any:
        try:
            return service.assignment_editor_projection(request.state.principal, await _json(request))
        except ServiceError as exc:
            return _safe_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to read assignment editor")

    @router.post("/api/inference/assignments/set")
    async def set_assignment(request: Request) -> Any:
        try:
            return service.set_assignment(request.state.principal, await _json(request))
        except ServiceError as exc:
            return _safe_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to save assignment")

    @router.post("/api/inference/assignments/preview-use-default")
    async def preview_use_default(request: Request) -> Any:
        try:
            body = await _json(request)
            if set(body) - {"scope", "capability_id", "invocation_id", "subject_kind", "subject_id"} or set(body) != {"scope", "capability_id"}:
                raise ServiceError(
                    "inference_assignment_request_invalid", "Use default preview has an invalid request shape.", context={"status": 400}
                )
            return service.preview_use_default(
                request.state.principal,
                scope=body["scope"],
                capability_id=body["capability_id"],
            )
        except ServiceError as exc:
            return _safe_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to preview assignment default")

    @router.post("/api/inference/assignments/clear")
    async def clear_assignment(request: Request) -> Any:
        try:
            return service.clear_assignment(request.state.principal, await _json(request))
        except ServiceError as exc:
            return _safe_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to clear assignment")

    return router


__all__ = ["build_inference_assignments_router"]
