"""Declared mesh discovery and inbox, with credential-holding relay transports."""
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

    service._discovery_requires_token = lambda: bool(ctx.mesh_requires_token)

    async def answer(fn: Any, *, status: int = 200) -> Any:
        try:
            return JSONResponse(await run_in_threadpool(fn), status_code=status)
        except ServiceError as exc:
            return _error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to build the mesh inbox")

    def api_mesh_relay_claim(request: Request, payload: dict[str, Any]) -> Any:
        try:
            return JSONResponse(registry().invoke(_principal(request), "mesh.relay.claim", {"payload": payload or {}},
                              held={"credential": _credential(request)}))
        except ServiceError as exc:
            return _error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to claim relay work")

    def api_mesh_relay_complete(job_id: str, request: Request, payload: dict[str, Any]) -> Any:
        try:
            return JSONResponse(registry().invoke(_principal(request), "mesh.relay.complete", {"job_id": job_id, "payload": payload or {}},
                              held={"credential": _credential(request)}))
        except ServiceError as exc:
            return _error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to complete relay work")

    def api_mesh_relay_fail(job_id: str, request: Request, payload: dict[str, Any]) -> Any:
        try:
            return JSONResponse(registry().invoke(_principal(request), "mesh.relay.fail", {"job_id": job_id, "payload": payload or {}},
                              held={"credential": _credential(request)}))
        except ServiceError as exc:
            return _error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to record relay failure")

    def registry() -> operations.OperationRegistry:
        return operations.for_context(ctx)

    callbacks = {"mesh.relay.claim": api_mesh_relay_claim, "mesh.relay.complete": api_mesh_relay_complete,
                 "mesh.relay.fail": api_mesh_relay_fail}
    mount_router(router, operation_router(
        [d for d in operations.DEVICE_OPERATIONS if d.service == "mesh_service"], registry, answer,
        module=__name__, hand_written={name: lambda d, handler=handler: handler
                                      for name, handler in callbacks.items()}))

    return router
