"""Calls transport: routes and tools share calls_operations and one LineService.

Only the wire (held node credential), code mint (request origin), and long
poll (awaited on this loop) need transport adapters. The public enrol exchange
keeps its one-time-code authority and never offers a tool or an agent a token.
The retired route bodies are in _parked/calls_handwritten_20261109.py.
"""
from __future__ import annotations

import inspect
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from ... import operations
from ...calls.service import CALLS, line_config
from ...line.hub import LINE_HUB
from ...logging_config import get_logger
from ...principals import UNAUTHENTICATED
from ...services.errors import NotFound, ServiceError, ValidationError
from ..context import WebContext
from ..operation_routes import operation_router
from ..runtime_support import error_500

log = get_logger("web.routes.calls")


def _refused(exc: ServiceError) -> JSONResponse:
    payload = dict(exc.context)
    status = int(payload.pop("status", 400 if isinstance(exc, ValidationError) else 409))
    payload.setdefault("error", exc.detail)
    payload.setdefault("reason", exc.code)
    return JSONResponse(payload, status_code=status)


async def _answer(fn: Any, *, status: int = 200) -> Any:
    """Bind the hub loop before async Calls verbs run from a worker."""
    operations.LIVE_CALLS_SERVICE.bind_loop()
    try:
        answer = await run_in_threadpool(fn)
        if inspect.isawaitable(answer):
            answer = {"commands": await answer}
        return JSONResponse(answer, status_code=status)
    except operations.OperationOwnerRequired as exc:
        return JSONResponse({"error": exc.detail, "reason": exc.code}, status_code=403)
    except operations.OperationRefused as exc:
        return JSONResponse({"error": exc.detail, "reason": exc.code}, status_code=400)
    except NotFound:
        return JSONResponse({"error": "call_not_found", "reason": "not_found"}, status_code=404)
    except ServiceError as exc:
        return _refused(exc)
    except Exception as exc:
        return error_500(exc, log, "Failed to run the call verb")


def wire_calls(ctx: WebContext) -> None:
    from ...services.thread_service import hub_thread_service

    CALLS.configure(
        broadcast=lambda kind, data: (ctx.broadcast or (lambda *_: None))(kind, data),
        thread_factory=lambda **overrides: hub_thread_service(ctx.broadcast, **overrides),
    )
    LINE_HUB.config_fn = line_config


async def _body(request: Request) -> dict[str, Any]:
    try:
        body = await request.json()
    except Exception:
        return {}
    return body if isinstance(body, dict) else {}


def build_calls_router(ctx: WebContext) -> APIRouter:
    wire_calls(ctx)

    def registry() -> operations.OperationRegistry:
        return operations.for_context(ctx, calls_service=lambda: operations.LIVE_CALLS_SERVICE)

    def wire(descriptor: Any) -> Any:
        async def endpoint(request: Request) -> Any:
            body = await _body(request)
            body.pop("node_credential", None)  # only the edge can hold this input
            principal = getattr(request.state, "principal", UNAUTHENTICATED)
            credential = getattr(request.state, "node_credential", None)
            return await _answer(lambda: registry().invoke(
                principal, descriptor.name, body, held={"node_credential": credential}, shape="web"))
        endpoint.__name__ = descriptor.handler
        return endpoint

    def code(descriptor: Any) -> Any:
        async def endpoint(request: Request) -> Any:
            body = await _body(request)
            body["hub"] = str(body.get("hub") or "").strip() or str(request.base_url).rstrip("/")
            principal = getattr(request.state, "principal", UNAUTHENTICATED)
            return await _answer(lambda: registry().invoke(principal, descriptor.name, body, shape="web"))
        endpoint.__name__ = descriptor.handler
        return endpoint

    return operation_router(
        operations.CALLS_OPERATIONS, registry, _answer, module=__name__,
        hand_written={**{f"calls.line.{verb}": wire for verb in ("hello", "events", "next")},
                      "calls.line.codes": code})


__all__ = ["build_calls_router", "wire_calls"]
