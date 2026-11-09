"""Delivery node-link routes (HS-94-03).

The hub end of the outbound node link (PLATFORM-CONTRACT §6): a node
authenticates every request with its OWN per-node token (the
``X-HoldSpeak-Node-Token`` header — never the browser token, §12.1),
introduces itself with hello, heartbeats every 5 s with optional
metadata-only event batches, and polls the command envelope. The
browser-facing ``/api/delivery/nodes`` projection exposes typed
liveness with last-seen retained — no tokens, URLs, or paths (§13).

Refusals are typed and bounded (§12.3): the ``reason`` field is
machine-readable; nothing on the wire echoes a secret, a path, or a
stack trace. Transport rationale (long-poll HTTP over the mesh
pattern instead of a raw WebSocket) is documented in
:mod:`holdspeak.delivery.node_link`.
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ...logging_config import get_logger
from ..context import WebContext
from . import delivery_declared
from ._mount import mount_router

log = get_logger("web.routes.delivery_node")

NODE_TOKEN_HEADER = "X-HoldSpeak-Node-Token"


class _HelloRequest(BaseModel):
    node_protocol: int
    name: str
    instance_id: str = ""
    capabilities: list[str] = []
    resume_cursor: Optional[int] = None
    node_wall_time: Optional[str] = None


class _HeartbeatRequest(BaseModel):
    name: str
    instance_id: Optional[str] = None
    events: list[dict[str, Any]] = []
    node_wall_time: Optional[str] = None


class _DisconnectRequest(BaseModel):
    name: str


def _refusal(exc: Any) -> JSONResponse:
    """Map a typed NodeLinkError onto a bounded wire refusal."""
    from ...delivery.node_link import AUTH_REASONS

    reason = getattr(exc, "reason", "refused")
    if reason in AUTH_REASONS:
        status = 401
    elif reason.startswith("event_"):
        status = 400
    else:
        status = 409  # hello_required / commands_disabled / already_paired
    return JSONResponse(
        {"ok": False, "error": reason, "detail": str(exc)}, status_code=status
    )


def build_delivery_node_router(ctx: WebContext) -> APIRouter:
    """The node link's routes. ``hello`` and ``heartbeat`` stay written here:
    node-token traffic from ``holdspeak node serve`` (§12.1), never a tool.
    ``/api/delivery/nodes`` is produced from the ``delivery.nodes`` row. The
    one shared :class:`NodeLinkState` (the hub's, or one built lazily) and
    its lock live on ``ctx.delivery_service`` (``DeliveryService.configure``)."""
    delivery_service = delivery_declared.delivery_of(ctx)
    router = APIRouter()

    def _guarded(fn: Any) -> Any:
        from ...delivery.node_link import NodeLinkError

        try:
            return delivery_service.node_call(fn)
        except NodeLinkError as exc:
            return _refusal(exc)
        except Exception as exc:  # §12.3: classified, never raw
            log.error(f"node link failure: {exc}")
            return JSONResponse(
                {"ok": False, "error": "node_link_failure"}, status_code=500
            )

    @router.post("/api/delivery/node/hello")
    def api_node_hello(
        body: _HelloRequest,
        x_holdspeak_node_token: Optional[str] = Header(default=None),
    ) -> Any:
        return _guarded(
            lambda link: link.hello(
                body.name,
                x_holdspeak_node_token,
                node_protocol=body.node_protocol,
                instance_id=body.instance_id,
                capabilities=body.capabilities,
                resume_cursor=body.resume_cursor,
                node_wall_time=body.node_wall_time,
            )
        )

    @router.post("/api/delivery/node/heartbeat")
    def api_node_heartbeat(
        body: _HeartbeatRequest,
        x_holdspeak_node_token: Optional[str] = Header(default=None),
    ) -> Any:
        return _guarded(
            lambda link: link.heartbeat(
                body.name,
                x_holdspeak_node_token,
                instance_id=body.instance_id,
                events=body.events,
                node_wall_time=body.node_wall_time,
            )
        )

    mount_router(router, delivery_declared.router(ctx, ("delivery.nodes",), module=__name__))
    return router
