"""PHILO-10-01: the Send over HTTP -- parse and serialize only; each route IS its declared operation.

GET    /api/channels/destinations                      channel.destinations
POST   /api/channels/destinations                      channel.save_destination
DELETE /api/channels/destinations/{destination_id}     channel.remove_destination (parks)
POST   /api/channels/destinations/{destination_id}/check  channel.check_destination
POST   /api/channels/preview                           channel.preview
POST   /api/channels/sends                             channel.prepare
POST   /api/channels/sends/{send_id}/discard           channel.discard
POST   /api/channels/send                              channel.send
GET    /api/channels/sends                             channel.sends
PUT    /api/channels/email-keys/{key_ref}              channel.save_email_key (the key HELD, never an argument)

An admitted route answers with its ``operation_id`` and terminal ``receipt``; a
refusal of an admitted operation carries them (``_room_kernel``).

PHILO-10-02 GATE 2 (Codex Astra r2 on #692): an operation that declares
blocking I/O (``OperationDescriptor.blocking_io``: a CLI send, an identity
read) runs OFF the event loop (the threadpool), so it never stalls the hub's
other requests.
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from ... import operations
from ...logging_config import get_logger
from ...operations import OperationRefused
from ...principals import UNAUTHENTICATED
from ...services.errors import NotFound, ServiceError, ValidationError
from ..context import WebContext
from ..runtime_support import error_500
from ._room_kernel import body_or_refusal, kernel_fields, kernel_refusal, refusal_fields

log = get_logger("web.routes.channels")


def build_channels_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    def principal(request: Request) -> Any:
        return getattr(request.state, "principal", UNAUTHENTICATED)

    def ops() -> Any:
        return operations.for_context(ctx)

    async def call(request: Request, name: str, args: dict[str, Any],
                   held: Optional[dict[str, Any]] = None) -> JSONResponse:
        # Off the loop exactly when the operation declares blocking I/O (a CLI or email send, an identity
        # read, the keychain).
        if ops().descriptor(name).blocking_io:
            return await run_in_threadpool(call_sync, request, name, args, held)
        return call_sync(request, name, args, held)

    def call_sync(request: Request, name: str, args: dict[str, Any],
                  held: Optional[dict[str, Any]] = None) -> JSONResponse:
        try:
            result, kernel = (ops().invoke_receipted(principal(request), name, args) if held is None
                              else ops().invoke_receipted(principal(request), name, args, held=held))
            return JSONResponse({**result, **kernel_fields(kernel)})
        except OperationRefused as exc:
            return JSONResponse({"success": False, "code": exc.code, "error_code": exc.code, "message": exc.detail,
                                 **refusal_fields(exc)}, status_code=400)
        except ServiceError as exc:
            if (refused := kernel_refusal(exc)) is not None:
                return refused
            status = (404 if isinstance(exc, NotFound)
                      else int(exc.context.get("status") or (400 if isinstance(exc, ValidationError) else 409)))
            return JSONResponse({"success": False, "code": exc.code, "error_code": exc.code, "message": exc.detail,
                                 **refusal_fields(exc)}, status_code=status)
        except Exception as exc:
            return error_500(exc, log, f"{name} failed")

    async def body(request: Request, name: str, *, optional: bool = False) -> tuple[Optional[dict[str, Any]], Any]:
        return await body_or_refusal(request, ops(), principal(request), name, optional=optional)

    def path_refusal(request: Request, name: str, field: str, data: dict[str, Any]) -> Optional[JSONResponse]:
        if field not in data:
            return None
        exc = OperationRefused("invalid_arguments", name, f"Invalid arguments for {name}: {field} comes from the path")
        kernel = ops().refuse(principal(request), name, "invalid_arguments", data)
        return JSONResponse({"success": False, "code": "invalid_arguments", "message": exc.detail,
                             **kernel_fields(kernel)}, status_code=400)

    @router.get("/api/channels/destinations")
    async def api_channel_destinations(request: Request, include_parked: bool = False) -> Any:
        return await call(request, "channel.destinations", {"include_parked": include_parked} if include_parked else {})

    @router.post("/api/channels/destinations")
    async def api_channel_save_destination(request: Request) -> Any:
        data, refused = await body(request, "channel.save_destination")
        return refused if refused is not None else await call(request, "channel.save_destination", data)

    @router.delete("/api/channels/destinations/{destination_id}")
    async def api_channel_remove_destination(destination_id: str, request: Request) -> Any:
        data, refused = await body(request, "channel.remove_destination", optional=True)
        if refused is not None:
            return refused
        if (bad := path_refusal(request, "channel.remove_destination", "destination_id", data)) is not None:
            return bad
        return await call(request, "channel.remove_destination", {**data, "destination_id": destination_id})

    @router.post("/api/channels/destinations/{destination_id}/check")
    async def api_channel_check_destination(destination_id: str, request: Request) -> Any:
        return await call(request, "channel.check_destination", {"destination_id": destination_id})

    @router.post("/api/channels/preview")
    async def api_channel_preview(request: Request) -> Any:
        data, refused = await body(request, "channel.preview")
        return refused if refused is not None else await call(request, "channel.preview", data)

    @router.post("/api/channels/sends")
    async def api_channel_prepare(request: Request) -> Any:
        data, refused = await body(request, "channel.prepare")
        return refused if refused is not None else await call(request, "channel.prepare", data)

    @router.post("/api/channels/sends/{send_id}/discard")
    async def api_channel_discard(send_id: str, request: Request) -> Any:
        data, refused = await body(request, "channel.discard", optional=True)
        if refused is not None:
            return refused
        if (bad := path_refusal(request, "channel.discard", "send_id", data)) is not None:
            return bad
        return await call(request, "channel.discard", {**data, "send_id": send_id})

    @router.post("/api/channels/send")
    async def api_channel_send(request: Request) -> Any:
        data, refused = await body(request, "channel.send")
        return refused if refused is not None else await call(request, "channel.send", data)

    @router.get("/api/channels/sends")
    async def api_channel_sends(request: Request, document_ref: Optional[str] = None,
                                send_id: Optional[str] = None) -> Any:
        args = {k: v for k, v in (("document_ref", document_ref), ("send_id", send_id)) if v}
        return await call(request, "channel.sends", args)

    @router.put("/api/channels/email-keys/{key_ref}")
    async def api_channel_save_email_key(key_ref: str, request: Request) -> Any:
        # The key is HELD: taken out of the body before anything validates or
        # journals the arguments (PHILO-10-03 key custody).
        data, refused = await body(request, "channel.save_email_key")
        if refused is not None:
            return refused
        key = data.pop("api_key", None)
        if (bad := path_refusal(request, "channel.save_email_key", "key_ref", data)) is not None:
            return bad
        return await call(request, "channel.save_email_key", {**data, "key_ref": key_ref}, held={"api_key": key})

    return router
