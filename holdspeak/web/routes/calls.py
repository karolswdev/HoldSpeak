"""Calls transport (2026-10-28); the work is :mod:`holdspeak.calls.service`.

GET  /api/calls/status         the line, the engine, the steps, the active call
GET  /api/calls                the last 20 calls, newest first
GET  /api/calls/{id}           one call with its transcript
POST /api/calls/place          {"to"?}: HoldSpeak calls (default: his number)
POST /api/calls/{id}/hangup    end the call
POST /api/calls/{id}/decide    {"decision": "approve"|"deny"}: the tap form of his spoken yes

The Line (2026-10-29, LINE design §4 "the wire"; the node's side, text only):
POST /api/calls/line/hello     {node, lines, version, active_call?} → {config}
POST /api/calls/line/events    {node, events: [{seq, kind, ...}]} → {acked}
POST /api/calls/line/next      {node, after?, wait_s≤25} → {commands} (a long poll)
And what the faces need:
GET  /api/calls/line/status    the Line's node, state, words, address, and where each secret is
POST /api/calls/line/test      {"to"?}: the Line calls him, says one line, hangs up
"""
from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ...calls.service import CALLS, line_config, line_status
from ...line import line_on
from ...line.hub import LINE_HUB
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
    LINE_HUB.config_fn = line_config


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

    # ── the Line's wire (the node's side) ────────────────────────────

    def _line_off() -> Any:
        return JSONResponse({"error": "line_off", "reason": "off"}, status_code=409) if not line_on() else None

    async def _body(request: Request) -> dict[str, Any]:
        try:
            body = await request.json()
        except Exception:
            return {}
        return body if isinstance(body, dict) else {}

    def _node(body: dict[str, Any]) -> str:
        return str(body.get("node") or "").strip()[:64]

    @router.post("/api/calls/line/hello")
    async def api_line_hello(request: Request) -> Any:
        off = _line_off()
        if off is not None:
            return off
        body = await _body(request)
        node = _node(body)
        if not node:
            return JSONResponse({"error": "node is required", "reason": "usage"}, status_code=400)
        lines = body.get("lines") if isinstance(body.get("lines"), list) else []
        active = body.get("active_call") if isinstance(body.get("active_call"), dict) else None
        answer = await asyncio.to_thread(LINE_HUB.hello, node, lines=lines, version=str(body.get("version") or ""),
                                         active_call=active)
        return JSONResponse(answer)

    @router.post("/api/calls/line/events")
    async def api_line_events(request: Request) -> Any:
        off = _line_off()
        if off is not None:
            return off
        body = await _body(request)
        node = _node(body)
        events = [e for e in (body.get("events") or []) if isinstance(e, dict)][:200]
        if not node:
            return JSONResponse({"error": "node is required", "reason": "usage"}, status_code=400)
        return JSONResponse({"acked": LINE_HUB.post_events(node, events)})

    @router.post("/api/calls/line/next")
    async def api_line_next(request: Request) -> Any:
        off = _line_off()
        if off is not None:
            return off
        body = await _body(request)
        node = _node(body)
        if not node:
            return JSONResponse({"error": "node is required", "reason": "usage"}, status_code=400)
        try:
            after, wait = int(body.get("after") or 0), float(body.get("wait_s") or 0)
        except (TypeError, ValueError):
            return JSONResponse({"error": "after and wait_s are numbers", "reason": "usage"}, status_code=400)
        return JSONResponse({"commands": await LINE_HUB.next(node, after=after, wait=wait)})

    # ── the Line, for the faces ──────────────────────────────────────

    @router.get("/api/calls/line/status")
    async def api_line_status() -> Any:
        try:
            def read() -> dict[str, Any]:
                from ...calls.service import _settings

                return line_status(CALLS._phone_fn() if line_on() else None, _settings())
            return JSONResponse(await asyncio.to_thread(read))
        except Exception as exc:
            return error_500(exc, log, "Failed to read the line")

    @router.post("/api/calls/line/test")
    async def api_line_test(request: Request) -> Any:
        body = await _body(request)
        try:
            return JSONResponse(await CALLS.test_line(str(body.get("to") or "")))
        except ServiceError as exc:
            return _refused(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to place the test call")

    @router.get("/api/calls")
    def api_calls_list() -> Any:
        return JSONResponse({"calls": CALLS.list()})

    @router.get("/api/calls/{call_id}")
    def api_call_get(call_id: str) -> Any:
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
