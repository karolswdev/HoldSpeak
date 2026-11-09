"""PARKED 20261108 (evening, the unreached-routes census): routes no client calls.

Parked from ``holdspeak/web/routes/delivery_node.py``: POST /api/delivery/node/disconnect.
Not imported. Kept for history; restore with ``git revert`` of the parking commit.
"""
from __future__ import annotations
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


from pathlib import Path
from threading import Lock
from typing import Any, Optional

from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ....logging_config import get_logger
from ...context import WebContext

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




def parked_build_delivery_node_router(
    ctx: WebContext,
    *,
    link: Any = None,
    token_store_path: Optional[Path] = None,
    web_token: Optional[str] = None,
    legacy_env: Optional[dict] = None,
) -> APIRouter:
    router = APIRouter()

    @router.post("/api/delivery/node/disconnect")
    def api_node_disconnect(
        body: _DisconnectRequest,
        x_holdspeak_node_token: Optional[str] = Header(default=None),
    ) -> Any:
        return _guarded(
            lambda: _link().disconnect(body.name, x_holdspeak_node_token)
        )

    return router
