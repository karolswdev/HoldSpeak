"""The coder board: which live coding session receives a spoken answer.

2026-11-09 (one contract): the routes are produced from the declared rows in
``holdspeak/coder_operations.py`` through ``OperationRegistry.invoke``; each
verb is a ``CoderService`` method. The steering surface (peek, arm, steer,
audit, the factory) is produced in ``coder_steering_routes.py`` with the
registry and the answer envelope from here.
"""
from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from .... import operations
from ....logging_config import get_logger
from ....operations import OperationOwnerRequired
from ....services.coder_service import CoderRefused, CoderService
from ....services.errors import NotFound, ServiceError, ValidationError
from ...context import WebContext
from ...operation_routes import operation_router
from ...runtime_support import error_500
from .._mount import mount_router
from ._shared import _normalize_runtime_status_payload

log = get_logger("web.routes.system")

#: The board's rows, in route order.
BOARD = ("coder.status", "coder.list", "coder.own_agents", "coder.own_agents.answer",
         "coder.select", "coder.dismiss", "coder.pin")


def registry_for(ctx: WebContext) -> Callable[[], operations.OperationRegistry]:
    """The routes' registry: the hub's bound contract, else one over a coder
    service built for this context (its bus, its launch reads)."""

    def fallback() -> CoderService:
        from ....db import get_database, get_observer

        return CoderService(get_database(), observer=get_observer(), broadcast=getattr(ctx, "broadcast", None),
                            launch_reads=getattr(ctx, "agent_hand_reads", None))

    return lambda: operations.for_context(ctx, coder_service=fallback)


class Holding:
    """The routes' registry with the inputs only this transport holds for its rows."""

    def __init__(self, registry: Callable[[], Any], held: Callable[[], dict[str, Any]]) -> None:
        self._registry, self._held = registry, held

    def invoke(self, principal: Any, name: str, args: Any, *, shape: str = "call") -> Any:
        return self._registry().invoke(principal, name, args, held=self._held(), shape=shape)


async def answer(fn: Callable[[], Any], *, status: int = 200) -> JSONResponse:
    """The coder verbs' envelope: the answer, else the refusal's own body at
    the status the hand-written routes answered with."""
    try:
        return JSONResponse(await run_in_threadpool(fn), status_code=status)
    except CoderRefused as exc:
        return JSONResponse(exc.context["body"], status_code=int(exc.context["http"]))
    except OperationOwnerRequired as exc:
        return JSONResponse({"error": exc.code, "code": exc.code}, status_code=403)
    except ServiceError as exc:
        http = exc.context.get("http") or exc.context.get("status")
        if not isinstance(http, int):
            http = 404 if isinstance(exc, NotFound) else 400 if isinstance(exc, ValidationError) else 409
        return JSONResponse({"error": exc.detail, "code": exc.code}, status_code=http)
    except Exception as exc:
        return error_500(exc, log, "coder verb failed")


def produce(names: tuple[str, ...], registry: Callable[[], Any]) -> APIRouter:
    """The routes of the named coder rows, in the order named."""
    by_name = {descriptor.name: descriptor for descriptor in operations.CODER_OPERATIONS}
    return operation_router([by_name[name] for name in names], registry, answer, module=__name__)


def _status_inputs(ctx: WebContext) -> dict[str, Any]:
    """What ``coder.status`` reads from the hub itself: the runtime status
    (normalized) and the active devices."""
    from ....meeting_session import _device_descriptor_to_dict

    try:
        state = ctx.get_state() or {}
    except Exception as exc:
        log.error(f"get_state failed: {exc}")
        state = {}
    runtime_error: str | None = None
    raw: Any = {}
    if ctx.on_get_status is not None:
        try:
            raw = ctx.on_get_status()
        except Exception as exc:
            log.error(f"on_get_status failed: {exc}")
            runtime_error = str(exc)
            raw = {}
    runtime = _normalize_runtime_status_payload(raw if isinstance(raw, dict) else {"runtime_status": raw}, state)
    devices = [_device_descriptor_to_dict(descriptor) for descriptor in ctx.device_registry.active()]
    return {"runtime": runtime, "runtime_error": runtime_error, "devices": devices}


def build_coders_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()
    registry = registry_for(ctx)
    holding = Holding(registry, lambda: _status_inputs(ctx))
    mount_router(router, produce(BOARD[:1], lambda: holding))
    mount_router(router, produce(BOARD[1:], registry))
    return router


__all__ = ["BOARD", "Holding", "answer", "build_coders_router", "produce", "registry_for"]
