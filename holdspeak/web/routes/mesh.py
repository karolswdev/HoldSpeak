"""Mesh discovery plus authenticated inbox and relay adapters."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ...logging_config import get_logger
from ...principals import UNAUTHENTICATED
from ...services.errors import ConflictError, ServiceError, ValidationError
from ..context import WebContext
from ..runtime_support import error_500

MESH_INFO_PATH = "/api/mesh/info"
log = get_logger("web.routes.mesh")


def _principal(request: Request) -> Any:
    return getattr(request.state, "principal", UNAUTHENTICATED)


def _error(exc: ServiceError) -> JSONResponse:
    if isinstance(exc, ValidationError):
        return JSONResponse({"error": exc.detail}, status_code=400)
    if isinstance(exc, ConflictError):
        return JSONResponse({"error": exc.detail}, status_code=409)
    return JSONResponse({"error": exc.detail}, status_code=int(exc.context.get("status") or 400))


def build_mesh_router(ctx: WebContext) -> APIRouter:
    service = ctx.mesh_service
    if service is None:
        raise RuntimeError("MeshService must be supplied at application composition")
    router = APIRouter()

    @router.get(MESH_INFO_PATH)
    async def api_mesh_info() -> Any:
        from ... import __version__
        from ...config import Config
        from ...mesh import resolve_device_name
        try:
            configured = Config.load().mesh.device_name
        except Exception:
            configured = ""
        return JSONResponse({"name": resolve_device_name(configured), "version": __version__, "requiresToken": bool(ctx.mesh_requires_token)})

    @router.get("/api/mesh/inbox")
    async def api_mesh_inbox(request: Request) -> Any:
        try:
            return JSONResponse(service.list_inbox(_principal(request)))
        except ServiceError as exc:
            return _error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to build the mesh inbox")

    @router.post("/api/mesh/relay/claim")
    async def api_mesh_relay_claim(request: Request, payload: dict[str, Any]) -> Any:
        try:
            return JSONResponse(service.claim_relay(_principal(request), payload or {}))
        except ServiceError as exc:
            return _error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to claim relay work")

    @router.post("/api/mesh/relay/{job_id}/complete")
    async def api_mesh_relay_complete(job_id: str, request: Request, payload: dict[str, Any]) -> Any:
        try:
            return JSONResponse(service.complete_relay(_principal(request), job_id, payload or {}))
        except ServiceError as exc:
            return _error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to complete relay work")

    @router.post("/api/mesh/relay/{job_id}/fail")
    async def api_mesh_relay_fail(job_id: str, request: Request, payload: dict[str, Any]) -> Any:
        try:
            return JSONResponse(service.fail_relay(_principal(request), job_id, payload or {}))
        except ServiceError as exc:
            return _error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to record relay failure")

    return router
