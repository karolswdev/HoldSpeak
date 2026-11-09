"""Mesh discovery plus authenticated inbox and relay adapters.

``GET /api/mesh/inbox`` is produced from ``mesh.inbox`` (``holdspeak/device_operations.py``,
2026-11-09). The discovery answer and the three relay legs (a node protocol: the
edge derives the node's credential, never an argument) stay hand-written.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from ... import operations

from ...logging_config import get_logger
from ...principals import UNAUTHENTICATED
from ...services.errors import ConflictError, ServiceError, ValidationError
from ..context import WebContext
from ..operation_routes import operation_router
from ..runtime_support import error_500
from ._mount import mount_router

MESH_INFO_PATH = "/api/mesh/info"
log = get_logger("web.routes.mesh")


def _principal(request: Request) -> Any:
    return getattr(request.state, "principal", UNAUTHENTICATED)


def _credential(request: Request) -> Any:
    """The authenticated node snapshot the edge derived, or ``None``.

    HS-131-16: the relay legs need the node's NAME and credential generation as
    well as its opaque id, and none of those may come from the request body. The
    edge middleware puts the snapshot here when — and only when — a node token
    authenticated the request.
    """
    return getattr(request.state, "node_credential", None)


def _error(exc: ServiceError) -> JSONResponse:
    """Refusal by NAME (Article V.3): the machine class rides with the message.

    HS-131-16 gave this edge a fixed refusal vocabulary — forged offer, stale
    nonce, wrong node, replayed reservation, conflicting report — and a worker
    has to be able to act on WHICH rule refused, not parse prose. ``code`` is
    that class; ``error`` stays the human sentence.
    """
    body = {"error": exc.detail, "code": exc.code}
    if isinstance(exc, ValidationError):
        return JSONResponse(body, status_code=400)
    if isinstance(exc, ConflictError):
        return JSONResponse(body, status_code=409)
    return JSONResponse(body, status_code=int(exc.context.get("status") or 400))


def build_mesh_router(ctx: WebContext) -> APIRouter:
    service = ctx.mesh_service
    if service is None:
        raise RuntimeError("MeshService must be supplied at application composition")
    router = APIRouter()

    @router.get(MESH_INFO_PATH)
    def api_mesh_info() -> Any:
        from ... import __version__
        from ...config import Config
        from ...mesh import resolve_device_name
        try:
            configured = Config.load().mesh.device_name
        except Exception:
            configured = ""
        return JSONResponse({"name": resolve_device_name(configured), "version": __version__, "requiresToken": bool(ctx.mesh_requires_token)})

    async def answer(fn: Any, *, status: int = 200) -> Any:
        try:
            return JSONResponse(await run_in_threadpool(fn), status_code=status)
        except ServiceError as exc:
            return _error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to build the mesh inbox")

    by_name = {d.name: d for d in operations.DEVICE_OPERATIONS}
    mount_router(router, operation_router([by_name["mesh.inbox"]],
                                          lambda: operations.for_context(ctx), answer, module=__name__))

    @router.post("/api/mesh/relay/claim")
    def api_mesh_relay_claim(request: Request, payload: dict[str, Any]) -> Any:
        try:
            return JSONResponse(service.claim_relay(
                _principal(request), payload or {}, credential=_credential(request)
            ))
        except ServiceError as exc:
            return _error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to claim relay work")

    @router.post("/api/mesh/relay/{job_id}/complete")
    def api_mesh_relay_complete(job_id: str, request: Request, payload: dict[str, Any]) -> Any:
        try:
            return JSONResponse(service.complete_relay(
                _principal(request), job_id, payload or {}, credential=_credential(request)
            ))
        except ServiceError as exc:
            return _error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to complete relay work")

    @router.post("/api/mesh/relay/{job_id}/fail")
    def api_mesh_relay_fail(job_id: str, request: Request, payload: dict[str, Any]) -> Any:
        try:
            return JSONResponse(service.fail_relay(
                _principal(request), job_id, payload or {}, credential=_credential(request)
            ))
        except ServiceError as exc:
            return _error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to record relay failure")

    return router
