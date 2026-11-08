"""PARKED 20261108 (subtraction day, Lane R): routes no client reads.

Parked from ``holdspeak/web/routes/model_library.py``: POST /api/inference/model-library/connect-paired-device.
Not imported. Kept for history; restore with ``git revert`` of the parking commit.
"""
from __future__ import annotations
"""Narrow owner-only HTTP transport for ModelLibraryProjection@1."""

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ....services.errors import ServiceError
from ...context import WebContext
from ...runtime_support import error_500
from ....logging_config import get_logger

log = get_logger("web.routes.model_library")


def _safe_error(exc: ServiceError) -> JSONResponse:
    """Map domain failures without serializing private context or request bodies."""
    status = int(exc.context.get("status") or 400)
    # 422: a well-formed request for a provider with no execution adapter
    # (PHILO-15 05, `not_supported`); the same code MCP returns.
    if status not in {400, 403, 404, 409, 413, 422, 503}:
        status = 400
    return JSONResponse({"code": exc.code, "message": exc.detail}, status_code=status)


def parked_build_model_library_router(ctx: WebContext) -> APIRouter:
    service = ctx.model_library_service
    if service is None:
        raise RuntimeError("ModelLibraryApplicationService must be supplied at application composition")
    router = APIRouter()

    def _owner(request: Request) -> None:
        # Deliberately before request.json()/form(): unauthorized callers never
        # get their potentially sensitive body parsed or retained by this seam.
        service.require_owner(getattr(request.state, "principal", None))

    async def _json(request: Request) -> dict[str, Any]:
        _owner(request)
        try:
            body = await request.json()
        except Exception as exc:
            raise ServiceError("model_library_request_invalid", "Expected a JSON object.", context={"status": 400}) from exc
        if not isinstance(body, dict):
            raise ServiceError("model_library_request_invalid", "Expected a JSON object.", context={"status": 400})
        return body

    def _provider_error_500(detail: str) -> JSONResponse:
        """Never hand a post-parse provider exception to the generic echo mapper.

        Provider credentials are deliberately write-only. A lower custody or
        runtime adapter can fail unexpectedly, so neither its text nor an
        exception repr may become an ordinary HTTP body or route log.
        """
        return error_500(RuntimeError("Provider request could not be completed."), log, detail)

    async def _provider_body(request: Request) -> tuple[dict[str, Any], dict[str, Any] | None]:
        """Parse the nonsecret draft and dedicated write-only secret body.

        This seam intentionally has no request logging. Owner authority is
        checked before JSON parsing so an unauthorized caller's credential body
        cannot become request state here.
        """
        body = await _json(request)
        if set(body) != {"draft", "secret"} or not isinstance(body.get("draft"), dict):
            raise ServiceError("model_library_provider_invalid", "Provider request is invalid.", context={"status": 400})
        secret = body.get("secret")
        if secret is not None and not isinstance(secret, dict):
            raise ServiceError("model_library_secret_invalid", "Provider credential is invalid.", context={"status": 400})
        return body["draft"], secret

    def _engine_changed(reason: str) -> None:
        """An engine was added: the batteries-included default rule looks again."""
        defaults = getattr(ctx, "inference_default_service", None)
        if defaults is None:
            return
        try:
            from ....intel_queue_conductor import owns_database

            if owns_database():
                defaults.kick(reason)
        except Exception as exc:  # pragma: no cover - a kick never fails the write
            log.warning(f"default rule kick failed: {exc}")

    @router.post("/api/inference/model-library/connect-paired-device")
    async def connect_paired_device(request: Request) -> Any:
        try:
            draft, secret = await _provider_body(request)
            if secret is not None:
                raise ServiceError("model_library_secret_invalid", "Paired device has no credential body.", context={"status": 400})
            result = service.connect_paired_device(request.state.principal, draft)
            _engine_changed("connect_paired_device")
            return JSONResponse(result, status_code=200)
        except ServiceError as exc:
            return _safe_error(exc)
        except Exception:
            return _provider_error_500("Failed to connect paired device")

    return router


__all__ = ["parked_build_model_library_router"]
