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
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ...logging_config import get_logger
from ..context import WebContext

log = get_logger("web.routes.delivery_factory")


def build_delivery_factory_router(
    ctx: WebContext,
    *,
    service: Any = None,
    profiles: Any = None,
    commands: Any = None,
    targets: Any = None,
    registry_path: Optional[Path] = None,
    map_path: Optional[Path] = None,
    profiles_path: Optional[Path] = None,
    launches_path: Optional[Path] = None,
    ledger_path: Optional[Path] = None,
    claims_state_path: Optional[Path] = None,
    local_node_id: str = "local",
    mode_loader: Any = None,
    sync_on_read: bool = True,
) -> APIRouter:
    """Every keyword is a test seam (the delivery-router precedent);
    production defaults assemble lazily on first request over the hub
    database, the Delivery Source registry, the shared target registry,
    and the HS-94-06 command service."""
    _ = ctx
    router = APIRouter()
    holder: dict[str, Any] = {
        "service": service,
        "profiles": profiles,
        "commands": commands,
        "targets": targets,
    }

    def _profiles() -> Any:
        if holder["profiles"] is None:
            from ...delivery.factory_launch import AgentProfileStore

            holder["profiles"] = AgentProfileStore(profiles_path)
        return holder["profiles"]

    def _targets() -> Any:
        if holder["targets"] is None:
            from ...delivery.terminal import TerminalTargetRegistry

            holder["targets"] = TerminalTargetRegistry()
        return holder["targets"]

    def _commands() -> Any:
        if holder["commands"] is None:
            from ...db import get_database
            from ...db.delivery_receipts import NodeReceiptLedger
            from ...delivery.commands import HubCommandService, NodeCommandProcessor

            processor = NodeCommandProcessor(
                node_id=local_node_id,
                targets=_targets(),
                ledger=NodeReceiptLedger(ledger_path),
            )
            holder["commands"] = HubCommandService(
                repo=get_database().delivery_receipts,
                processor=processor,
                local_node_id=local_node_id,
                mode_loader=mode_loader,
            )
        return holder["commands"]

    def _service() -> Any:
        if holder["service"] is None:
            from ...db import get_database
            from ...delivery import DeliveryRegistry
            from ...delivery.factory_launch import LaunchLedger, LaunchService

            holder["service"] = LaunchService(
                profiles=_profiles(),
                registry=DeliveryRegistry(registry_path, map_path=map_path),
                targets=_targets(),
                commands=_commands(),
                attempts=get_database().work_attempts,
                ledger=LaunchLedger(launches_path),
                local_node_id=local_node_id,
            )
        return holder["service"]

    def _refused(exc: Any) -> JSONResponse:
        return JSONResponse(
            {"ok": False, "error": getattr(exc, "reason", "refused"), "detail": str(exc)},
            status_code=400,
        )

    @router.get("/api/delivery/factory/profiles")
    async def api_factory_profiles() -> Any:
        try:
            return await asyncio.to_thread(_profiles().to_wire)
        except Exception as exc:
            log.error(f"factory profiles read failed: {exc}")
            return JSONResponse({"error": "factory_profiles_failure"}, status_code=500)

    @router.post("/api/delivery/factory/launch")
    async def api_factory_launch(payload: Optional[dict[str, Any]] = None) -> Any:
        """One §9 agent.launch. The raw body rides to the service so a
        client-supplied executable/argv/command/shell/path refuses BY
        NAME — it is never silently dropped by a request model."""
        from ...delivery.commands import CommandRefused
        from ...delivery.factory_launch import LaunchRefused

        body = payload if isinstance(payload, dict) else {}
        try:
            record = await asyncio.to_thread(_service().launch, body)
        except (LaunchRefused, CommandRefused) as exc:
            return _refused(exc)
        except Exception as exc:
            log.error(f"factory launch failed: {exc}")
            return JSONResponse({"error": "factory_launch_failure"}, status_code=500)
        return JSONResponse(record)

    @router.get("/api/delivery/factory/discover")
    async def api_factory_discover() -> Any:
        """Panes/sessions as immutable targets. The best-effort sweep
        binds fresh rider claims and expires overdue registrations so
        the listing is honest without any client write."""
        try:
            def _read() -> dict[str, Any]:
                svc = _service()
                if sync_on_read:
                    try:
                        svc.bind_rider_claims(state_path=claims_state_path)
                        svc.expire_unregistered()
                    except Exception as sync_exc:
                        log.warning(f"launch-claim sweep skipped: {sync_exc}")
                return svc.discover()

            return await asyncio.to_thread(_read)
        except Exception as exc:
            log.error(f"factory discover failed: {exc}")
            return JSONResponse({"error": "factory_discover_failure"}, status_code=500)

    return router
