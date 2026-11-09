"""Control-mode policy inspection and scoped-grant transport adapters."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ...logging_config import get_logger
from ...services.errors import ConflictError, NotFound, ServiceError, ValidationError
from ..context import WebContext
from ..runtime_support import error_500

log = get_logger("web.routes.authority")


async def _body(request: Request) -> dict[str, Any] | None:
    try:
        value = await request.json()
    except Exception:
        return None
    return value if isinstance(value, dict) else None


def _service_error(exc: ServiceError, *, missing_grant: str | None = None) -> JSONResponse:
    if isinstance(exc, ValidationError):
        return JSONResponse({"error": exc.detail}, status_code=400)
    if isinstance(exc, ConflictError):
        return JSONResponse({"error": exc.detail}, status_code=409)
    if isinstance(exc, NotFound):
        return JSONResponse(
            {"error": missing_grant or "Proposed action not found"}, status_code=404
        )
    return JSONResponse({"error": exc.detail}, status_code=400)


def build_authority_router(ctx: WebContext) -> APIRouter:
    service = ctx.authority_service
    if service is None:
        raise RuntimeError("AuthorityService must be supplied at application composition")
    router = APIRouter()

    @router.get("/api/authority/policy")
    def api_authority_policy(request: Request) -> Any:
        try:
            return JSONResponse(service.get_policy(request.state.principal))
        except ServiceError as exc:
            return _service_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to read authority policy")

    @router.put("/api/authority/control-mode")
    async def api_set_control_mode(request: Request) -> Any:
        body = await _body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            return JSONResponse(
                service.set_control_mode(
                    request.state.principal, str(body.get("control_mode") or "")
                )
            )
        except ServiceError as exc:
            return _service_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to update control mode")

    return router
