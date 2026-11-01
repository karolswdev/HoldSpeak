"""Phone transport (2026-10-28, design §10); the work is :mod:`holdspeak.phone.service`.

POST   /api/phone/pair                         owner: a 10-minute pairing token and its QR
POST   /api/phone/devices                      the app: {pair_token, name, platform, push_token?} → its device token
GET    /api/phone/devices                      owner: the paired phones
DELETE /api/phone/devices/{id}                 owner: revoke (its socket closes, its token stops at once)
POST   /api/phone/messages                     owner, agent, device: {text, reply_to?} → the message
GET    /api/phone/messages?after_seq=          owner, device
POST   /api/phone/messages/{id}/read           owner, device
POST   /api/phone/messages/{id}/wait           owner: Let it wait (it leaves Needs you)
POST   /api/phone/calls                        owner, agent (gated): {reason, context, urgent} → {call_id, state}
GET    /api/phone/calls                        owner: the calls
GET    /api/phone/calls/{id}                   owner, device
POST   /api/phone/calls/{id}/accept|decline|end   device, owner
POST   /api/phone/calls/{id}/ring              owner: a held call rings (Call now)
POST   /api/phone/calls/{id}/again             owner: a missed call, again (Call again)
GET    /api/phone/events?after_seq=            owner, device: the event log
GET    /api/phone/status                       owner
GET    /api/phone/push                         owner: where each part of his Apple push key is (never the key)
PUT    /api/phone/push                         owner: {p8?, key_id?, team_id?, bundle_id?, host?} → the key store
POST   /api/phone/push/test                    owner: one silent push to the paired phone; Apple's answer
WS     /api/phone/ws?after_seq=                device (or owner): replay from after_seq, then live

The device principal is its JWT (``Authorization: Bearer <device token>``;
on the socket also ``?device_token=``), and every request reads the device
row again; the owner principal is the hub token. The edge lets the device
routes through (``principals.phone_device_route``); each handler here decides
who may call it. Every handler runs the service off the event loop.
"""
from __future__ import annotations

import asyncio
from typing import Any, Callable, Optional

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from ...logging_config import get_logger
from ...phone import devices as devs
from ...principals import PrincipalKind
from ...services.errors import ServiceError
from ..context import WebContext

log = get_logger("web.routes.phone")

#: A socket with no frame from the hub for this long gets a ping.
PING_SECONDS = 20.0


def _service() -> Any:
    from ...phone.service import default_phone_service

    return default_phone_service()


def _principal(request: Request) -> Any:
    return getattr(request.state, "principal", None)


def _owner_or_agent(request: Request) -> Any:
    principal = _principal(request)
    kind = getattr(principal, "kind", None)
    return principal if kind in (PrincipalKind.OWNER, PrincipalKind.AGENT) else None


def _device_token(request: Any) -> str:
    return devs.bearer(request.headers.get("authorization"))


async def _device(request: Request) -> Optional[dict[str, Any]]:
    token = _device_token(request)
    if not token or token.count(".") != 2:
        return None
    return await run_in_threadpool(_service().authenticate, token)


async def _body(request: Request) -> dict[str, Any]:
    try:
        body = await request.json()
    except Exception:
        body = None
    return body if isinstance(body, dict) else {}


def _refused(exc: ServiceError) -> JSONResponse:
    payload = dict(exc.context)
    status = int(payload.pop("status", 409))
    return JSONResponse({"error": exc.code, "code": exc.code, "detail": exc.detail, **payload}, status_code=status)


def _unauthorized() -> JSONResponse:
    return JSONResponse({"error": "unauthorized", "code": "unauthorized",
                         "detail": "This phone is not paired, or it was revoked. Pair it again."}, status_code=401)


async def _call(fn: Callable[[], Any], *, status: int = 200) -> JSONResponse:
    try:
        return JSONResponse(await run_in_threadpool(fn), status_code=status)
    except ServiceError as exc:
        return _refused(exc)
    except Exception as exc:
        log.error(f"phone route failed: {exc}", exc_info=True)
        return JSONResponse({"error": "phone_failed", "code": "phone_failed",
                             "detail": "The phone service failed. Nothing changed. The log names the cause."},
                            status_code=500)


def build_phone_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    @router.post("/api/phone/pair")
    async def api_phone_pair(request: Request) -> Any:
        principal = _principal(request)
        base = str(request.base_url).rstrip("/")
        return await _call(lambda: _service().pair_token(principal, hub_urls=[base]), status=201)

    @router.post("/api/phone/devices")
    async def api_phone_devices_pair(request: Request) -> Any:
        body = await _body(request)
        return await _call(lambda: _service().redeem(body), status=201)

    @router.get("/api/phone/devices")
    async def api_phone_devices(request: Request) -> Any:
        principal = _principal(request)
        return await _call(lambda: _service().devices(principal))

    @router.delete("/api/phone/devices/{device_id}")
    async def api_phone_device_revoke(device_id: str, request: Request) -> Any:
        principal = _principal(request)
        return await _call(lambda: _service().revoke(principal, device_id))

    @router.post("/api/phone/messages")
    async def api_phone_message_send(request: Request) -> Any:
        body = await _body(request)
        principal, device = _owner_or_agent(request), None
        if principal is None:
            device = await _device(request)
            if device is None:
                return _unauthorized()
        text, reply_to = str(body.get("text") or ""), body.get("reply_to") or None
        step = body.get("program_step_id") or None
        return await _call(lambda: _service().send_message(principal, text, reply_to, device=device,
                                                           program_step_id=step), status=201)

    @router.get("/api/phone/messages")
    async def api_phone_messages(request: Request) -> Any:
        if _owner_or_agent(request) is None and await _device(request) is None:
            return _unauthorized()
        after = int(request.query_params.get("after_seq") or 0)
        return await _call(lambda: _service().messages(after_seq=after))

    @router.post("/api/phone/messages/{message_id}/read")
    async def api_phone_message_read(message_id: str, request: Request) -> Any:
        by = "desk"
        if _owner_or_agent(request) is None:
            if await _device(request) is None:
                return _unauthorized()
            by = "phone"
        return await _call(lambda: _service().mark_read(message_id, by=by))

    @router.post("/api/phone/messages/{message_id}/decide")
    async def api_phone_message_decide(message_id: str, request: Request) -> Any:
        """JRN6: a press on a message's verb: his paired phone, or the owner."""
        principal, device = _principal(request), None
        if getattr(principal, "kind", None) is not PrincipalKind.OWNER:
            device = await _device(request)
            if device is None:
                return _unauthorized()
        body = await _body(request)
        return await _call(lambda: _service().decide(message_id, body.get("choice"), device=device))

    @router.post("/api/phone/messages/{message_id}/wait")
    async def api_phone_message_wait(message_id: str, request: Request) -> Any:
        principal = _principal(request)
        return await _call(lambda: _service().let_wait(principal, message_id))

    @router.post("/api/phone/calls")
    async def api_phone_call(request: Request) -> Any:
        principal = _owner_or_agent(request)
        if principal is None:
            return JSONResponse({"error": "owner_or_agent_required", "code": "owner_or_agent_required",
                                 "detail": "The desk or an agent places a call; a phone answers one."},
                                status_code=403)
        body = await _body(request)
        return await _call(lambda: _service().call(
            principal, reason=str(body.get("reason") or ""), context=str(body.get("context") or ""),
            urgent=bool(body.get("urgent")), program_step_id=body.get("program_step_id") or None,
        ), status=201)

    @router.get("/api/phone/calls")
    async def api_phone_calls() -> Any:
        return await _call(lambda: _service().calls())

    @router.get("/api/phone/calls/{call_id}")
    async def api_phone_call_get(call_id: str, request: Request) -> Any:
        if _owner_or_agent(request) is None and await _device(request) is None:
            return _unauthorized()
        return await _call(lambda: _service().get_call(call_id))

    @router.post("/api/phone/calls/{call_id}/{verb}")
    async def api_phone_call_verb(call_id: str, verb: str, request: Request) -> Any:
        principal = _owner_or_agent(request)
        device = None
        if principal is None:
            device = await _device(request)
            if device is None:
                return _unauthorized()
        service = _service()
        if verb == "accept":
            return await _call(lambda: service.accept(call_id, device=device))
        if verb == "decline":
            return await _call(lambda: service.decline(call_id, device=device))
        if verb == "end":
            return await _call(lambda: service.end(call_id, device=device))
        if verb in ("ring", "again") and device is None:
            owner = _principal(request)
            fn = service.ring_held if verb == "ring" else service.call_again
            return await _call(lambda: fn(owner, call_id))
        return JSONResponse({"error": "unknown_verb", "code": "unknown_verb",
                             "detail": "A call takes accept, decline, end, ring or again."}, status_code=404)

    @router.get("/api/phone/events")
    async def api_phone_events(request: Request) -> Any:
        if _owner_or_agent(request) is None and await _device(request) is None:
            return _unauthorized()
        after = int(request.query_params.get("after_seq") or 0)
        return await _call(lambda: _service().events.page(after))

    @router.get("/api/phone/status")
    async def api_phone_status(request: Request) -> Any:
        principal = _principal(request)
        return await _call(lambda: _service().status(principal))

    @router.get("/api/phone/push")
    async def api_phone_push(request: Request) -> Any:
        principal = _principal(request)
        return await _call(lambda: _service().push_key(principal))

    @router.put("/api/phone/push")
    async def api_phone_push_save(request: Request) -> Any:
        principal = _principal(request)
        body = await _body(request)
        return await _call(lambda: _service().save_push_key(principal, body))

    @router.post("/api/phone/push/test")
    async def api_phone_push_test(request: Request) -> Any:
        principal = _principal(request)
        return await _call(lambda: _service().test_push(principal))

    @router.websocket("/api/phone/ws")
    async def api_phone_ws(websocket: WebSocket) -> None:
        from ...phone.events import REVOKED
        from ...principals import derive_owner
        from ...timestamps import utc_now_iso

        service = _service()
        token = devs.bearer(websocket.headers.get("authorization")) or str(
            websocket.query_params.get("device_token") or "")
        device = await run_in_threadpool(service.authenticate, token) if token.count(".") == 2 else None
        owner = derive_owner(token or str(websocket.query_params.get("token") or ""),
                             getattr(websocket.app.state, "owner_token", ""))
        if device is None and owner is None:
            await websocket.close(code=4401)
            return
        await websocket.accept()
        loop = asyncio.get_running_loop()
        subscriber = service.events.subscribe(loop, device_id=(device or {}).get("id"))
        try:
            after = int(websocket.query_params.get("after_seq") or 0)
        except ValueError:
            after = 0
        try:
            last_seq = await run_in_threadpool(service.events.last_seq)
            hub = await run_in_threadpool(service.hub)
            await websocket.send_json({"type": "hello", "ts": utc_now_iso(),
                                       "data": {"hub_id": hub, "last_seq": last_seq, "server_ts": utc_now_iso()}})
            sent = after
            for event in await run_in_threadpool(service.events.replay, after):
                await websocket.send_json(event)
                sent = max(sent, int(event["seq"]))
            reader = asyncio.ensure_future(websocket.receive())
            while True:
                getter = asyncio.ensure_future(subscriber.queue.get())
                done, _ = await asyncio.wait({getter, reader}, timeout=PING_SECONDS,
                                             return_when=asyncio.FIRST_COMPLETED)
                if reader in done:
                    getter.cancel()
                    message = reader.result()
                    if message.get("type") == "websocket.disconnect":
                        break
                    reader = asyncio.ensure_future(websocket.receive())  # clients send nothing we read
                    continue
                if getter not in done:
                    getter.cancel()
                    await websocket.send_json({"type": "ping", "ts": utc_now_iso(), "data": {}})
                    continue
                event = getter.result()
                if event.get("type") == REVOKED["type"]:
                    reader.cancel()
                    await websocket.close(code=4401)
                    break
                if int(event.get("seq") or 0) <= sent:
                    continue
                await websocket.send_json(event)
                sent = int(event["seq"])
        except WebSocketDisconnect:
            pass
        except Exception as exc:
            log.info(f"phone socket closed: {exc}")
        finally:
            service.events.unsubscribe(subscriber)

    return router


__all__ = ["build_phone_router"]
