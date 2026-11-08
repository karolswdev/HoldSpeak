"""PARKED 20261108 (subtraction day, Lane R): routes no client reads.

Parked from ``holdspeak/web/routes/delivery_node.py``: GET /api/delivery/node/commands.
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
    from ....delivery.node_link import AUTH_REASONS

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
    """Every keyword is a test seam (the delivery-router precedent).

    ``link`` accepts a pre-built :class:`NodeLinkState` so the hub can
    share one state instance between this router and its embedded
    local-node adapter; absent, one builds lazily on first request
    (assembling the app stays side-effect free).
    """
    _ = ctx
    router = APIRouter()
    holder: dict[str, Any] = {"link": link}
    holder_lock = Lock()
    link_lock = Lock()

    def _link() -> Any:
        if holder["link"] is None:
            with holder_lock:
                if holder["link"] is None:
                    from ....delivery.node_link import NodeLinkState, NodeTokenStore

                    holder["link"] = NodeLinkState(
                        NodeTokenStore(token_store_path), web_token=web_token
                    )
        return holder["link"]

    def _guarded(fn: Any) -> Any:
        from ....delivery.node_link import NodeLinkError

        try:
            with link_lock:
                return fn()
        except NodeLinkError as exc:
            return _refusal(exc)
        except Exception as exc:  # §12.3: classified, never raw
            log.error(f"node link failure: {exc}")
            return JSONResponse(
                {"ok": False, "error": "node_link_failure"}, status_code=500
            )

    @router.get("/api/delivery/node/commands")
    def api_node_commands(
        name: str = "",
        x_holdspeak_node_token: Optional[str] = Header(default=None),
    ) -> Any:
        """The command claim leg. HS-94-03 returns the empty envelope;
        the capability/protocol gate already refuses mismatched nodes
        by name while their observation keeps flowing."""
        return _guarded(lambda: _link().poll_commands(name, x_holdspeak_node_token))

    return router
