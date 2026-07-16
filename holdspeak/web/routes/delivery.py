"""Delivery Runtime routes (HS-94-02).

The §10 hub API's read foundation: a cached coherent snapshot, the
source registry view, server-resolved source registration, and
cursor-addressed event replay. Two rules ride every handler:

- polling never triggers a fresh dw/gh process (§11) — the snapshot
  is cached behind the collector's bounded-age policy, and event
  replay serves the retained buffers;
- blocking collection runs off the event loop via
  ``asyncio.to_thread`` (the Phase-85 rule).

The collector/registry pair builds lazily on first request so
assembling the app (including the API-surface generator) has no
side effects — no registry file writes, no git subprocesses.

The legacy `/api/missioncontrol/*` surface stays on the untouched
bridge; this router runs alongside it (§10 compatibility rule).
"""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ...logging_config import get_logger
from ..context import WebContext

log = get_logger("web.routes.delivery")


def _classified_500(exc: Exception, detail: str) -> JSONResponse:
    """§12.3: node errors returned to clients are classified and
    bounded — the exception (which may carry paths) goes to the log,
    never the wire."""
    log.error(f"{detail}: {exc}")
    return JSONResponse({"error": detail}, status_code=500)


class _RegisterSourceRequest(BaseModel):
    path: str
    label: Optional[str] = None


def build_delivery_router(
    ctx: WebContext,
    *,
    collector: Any = None,
    registry_path: Optional[Path] = None,
    map_path: Optional[Path] = None,
    runner: Any = None,
    dw_argv_factory: Any = None,
    max_age_seconds: float = 15.0,
) -> APIRouter:
    """Every keyword is a test seam (the mission-control precedent);
    production uses the defaults. ``ctx`` is accepted for parity with
    the other route factories (belt-frame emission joins in HS-94-04)."""
    _ = ctx
    router = APIRouter()
    holder: dict[str, Any] = {"collector": collector}

    def _collector() -> Any:
        if holder["collector"] is None:
            from ...delivery import DeliveryCollector, DeliveryRegistry

            registry = DeliveryRegistry(registry_path, map_path=map_path)
            holder["collector"] = DeliveryCollector(
                registry,
                runner=runner,
                dw_argv_factory=dw_argv_factory,
                max_age_seconds=max_age_seconds,
            )
        return holder["collector"]

    @router.get("/api/delivery/snapshot")
    async def api_delivery_snapshot(request: Request) -> Any:
        """The coherent cached read model (§4.4). ETag is the snapshot
        revision; a matching If-None-Match answers 304 without a body."""
        try:
            snap = await asyncio.to_thread(lambda: _collector().snapshot())
            revision = str(snap.get("revision") or "")
            if revision and request.headers.get("if-none-match") == revision:
                return Response(status_code=304, headers={"ETag": revision})
            return JSONResponse(snap, headers={"ETag": revision})
        except Exception as exc:
            return _classified_500(exc, "delivery snapshot failed")

    @router.get("/api/delivery/sources")
    async def api_delivery_sources() -> Any:
        """Registry + freshness view: labels, opaque IDs, typed
        statuses. Never shells out."""
        try:
            return await asyncio.to_thread(lambda: _collector().sources_view())
        except Exception as exc:
            return _classified_500(exc, "delivery sources read failed")

    @router.post("/api/delivery/sources")
    async def api_delivery_register_source(body: _RegisterSourceRequest) -> Any:
        """Register a source by path. The server resolves and
        validates (§10: config flow, not a trusted raw path); the
        response carries wire shapes only."""
        try:
            from ...delivery.registry import RegistryError

            try:
                result = await asyncio.to_thread(
                    _collector().register_source, body.path, label=body.label
                )
            except RegistryError as refusal:
                return JSONResponse(
                    {"success": False, "error": str(refusal)}, status_code=400
                )
            return {"success": True, **result}
        except Exception as exc:
            return _classified_500(exc, "delivery source registration failed")

    @router.get("/api/delivery/events")
    async def api_delivery_events(after: str = "") -> Any:
        """Replay rail events from the composed cursor — served from
        the collector's retained buffers, never a fresh dw run per
        poll. The first read after boot performs the initial
        collection."""
        try:
            def _read() -> Any:
                c = _collector()
                if not c.has_collected:
                    c.snapshot()  # initial collection only
                return c.events_after(after)

            return await asyncio.to_thread(_read)
        except Exception as exc:
            return _classified_500(exc, "delivery events read failed")

    return router
