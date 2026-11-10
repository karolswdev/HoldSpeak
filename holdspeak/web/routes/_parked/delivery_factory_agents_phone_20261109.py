# PARKED: replaced by declared operations; kept for history.
"""Remote factory + Story-bound agent launch routes (HS-94-07).

The §9/§10 factory surface:

- ``GET  /api/delivery/factory/profiles`` — the node-configured Agent
  Profiles (fixed executables + allow-listed option slots). A client
  selects a ``profile_id``; it can never supply an executable, argv,
  or shell string (the service refuses each BY NAME).
- ``POST /api/delivery/factory/launch`` — one typed agent.launch:
  {profile, source, worktree, story} → worktree-create receipt (mode
  ``new``), spawn receipt, immutable target, ONE Work attempt, launch
  record. The body is taken raw so a smuggled execution field refuses
  by name instead of being silently stripped.
- ``GET  /api/delivery/factory/discover`` — panes/sessions as TARGETS
  (node + source/worktree + profile + immutable target handle); no
  pre-known ``pane:%N`` is ever required. Reads sweep rider claims and
  the registration timeout first (bounded, best-effort) so a launched
  agent appears bound — or honestly ``failed_to_register`` — without
  any client write.

Assembly is in-test/lazy (the delivery-router precedent); production
wiring happens in the web server, not here. Blocking work (tmux, git,
SQLite) runs off the event loop (the Phase-85 rule). Wire payloads are
path-free (§13) and refusals are typed (§12).
"""

from __future__ import annotations

import asyncio
from typing import Any, Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ...logging_config import get_logger
from ..context import WebContext
from . import delivery_declared
from ._mount import mount_router

log = get_logger("web.routes.delivery_factory")


def build_delivery_factory_router(ctx: WebContext) -> APIRouter:
    """The factory routes. ``profiles`` and ``discover`` are produced from
    the ``delivery.factory_profiles`` and ``delivery.factory_discover`` rows.
    ``launch`` stays written here: it spawns an agent process. The launcher,
    the profiles, the shared targets and commands, and their test seams live
    on ``ctx.delivery_service`` (``DeliveryService.configure``)."""
    delivery_service = delivery_declared.delivery_of(ctx)
    router = APIRouter()

    def _refused(exc: Any) -> JSONResponse:
        return JSONResponse(
            {"ok": False, "error": getattr(exc, "reason", "refused"), "detail": str(exc)},
            status_code=400,
        )

    @router.post("/api/delivery/factory/launch")
    async def api_factory_launch(request: Request, payload: Optional[dict[str, Any]] = None) -> Any:
        """One §9 agent.launch. The raw body rides to the service so a
        client-supplied executable/argv/command/shell/path refuses BY
        NAME — it is never silently dropped by a request model."""
        from ...delivery.commands import CommandRefused
        from ...delivery.factory_launch import LaunchRefused
        from ...principals import UNAUTHENTICATED

        body = payload if isinstance(payload, dict) else {}
        principal = getattr(request.state, "principal", UNAUTHENTICATED)
        try:
            record = await asyncio.to_thread(lambda: delivery_service.factory_launch(principal, body))
        except (LaunchRefused, CommandRefused) as exc:
            return _refused(exc)
        except Exception as exc:
            log.error(f"factory launch failed: {exc}")
            return JSONResponse({"error": "factory_launch_failure"}, status_code=500)
        return JSONResponse(record)

    mount_router(router, delivery_declared.router(
        ctx, ("delivery.factory_profiles", "delivery.factory_discover"), module=__name__,
    ))
    return router
