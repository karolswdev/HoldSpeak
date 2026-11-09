"""Delivery Runtime routes (HS-94-02).

The §10 hub API's read foundation: a cached coherent snapshot, the
source registry view, server-resolved source registration, and
cursor-addressed event replay. Two rules ride every handler:

- polling never triggers a fresh dw/gh process (§11) — the snapshot
  is cached behind the collector's bounded-age policy, and event
  replay serves the retained buffers;
- blocking collection runs off the event loop via
  ``asyncio.to_thread`` (the Phase-85 rule).

The collector/registry pair builds lazily on first request (on
``DeliveryService``) so assembling the app (including the API-surface
generator) has no side effects — no registry file writes, no git
subprocesses. 2026-11-09 (one contract): the routes are produced from
the ``delivery.snapshot`` / ``delivery.sources`` /
``delivery.source_register`` rows (``holdspeak/delivery_operations.py``).

The legacy `/api/missioncontrol/*` surface stays on the untouched
bridge; this router runs alongside it (§10 compatibility rule).
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from ...principals import UNAUTHENTICATED
from ..context import WebContext
from . import delivery_declared


def build_delivery_router(ctx: WebContext) -> APIRouter:
    """The read model's routes; the collector and its test seams live on
    ``ctx.delivery_service`` (``DeliveryService.configure``)."""
    registry = delivery_declared.registry_for(ctx)

    def snapshot_handler(descriptor: Any) -> Any:
        async def api_delivery_snapshot(request: Request) -> Any:
            """The coherent cached read model (§4.4). ETag is the snapshot
            revision; a matching If-None-Match answers 304 without a body."""
            principal = getattr(request.state, "principal", UNAUTHENTICATED)
            try:
                snap = await run_in_threadpool(lambda: registry().invoke(principal, descriptor.name, {}, shape="web"))
            except Exception as exc:
                return delivery_declared.refused(descriptor.name, exc)
            revision = str(snap.get("revision") or "")
            if revision and request.headers.get("if-none-match") == revision:
                return Response(status_code=304, headers={"ETag": revision})
            return JSONResponse(snap, headers={"ETag": revision})

        return api_delivery_snapshot

    return delivery_declared.router(
        ctx, ("delivery.snapshot", "delivery.sources", "delivery.source_register"), module=__name__,
        hand_written={"delivery.snapshot": snapshot_handler},
    )
