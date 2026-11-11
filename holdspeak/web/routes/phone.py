"""Phone transport (2026-10-28, design §10); the work is :mod:`holdspeak.phone.service`.

The owner's verbs (devices, revoke, wait, calls, ring, again, push) are
produced from ``holdspeak/phone_operations.py``. Written here: pair (it holds
the address he pressed Pair on), the pairing redeem (it holds the address the
phone reached; the two must match), the routes a paired phone
calls (messages, read, decide, a call, accept|decline|end, events, the socket),
sending a message, placing a call and the status.

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

from ... import operations
from ...logging_config import get_logger
from ...phone import devices as devs
from ...phone_operations import PRODUCED
from ...principals import UNAUTHENTICATED, PrincipalKind
from ...services.errors import ServiceError
from ..context import WebContext
from ..operation_routes import operation_router
from ._mount import mount_router

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
    if getattr(_principal(request), "kind", None) is PrincipalKind.AGENT:
        return None
    registry = operations.bind_available({"phone_service": _service()})
    return await run_in_threadpool(lambda: registry.invoke(_principal(request) or UNAUTHENTICATED,
        "phone.authenticate", {}, held={"token": token}))


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
    except operations.OperationRefused as exc:
        return JSONResponse({"error": exc.code, "code": exc.code, "detail": exc.detail}, status_code=400)
    except Exception as exc:
        log.error(f"phone route failed: {exc}", exc_info=True)
        return JSONResponse({"error": "phone_failed", "code": "phone_failed",
                             "detail": "The phone service failed. Nothing changed. The log names the cause."},
                            status_code=500)


def build_phone_router(ctx: WebContext) -> APIRouter:
    """The owner's verbs are produced from ``holdspeak/phone_operations.py``; a
    route a paired phone calls authenticates the device here, then invokes its
    declared operation with the device HELD."""
    router = APIRouter()

    def registry() -> operations.OperationRegistry:
        return operations.for_context(ctx, phone_service=lambda: operations.LIVE_PHONE_SERVICE)

    def invoke(principal: Any, name: str, args: dict[str, Any], *, status: int = 200, **held: Any) -> Any:
        return _call(lambda: registry().invoke(principal, name, args, held=held or None), status=status)

    @router.post("/api/phone/pair")
    async def api_phone_pair(request: Request) -> Any:
        base = str(request.base_url).rstrip("/")
        return await invoke(_principal(request), "phone.pair", {}, status=201, hub_urls=[base])

    @router.post("/api/phone/devices")
    async def api_phone_devices_pair(request: Request) -> Any:
        # The address the phone reached; the pairing token must have been made on it.
        origin = str(request.base_url).rstrip("/")
        body = {key: value for key, value in (await _body(request)).items() if key != "origin"}
        return await invoke(_principal(request) or UNAUTHENTICATED, "phone.redeem", body, status=201, origin=origin)

    by_name = {op.name: op for op in operations.PHONE_OPERATIONS}
    mount_router(router, operation_router([by_name[name] for name in PRODUCED], registry, _call,
                                          module=__name__))

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
        return await invoke(_principal(request), "phone.messages", {"after_seq": after})

    @router.post("/api/phone/messages/{message_id}/read")
    async def api_phone_message_read(message_id: str, request: Request) -> Any:
        device = None
        if getattr(_principal(request), "kind", None) is not PrincipalKind.OWNER:
            device = await _device(request)
            if device is None:
                return _unauthorized()
        return await invoke(_principal(request), "phone.mark_read", {"message_id": message_id}, device=device)

    @router.post("/api/phone/messages/{message_id}/decide")
    async def api_phone_message_decide(message_id: str, request: Request) -> Any:
        """JRN6: a press on a message's verb: his paired phone, or the owner."""
        principal, device = _principal(request), None
        if getattr(principal, "kind", None) is not PrincipalKind.OWNER:
            device = await _device(request)
            if device is None:
                return _unauthorized()
        body = await _body(request)
        return await invoke(principal, "phone.decide", {"message_id": message_id, "choice": body.get("choice"), "expected_commit_binding": body.get("expected_commit_binding")},
                            device=device)

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

    @router.get("/api/phone/calls/{call_id}")
    async def api_phone_call_get(call_id: str, request: Request) -> Any:
        if _owner_or_agent(request) is None and await _device(request) is None:
            return _unauthorized()
        return await invoke(_principal(request), "phone.get_call", {"call_id": call_id})

    def answer_verb(verb: str) -> None:
        async def endpoint(call_id: str, request: Request) -> Any:
            device = None
            if getattr(_principal(request), "kind", None) is not PrincipalKind.OWNER:
                device = await _device(request)
                if device is None:
                    return _unauthorized()
            return await invoke(_principal(request), f"phone.{verb}", {"call_id": call_id}, device=device)

        endpoint.__name__ = endpoint.__qualname__ = f"api_phone_call_{verb}"
        router.add_api_route(f"/api/phone/calls/{{call_id}}/{verb}", endpoint, methods=["POST"])

    for verb in ("accept", "decline", "end"):
        answer_verb(verb)

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

    @router.websocket("/api/phone/ws")
    async def api_phone_ws(websocket: WebSocket) -> None:
        from ...phone.events import REVOKED
        from ...principals import derive_owner
        from ...timestamps import utc_now_iso

        service = _service()
        token = devs.bearer(websocket.headers.get("authorization")) or str(
            websocket.query_params.get("device_token") or "")
        device = await run_in_threadpool(lambda: registry().invoke(UNAUTHENTICATED, "phone.authenticate", {},
            held={"token": token})) if token.count(".") == 2 else None
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
            hub = await run_in_threadpool(lambda: registry().invoke(owner or UNAUTHENTICATED, "phone.hub", {},
                held={"device": device}))
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
