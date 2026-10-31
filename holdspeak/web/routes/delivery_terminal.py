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
- ``POST /api/delivery/terminal/node/results`` — the node-authenticated
  results leg joining node receipts/reconcile answers into the hub half.

Assembly is in-test/lazy (the delivery-router precedent); production
wiring happens in the web server, not here. Blocking work (tmux, SQLite)
runs off the event loop (the Phase-85 rule).
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Optional

import anyio
from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from ...db import get_observer
from ...logging_config import get_logger
from ...services.delivery_service import DeliveryService
from ..context import WebContext

log = get_logger("web.routes.delivery_terminal")

_STREAM_END = object()


def _next_stream_frame(iterator: Any) -> Any:
    """Call ``next`` off-loop without leaking StopIteration through await."""
    try:
        return next(iterator)
    except StopIteration:
        return _STREAM_END

NODE_TOKEN_HEADER = "X-HoldSpeak-Node-Token"

# Typed subscription absences → HTTP status (§7.1). The envelope's
# "status" field stays the contract's vocabulary either way.
_ABSENCE_HTTP = {
    "target_gone": 404,
    "generation_mismatch": 409,
    "stream_unavailable": 503,
    "unauthorized": 401,
}


class _TargetRequest(BaseModel):
    ref: str


class _SubscriptionRequest(BaseModel):
    target_id: str
    target_generation: str
    resume_sequence: Optional[int] = None
    last_hash: Optional[str] = None


class _LiveRequest(BaseModel):
    target_id: str
    target_generation: str
    stream_id: Optional[str] = None
    resume_sequence: Optional[int] = None


class _ResultsRequest(BaseModel):
    name: str
    results: list[dict[str, Any]] = []


def build_delivery_terminal_router(
    ctx: WebContext,
    *,
    service: Any = None,
    stream: Any = None,
    live: Any = None,
    targets: Any = None,
    workspace: Any = None,
    link: Any = None,
    hub_db: Any = None,
    registry_path: Optional[Path] = None,
    launches_path: Optional[Path] = None,
    ledger_path: Optional[Path] = None,
    local_node_id: str = "local",
    mode_loader: Any = None,
) -> APIRouter:
    """Every keyword is a test seam (the delivery-router precedent).

    ``service``/``stream``/``targets`` accept pre-built HS-94-06 objects
    (tests inject fakes and clocks); absent, production defaults build
    lazily on first request over the hub database and the node ledger.
    ``link`` is the shared :class:`NodeLinkState` whose token store
    authenticates the node results leg.
    """
    delivery_service = DeliveryService(hub_db, observer=get_observer()) if hub_db is not None else ctx.delivery_service
    router = APIRouter()
    holder: dict[str, Any] = {
        "service": service,
        "stream": stream,
        "live": live,
        "targets": targets,
        "workspace": workspace,
        "link": link,
    }

    def _targets() -> Any:
        if holder["targets"] is None:
            from ...delivery.terminal import TerminalTargetRegistry

            holder["targets"] = TerminalTargetRegistry()
        return holder["targets"]

    def _stream() -> Any:
        if holder["stream"] is None:
            from ...delivery.terminal import TerminalStreamService

            holder["stream"] = TerminalStreamService(_targets())
        return holder["stream"]

    def _live() -> Any:
        if holder["live"] is None:
            if delivery_service is None:
                raise RuntimeError("DeliveryService must be supplied at application composition")
            holder["live"] = delivery_service.terminal_live_service(targets=_targets())
        return holder["live"]

    def _workspace() -> Any:
        if holder["workspace"] is None:
            if delivery_service is None:
                raise RuntimeError("DeliveryService must be supplied at application composition")
            workspace_args = {"targets": _targets(), "local_node_id": local_node_id}
            if registry_path is not None:
                workspace_args["registry_path"] = registry_path
            if launches_path is not None:
                workspace_args["launches_path"] = launches_path
            holder["workspace"] = delivery_service.terminal_workspace_service(**workspace_args)
        return holder["workspace"]

    def _service() -> Any:
        if holder["service"] is None:
            if delivery_service is None:
                raise RuntimeError("DeliveryService must be supplied at application composition")
            holder["service"] = delivery_service.command_service(
                targets=_targets(),
                ledger_path=ledger_path,
                local_node_id=local_node_id,
                mode_loader=mode_loader,
            )
            # Remote nodes claim their queued commands through the shared
            # node link; hook the claim source once the service exists.
            if holder["link"] is not None and getattr(
                holder["link"], "command_source", None
            ) is None:
                holder["link"].command_source = holder["service"].claim_for_node
        return holder["service"]

    def _refused(exc: Any) -> JSONResponse:
        reason = getattr(exc, "reason", "refused")
        status = 401 if reason == "unauthorized" else 400
        return JSONResponse(
            {"ok": False, "error": reason, "detail": str(exc)}, status_code=status
        )

    @router.post("/api/delivery/terminal/targets")
    async def api_terminal_target(body: _TargetRequest) -> Any:
        """Issue/refresh the immutable target for a pane ref. The
        response is the ONLY way a client learns a target_id — commands
        and subscriptions never accept a raw pane selector."""
        try:
            issued = await asyncio.to_thread(_targets().issue, body.ref)
        except Exception as exc:
            log.error(f"target issue failure: {exc}")
            return JSONResponse({"error": "terminal_target_failure"}, status_code=500)
        if issued["status"] != "issued":
            status = 404 if issued["status"] == "pane_gone" else 503
            return JSONResponse(issued, status_code=status)
        issued["node_id"] = local_node_id
        return issued

    @router.get("/api/delivery/terminal/sessions")
    async def api_terminal_sessions() -> Any:
        """List current local terminal sessions from live tmux panes.

        Discovery is a read-only projection. Blocking tmux and hook-registry
        reads run off the event loop; an unclassified shell is still a useful
        ``live`` pane and is never presented as an agent state.
        """
        try:
            out = await asyncio.to_thread(_workspace().discover)
        except Exception as exc:
            log.error(f"terminal session discovery failure: {exc}")
            return JSONResponse(
                {"status": "error", "detail": "terminal session discovery failed", "sessions": []},
                status_code=500,
            )
        return JSONResponse(out)

    @router.post("/api/delivery/terminal/subscriptions")
    async def api_terminal_subscribe(body: _SubscriptionRequest) -> Any:
        try:
            out = await asyncio.to_thread(
                _stream().read,
                body.target_id,
                body.target_generation,
                resume_sequence=body.resume_sequence,
                last_hash=body.last_hash,
            )
        except Exception as exc:
            log.error(f"terminal subscription failure: {exc}")
            return JSONResponse(
                {"error": "terminal_stream_failure"}, status_code=500
            )
        status = _ABSENCE_HTTP.get(out.get("status"))
        return JSONResponse(out, status_code=status or 200)

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
            subscription = await asyncio.to_thread(
                _live().subscribe,
                body.target_id,
                body.target_generation,
                stream_id=body.stream_id,
                resume_sequence=body.resume_sequence,
            )
        except Exception as exc:
            status_name = getattr(exc, "status", "stream_unavailable")
            status_code = _ABSENCE_HTTP.get(status_name, 503)
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
        operation = body.get("operation") or {}
        principal = getattr(
            request.state, "principal", UNAUTHENTICATED
        )
        try:
            if (
                operation.get("family") == "coder_steering"
                and operation.get("verb") in {"terminal.text", "terminal.keys"}
            ):
                out = await asyncio.to_thread(
                    _service().submit_process_input, body, principal
                )
            elif (
                operation.get("family") == "coder_steering"
                and operation.get("verb") == "process.resize@1"
            ):
                out = await asyncio.to_thread(
                    _service().submit_process_resize, body, principal
                )
            else:
                out = await asyncio.to_thread(_service().submit, body)
        except CommandRefused as exc:
            return _refused(exc)
        except Exception as exc:
            log.error(f"terminal command failure: {exc}")
            return JSONResponse(
                {"error": "terminal_command_failure"}, status_code=500
            )
        return JSONResponse(out)

    @router.get("/api/delivery/terminal/commands/{command_id}")
    async def api_terminal_receipt(command_id: str) -> Any:
        try:
            out = await asyncio.to_thread(_service().receipt, command_id)
        except Exception as exc:
            log.error(f"terminal receipt failure: {exc}")
            return JSONResponse(
                {"error": "terminal_receipt_failure"}, status_code=500
            )
        if out is None:
            return JSONResponse(
                {"error": "unknown_command_id"}, status_code=404
            )
        return JSONResponse(out)

    @router.post("/api/delivery/terminal/node/results")
    async def api_terminal_node_results(
        body: _ResultsRequest,
        x_holdspeak_node_token: Optional[str] = Header(default=None),
    ) -> Any:
        """The node's results leg: receipts and reconcile answers for
        claimed commands. Authenticated with the node's OWN token via
        the shared node-link token store — never the browser token."""
        from ...delivery.node_link import NodeLinkError

        if holder["link"] is None:
            return JSONResponse(
                {"ok": False, "error": "node_link_unwired"}, status_code=503
            )
        try:
            # The link's own auth seam: per-node token, browser-token
            # equality refused first (§12.1 distinctness).
            node_id = holder["link"]._verify(body.name, x_holdspeak_node_token)
            out = await asyncio.to_thread(
                _service().record_results, node_id, body.results
            )
        except NodeLinkError as exc:
            return JSONResponse(
                {"ok": False, "error": exc.reason, "detail": str(exc)},
                status_code=401,
            )
        except Exception as exc:
            log.error(f"terminal node results failure: {exc}")
            return JSONResponse(
                {"ok": False, "error": "terminal_results_failure"}, status_code=500
            )
        return JSONResponse(out)

    return router
