"""The delivery routes produced from ``holdspeak/delivery_operations.py`` (2026-11-09).

Each route file mounts its own rows here, so a handler keeps its module and
name (the OpenAPI document does not change). The call is
``OperationRegistry.invoke``; the answer keeps the status codes and bodies the
hand-written handlers answered with: a typed delivery refusal carries its HTTP
status and body (``ServiceError.context``), any other failure is a classified
500 whose cause goes to the log, never to the wire (§12.3).
"""
from __future__ import annotations

from typing import Any, Callable, Iterable, Mapping

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from ... import operations
from ...logging_config import get_logger
from ...operations import OperationRefused
from ...services.delivery_service import TERMINAL_ABSENCE_HTTP, DeliveryService
from ...services.errors import ServiceError
from ..context import WebContext
from ..operation_routes import operation_router
from ._mount import mount_router

log = get_logger("web.routes.delivery")

#: The 500 body of each verb (the words the hand-written handler answered with).
_FAILED: dict[str, dict[str, Any]] = {
    "delivery.snapshot": {"error": "delivery snapshot failed"},
    "delivery.sources": {"error": "delivery sources read failed"},
    "delivery.source_register": {"error": "delivery source registration failed"},
    "delivery.attempts": {"error": "delivery attempts read failed"},
    "delivery.attempt_create": {"error": "delivery attempt creation failed"},
    "delivery.story_dossier": {"error": "story dossier failed"},
    "delivery.phase_dossier": {"error": "phase dossier failed"},
    "delivery.evidence_asset": {"error": "evidence asset failed"},
    "delivery.prs": {"error": "pr receipts read failed"},
    "delivery.prs_refresh": {"error": "pr receipts refresh failed"},
    "delivery.pr_diff": {"error": "pr diff failed"},
    "delivery.pr_fetch": {"error": "pr fetch failed"},
    "delivery.nodes": {"ok": False, "error": "node_link_failure"},
    "delivery.terminal_sessions": {"status": "error", "detail": "terminal session discovery failed", "sessions": []},
    "delivery.terminal_read": {"error": "terminal_stream_failure"},
    "delivery.factory_profiles": {"error": "factory_profiles_failure"},
    "delivery.factory_discover": {"error": "factory_discover_failure"},
}


def _unknown_pr(result: Any) -> int:
    return 404 if isinstance(result, dict) and result.get("status") == "unknown_pr" else 200


def _absence(result: Any) -> int:
    return TERMINAL_ABSENCE_HTTP.get(result.get("status"), 200) if isinstance(result, dict) else 200


#: The verbs whose answer status depends on the answer (a typed absence is an answer, not an error).
_STATUS_OF: dict[str, Callable[[Any], int]] = {
    "delivery.pr_diff": _unknown_pr, "delivery.pr_fetch": _unknown_pr, "delivery.terminal_read": _absence,
}


def delivery_of(ctx: WebContext) -> DeliveryService:
    """The context's DeliveryService; a partially wired context gets a bare one (no database)."""
    if ctx.delivery_service is None:
        ctx.delivery_service = DeliveryService(None)  # type: ignore[arg-type]
    from .actuator_shared import PrActuatorLifecycle
    ctx.delivery_service.configure(pr_actuators=PrActuatorLifecycle(ctx, ctx.delivery_service))
    return ctx.delivery_service


def registry_for(ctx: WebContext) -> Callable[[], operations.OperationRegistry]:
    """The hub's bound contract, else one bound over the context's services."""
    delivery_of(ctx)
    return lambda: operations.for_context(ctx)


def refused(name: str, exc: Exception) -> JSONResponse:
    """The wire answer of a failed delivery verb."""
    from ...delivery.commands import CommandRefused
    from ...delivery.factory_launch import LaunchRefused
    if isinstance(exc, (CommandRefused, LaunchRefused)):
        return JSONResponse({"ok": False, "error": exc.reason, "detail": str(exc)}, status_code=400)
    if isinstance(exc, ServiceError) and "http" in exc.context:
        return JSONResponse(exc.context.get("body") or {"error": exc.code, "detail": exc.detail},
                            status_code=int(exc.context["http"]))
    if isinstance(exc, ServiceError) and isinstance(exc.context.get("status"), int):  # owner_required: 403
        return JSONResponse({"error": exc.code, "detail": exc.detail}, status_code=exc.context["status"])
    if isinstance(exc, OperationRefused):  # the contract's refusal (invalid_arguments)
        return JSONResponse({"error": exc.code, "detail": exc.detail}, status_code=400)
    log.error(f"{name} failed: {exc}")
    return JSONResponse(_FAILED.get(name, {"error": f"{name} failed"}), status_code=500)


def _answer(name: str) -> Callable[..., Any]:
    async def answer(fn: Callable[[], Any], *, status: int = 200) -> JSONResponse:
        try:
            result = await run_in_threadpool(fn)
        except Exception as exc:
            return refused(name, exc)
        return JSONResponse(result, status_code=_STATUS_OF.get(name, lambda _r: status)(result))

    return answer


def router(ctx: WebContext, names: Iterable[str], *, module: str,
           hand_written: Mapping[str, Callable[[Any], Callable[..., Any]]] | None = None) -> APIRouter:
    """The routes of the named delivery operations, in the order named."""
    by_name = {descriptor.name: descriptor for descriptor in operations.DELIVERY_OPERATIONS}
    registry = registry_for(ctx)
    produced = APIRouter()
    for name in names:
        mount_router(produced, operation_router([by_name[name]], registry, _answer(name), module=module,
                                                hand_written=hand_written))
    return produced


__all__ = ["delivery_of", "refused", "registry_for", "router"]
