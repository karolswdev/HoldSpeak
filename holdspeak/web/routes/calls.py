"""Calls transport (2026-10-28); the work is :mod:`holdspeak.calls.service`.

GET  /api/calls/status         the line, the engine, the steps, the active call
GET  /api/calls                the last 20 calls, newest first
GET  /api/calls/{id}           one call with its transcript
POST /api/calls/place          {"to"?}: HoldSpeak calls (default: his number)
POST /api/calls/{id}/hangup    end the call
POST /api/calls/{id}/decide    {"decision": "approve"|"deny"}: the tap form of his spoken yes
"""
from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ...calls.service import CALLS
from ...logging_config import get_logger
from ...services.errors import ServiceError, ValidationError
from ..context import WebContext
from ..runtime_support import error_500

log = get_logger("web.routes.calls")


def _refused(exc: ServiceError) -> JSONResponse:
    payload = dict(exc.context)
    status = int(payload.pop("status", 400 if isinstance(exc, ValidationError) else 409))
    payload.setdefault("error", exc.detail)
    payload.setdefault("reason", exc.code)
    return JSONResponse(payload, status_code=status)


def _missing() -> JSONResponse:
    return JSONResponse({"error": "call_not_found", "reason": "not_found"}, status_code=404)


def wire_calls(ctx: WebContext) -> None:
    """Bind the hub's broadcast and thread loop to the calls service."""
    from ._thread_factory import thread_service_from_ctx

    CALLS.configure(
        broadcast=lambda kind, data: (ctx.broadcast or (lambda *_: None))(kind, data),
        thread_factory=lambda **overrides: thread_service_from_ctx(ctx, **overrides),
    )


def build_calls_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()
    wire_calls(ctx)

    @router.get("/api/calls/status")
    async def api_calls_status() -> Any:
        try:
            CALLS.ensure_listening()
            return JSONResponse(await asyncio.to_thread(CALLS.status))
        except Exception as exc:
            return error_500(exc, log, "Failed to read calls")

    @router.get("/api/calls")
    async def api_calls_list() -> Any:
        return JSONResponse({"calls": CALLS.list()})

    @router.get("/api/calls/{call_id}")
    async def api_call_get(call_id: str) -> Any:
        found = CALLS.get(call_id)
        return JSONResponse(found) if found is not None else _missing()

    @router.post("/api/calls/place")
    async def api_call_place(request: Request) -> Any:
        try:
            body = await request.json()
        except Exception:
            body = {}
        to = str((body or {}).get("to") or "") if isinstance(body, dict) else ""
        try:
            return JSONResponse(await CALLS.place(to), status_code=201)
        except ServiceError as exc:
            return _refused(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to place the call")

    @router.post("/api/calls/{call_id}/hangup")
    async def api_call_hangup(call_id: str) -> Any:
        try:
            found = await CALLS.hangup(call_id)
        except Exception as exc:
            return error_500(exc, log, "Failed to hang up")
        return JSONResponse(found) if found is not None else _missing()

    @router.post("/api/calls/{call_id}/decide")
    async def api_call_decide(call_id: str, request: Request) -> Any:
        try:
            body = await request.json()
        except Exception:
            body = {}
        decision = str((body or {}).get("decision") or "") if isinstance(body, dict) else ""
        try:
            found = CALLS.decide(call_id, decision)
        except ServiceError as exc:
            return _refused(exc)
        return JSONResponse(found) if found is not None else _missing()

    return router


__all__ = ["build_calls_router", "wire_calls"]
