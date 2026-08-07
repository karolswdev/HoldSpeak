"""Write-only credential transport adapters for app settings."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ....logging_config import get_logger
from ....services.credential_service import redacted_settings, strip_secret_mutations
from ....services.errors import NotFound, ServiceError, ValidationError
from ...context import WebContext
from ...runtime_support import error_500

log = get_logger("web.routes.system.settings_secrets")


def _service_error(exc: ServiceError) -> JSONResponse:
    if isinstance(exc, NotFound):
        return JSONResponse(
            {"success": False, "error": "Unknown secret setting"}, status_code=404
        )
    if isinstance(exc, ValidationError):
        return JSONResponse({"success": False, "error": exc.detail}, status_code=400)
    return JSONResponse({"success": False, "error": exc.detail}, status_code=400)


def register_settings_secret_routes(router: APIRouter, ctx: WebContext) -> None:
    service = ctx.credential_service
    if service is None:
        raise RuntimeError("CredentialService must be supplied at application composition")

    @router.put("/api/settings/secrets/{secret_id}")
    async def api_replace_secret(
        secret_id: str, body: dict[str, Any], request: Request
    ) -> Any:
        try:
            secrets = service.replace(
                request.state.principal, secret_id, body.get("value"), body
            )
            return JSONResponse({"success": True, "secrets": secrets})
        except ServiceError as exc:
            return _service_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to replace secret setting")

    @router.post("/api/settings/secrets/{secret_id}/rotate")
    async def api_rotate_secret(secret_id: str, request: Request) -> Any:
        try:
            secrets = service.rotate(request.state.principal, secret_id)
            return JSONResponse({"success": True, "secrets": secrets})
        except ServiceError as exc:
            return _service_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to rotate secret setting")

    @router.delete("/api/settings/secrets/{secret_id}")
    async def api_delete_secret(secret_id: str, request: Request) -> Any:
        try:
            secrets = service.delete(request.state.principal, secret_id)
            return JSONResponse({"success": True, "secrets": secrets})
        except ServiceError as exc:
            return _service_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to delete secret setting")


__all__ = [
    "redacted_settings",
    "register_settings_secret_routes",
    "strip_secret_mutations",
]
