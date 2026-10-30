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
Enrolment (LINE-3): a Line node on another machine gets its own credential,
scoped to the three wire routes above and nothing else:
POST   /api/calls/line/codes          {node}: a one-time code (10 minutes, once) and the command to run there
POST   /api/calls/line/enrol          {code}: public at the edge; the code is the authority → {node, token}
GET    /api/calls/line/nodes          the enrolled Line nodes and each one's word from its last hello
DELETE /api/calls/line/nodes/{node}   revoke that node's credential
The Telnyx setup (LINE-3b, ``holdspeak/line/setup.py``; his key in the keystore):
GET  /api/calls/line/telnyx/status    key? connection? number? balance
POST /api/calls/line/telnyx/connect   the SIP connection (idempotent); the password to the keystore
GET  /api/calls/line/telnyx/numbers   ?area=212: up to 10 numbers with their cost and a quote each
POST /api/calls/line/telnyx/buy       {phone_number, quote}: BUYS (money); refused without his
                                      press's quote; the kernel operation calls.line.buy_number
POST /api/calls/line/telnyx/assign    {phone_number}: point it at the line; calls.line.account.number
"""
from __future__ import annotations

import asyncio
from typing import Any, Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ...calls.service import CALLS, line_config, line_status
from ...line import line_on
from ...line.enrol import CODES, EnrolError, enrolled, redeem, revoke, wire_node
from ...line import setup as line_setup
from ...line.hub import LINE_HUB
from ...logging_config import get_logger
from ...principals import UNAUTHENTICATED
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

    def _node(body: dict[str, Any], request: Optional[Request] = None) -> str:
        """The node a wire request speaks for: a line credential speaks only
        for its own node (LINE-3); the owner's token names it in the body."""
        named = str(body.get("node") or "").strip()[:64]
        if request is None:
            return named
        return wire_node(getattr(request.state, "node_credential", None), named) or ""

    @router.post("/api/calls/line/hello")
    async def api_line_hello(request: Request) -> Any:
        off = _line_off()
        if off is not None:
            return off
        body = await _body(request)
        node = _node(body, request)
        if not node:
            return JSONResponse({"error": "node is required", "reason": "usage"}, status_code=400)
        lines = body.get("lines") if isinstance(body.get("lines"), list) else []
        active = body.get("active_call") if isinstance(body.get("active_call"), dict) else None
        machine = body.get("machine") if isinstance(body.get("machine"), dict) else None
        answer = await asyncio.to_thread(LINE_HUB.hello, node, lines=lines, version=str(body.get("version") or ""),
                                         active_call=active, machine=machine)
        return JSONResponse(answer)

    @router.post("/api/calls/line/events")
    async def api_line_events(request: Request) -> Any:
        off = _line_off()
        if off is not None:
            return off
        body = await _body(request)
        node = _node(body, request)
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
        node = _node(body, request)
        if not node:
            return JSONResponse({"error": "node is required", "reason": "usage"}, status_code=400)
        try:
            after, wait = int(body.get("after") or 0), float(body.get("wait_s") or 0)
        except (TypeError, ValueError):
            return JSONResponse({"error": "after and wait_s are numbers", "reason": "usage"}, status_code=400)
        return JSONResponse({"commands": await LINE_HUB.next(node, after=after, wait=wait)})

    # ── enrolment (LINE-3) ───────────────────────────────────────────

    def _store(request: Request) -> Any:
        return getattr(request.app.state, "node_token_store", None)

    @router.post("/api/calls/line/codes")
    async def api_line_code(request: Request) -> Any:
        body = await _body(request)
        try:
            minted = CODES.mint(str(body.get("node") or ""))
        except EnrolError as exc:
            return JSONResponse({"error": str(exc), "reason": exc.reason}, status_code=400)
        hub = str(body.get("hub") or "").strip() or str(request.base_url).rstrip("/")
        minted["hub"] = hub
        minted["command"] = f"holdspeak line enrol --hub {hub} --code {minted['code']} --node {minted['node']}"
        return JSONResponse(minted)

    @router.post("/api/calls/line/enrol")
    async def api_line_enrol(request: Request) -> Any:
        off = _line_off()
        if off is not None:
            return off
        store = _store(request)
        if store is None:
            return JSONResponse({"error": "This hub has no node store.", "reason": "no_store"}, status_code=409)
        body = await _body(request)
        try:
            answer = await asyncio.to_thread(redeem, CODES, store, str(body.get("code") or ""))
        except EnrolError as exc:
            return JSONResponse({"error": str(exc), "reason": exc.reason}, status_code=401)
        log.info(f"line node enrolled: {answer['node']}")
        return JSONResponse(answer)

    @router.get("/api/calls/line/nodes")
    async def api_line_nodes(request: Request) -> Any:
        store = _store(request)

        def read() -> list[dict[str, Any]]:
            from ...line.adapter import Line
            from ...calls.service import _settings

            cfg = _settings()
            rows = []
            for row in enrolled(store):
                status = line_status(Line(row["node"]), cfg)
                rows.append({**row, "state": status["state"], "words": status["words"],
                             "machine": status.get("machine") or {}})
            return rows

        try:
            return JSONResponse({"nodes": await asyncio.to_thread(read)})
        except Exception as exc:
            return error_500(exc, log, "Failed to read the line nodes")

    @router.delete("/api/calls/line/nodes/{node}")
    async def api_line_node_revoke(node: str, request: Request) -> Any:
        store = _store(request)
        try:
            done = store is not None and await asyncio.to_thread(revoke, store, node)
        except EnrolError as exc:
            return JSONResponse({"error": str(exc), "reason": exc.reason}, status_code=400)
        if not done:
            return JSONResponse({"error": "No such Line node.", "reason": "not_found"}, status_code=404)
        return JSONResponse({"node": node, "revoked": True})

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

    # ── the Telnyx setup (LINE-3b): each press off the loop ──────────

    async def _telnyx(request: Request, work: Any, what: str) -> Any:
        off = _line_off()
        if off is not None:
            return off
        try:
            return JSONResponse(await asyncio.to_thread(work))
        except ServiceError as exc:
            return _refused(exc)
        except Exception as exc:
            return error_500(exc, log, what)

    @router.get("/api/calls/line/telnyx/status")
    async def api_line_telnyx_status(request: Request) -> Any:
        return await _telnyx(request, lambda: line_setup.TELNYX_SETUP.status(), "Failed to read Telnyx")

    @router.post("/api/calls/line/telnyx/connect")
    async def api_line_telnyx_connect(request: Request) -> Any:
        return await _telnyx(request, lambda: line_setup.TELNYX_SETUP.connect(), "Failed to connect to Telnyx")

    @router.get("/api/calls/line/telnyx/numbers")
    async def api_line_telnyx_numbers(request: Request, area: str = "") -> Any:
        return await _telnyx(request, lambda: line_setup.TELNYX_SETUP.numbers(area), "Failed to find numbers")

    @router.post("/api/calls/line/telnyx/buy")
    async def api_line_telnyx_buy(request: Request) -> Any:
        body = await _body(request)
        principal = getattr(request.state, "principal", UNAUTHENTICATED)
        return await _telnyx(request, lambda: line_setup.TELNYX_SETUP.buy(
            principal, str(body.get("phone_number") or ""), str(body.get("quote") or "")), "Failed to buy the number")

    @router.post("/api/calls/line/telnyx/assign")
    async def api_line_telnyx_assign(request: Request) -> Any:
        body = await _body(request)
        return await _telnyx(request, lambda: line_setup.TELNYX_SETUP.assign(str(body.get("phone_number") or "")),
                             "Failed to assign the number")

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
