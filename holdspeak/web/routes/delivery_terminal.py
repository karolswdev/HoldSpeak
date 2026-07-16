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
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ...logging_config import get_logger
from ..context import WebContext

log = get_logger("web.routes.delivery_terminal")

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


class _ResultsRequest(BaseModel):
    name: str
    results: list[dict[str, Any]] = []


def build_delivery_terminal_router(
    ctx: WebContext,
    *,
    service: Any = None,
    stream: Any = None,
    targets: Any = None,
    link: Any = None,
    hub_db: Any = None,
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
    _ = ctx
    router = APIRouter()
    holder: dict[str, Any] = {
        "service": service,
        "stream": stream,
        "targets": targets,
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

    def _service() -> Any:
        if holder["service"] is None:
            from ...db import get_database
            from ...db.delivery_receipts import NodeReceiptLedger
            from ...delivery.commands import HubCommandService, NodeCommandProcessor

            db = hub_db if hub_db is not None else get_database()
            processor = NodeCommandProcessor(
                node_id=local_node_id,
                targets=_targets(),
                ledger=NodeReceiptLedger(ledger_path),
            )
            holder["service"] = HubCommandService(
                repo=db.delivery_receipts,
                processor=processor,
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

    @router.post("/api/delivery/terminal/commands")
    async def api_terminal_command(payload: Optional[dict[str, Any]] = None) -> Any:
        from ...delivery.commands import CommandRefused

        body = payload if isinstance(payload, dict) else {}
        try:
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
