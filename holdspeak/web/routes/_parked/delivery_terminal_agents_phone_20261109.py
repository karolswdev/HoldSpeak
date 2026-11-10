# PARKED: replaced by declared operations; kept for history.
"""Delivery terminal routes (HS-94-06).

The hub HTTP surface over PLATFORM-CONTRACT §7/§8:

- ``POST /api/delivery/terminal/targets`` — issue/refresh the immutable
  node-issued target for a pane ref (``pane:%N`` compat included).
- ``POST /api/delivery/terminal/subscriptions`` — one subscription poll:
  snapshot / sequenced ANSI-preserving deltas / ``not_modified`` /
  ``resync_required``, or a typed absence (``target_gone``,
  ``generation_mismatch``, ``stream_unavailable``). Poll-based delivery,
  consistent with the node link's long-poll transport.
- ``POST /api/delivery/terminal/commands`` — submit one command intent;
  the hub derives the whole authority block (a client-supplied
  ``authority`` refuses by name) and executes locally through the
  chokepoints, or queues for the remote node's claim leg.
- ``GET  /api/delivery/terminal/commands/{command_id}`` — the aggregate
  Receipt, reconciled by command_id (never a blind retry).

Assembly is in-test/lazy (the delivery-router precedent); production
wiring happens in the web server, not here. Blocking work (tmux, SQLite)
runs off the event loop (the Phase-85 rule).
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Optional

import anyio
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from ...logging_config import get_logger
from ...services.delivery_service import TERMINAL_ABSENCE_HTTP
from ..context import WebContext
from . import delivery_declared
from ._mount import mount_router

log = get_logger("web.routes.delivery_terminal")

_STREAM_END = object()


def _next_stream_frame(iterator: Any) -> Any:
    """Call ``next`` off-loop without leaking StopIteration through await."""
    try:
        return next(iterator)
    except StopIteration:
        return _STREAM_END


class _LiveRequest(BaseModel):
    target_id: str
    target_generation: str
    stream_id: Optional[str] = None
    resume_sequence: Optional[int] = None


def build_delivery_terminal_router(ctx: WebContext) -> APIRouter:
    """The terminal routes. ``sessions`` and ``subscriptions`` are produced
    from the ``delivery.terminal_sessions`` and ``delivery.terminal_read``
    rows. Two stay written here: ``live`` answers an NDJSON stream, and
    ``commands`` runs keys and process commands in a terminal (a spawn
    among them). The targets, the stream, the commands and their test seams
    live on ``ctx.delivery_service`` (``DeliveryService.configure``)."""
    delivery_service = delivery_declared.delivery_of(ctx)
    router = APIRouter()
    mount_router(router, delivery_declared.router(
        ctx, ("delivery.terminal_sessions", "delivery.terminal_read"), module=__name__,
    ))

    def _refused(exc: Any) -> JSONResponse:
        reason = getattr(exc, "reason", "refused")
        status = 401 if reason == "unauthorized" else 400
        return JSONResponse(
            {"ok": False, "error": reason, "detail": str(exc)}, status_code=status
        )

    @router.post(
        "/api/delivery/terminal/live",
        response_class=StreamingResponse,
        response_model=None,
        responses={
            200: {
                "description": "Continuous terminal frames as newline-delimited JSON",
                "content": {"application/x-ndjson": {"schema": {"type": "string"}}},
            },
            401: {"description": "Authentication or target authority required"},
            404: {"description": "Target is gone"},
            409: {"description": "Target generation changed"},
            503: {"description": "Local stream unavailable"},
        },
    )
    async def api_terminal_live(body: _LiveRequest) -> Any:
        """Continuous local output as one authenticated NDJSON stream.

        ``subscribe`` performs the initial immutable-target proof and the
        control-mode startup off the event loop.  Each blocking iterator step
        runs in a cancellable worker, so a blocked PTY read never stalls the
        Desk loop and disconnect wakes the subscription promptly.  Closing
        the iterator detaches only the control client.
        """
        try:
            subscription = await asyncio.to_thread(lambda: delivery_service.terminal_subscribe(
                body.target_id,
                body.target_generation,
                stream_id=body.stream_id,
                resume_sequence=body.resume_sequence,
            ))
        except Exception as exc:
            status_name = getattr(exc, "status", "stream_unavailable")
            status_code = TERMINAL_ABSENCE_HTTP.get(status_name, 503)
            detail = getattr(exc, "detail", str(exc))
            return JSONResponse(
                {"status": status_name, "detail": detail}, status_code=status_code
            )

        async def lines() -> Any:
            iterator = iter(subscription.frames())
            try:
                while True:
                    frame = await anyio.to_thread.run_sync(
                        _next_stream_frame,
                        iterator,
                        abandon_on_cancel=True,
                    )
                    if frame is _STREAM_END:
                        return
                    yield (json.dumps(frame, separators=(",", ":")) + "\n").encode(
                        "utf-8"
                    )
            finally:
                subscription.close()

        return StreamingResponse(lines(), media_type="application/x-ndjson")

    @router.post("/api/delivery/terminal/commands")
    async def api_terminal_command(
        request: Request, payload: Optional[dict[str, Any]] = None
    ) -> Any:
        from ...delivery.commands import CommandRefused
        from ...principals import UNAUTHENTICATED

        body = payload if isinstance(payload, dict) else {}
        principal = getattr(
            request.state, "principal", UNAUTHENTICATED
        )
        try:
            out = await asyncio.to_thread(lambda: delivery_service.terminal_command(principal, body))
        except CommandRefused as exc:
            return _refused(exc)
        except Exception as exc:
            log.error(f"terminal command failure: {exc}")
            return JSONResponse(
                {"error": "terminal_command_failure"}, status_code=500
            )
        return JSONResponse(out)

    return router
