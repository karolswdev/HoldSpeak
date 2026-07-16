"""Work attempt routes (HS-94-04).

The §10 attempt surface: ``POST /api/delivery/attempts`` attaches
exact work with explicit refs (provenance is always ``manual`` here —
a client cannot mint launch/rider/contract provenance), and
``GET /api/delivery/attempts`` projects the durable rows with states,
provenance, and replayable history. Reads sweep the emitted rider
claims first (bounded, best-effort) so an agent whose hooks claimed a
Story appears as an exact attempt without any write from the client.

The §12/§13 rules ride every handler: refusals are typed and
path-free, wire rows carry opaque IDs only, and blocking work runs
off the event loop (the Phase-85 rule). Service assembly is lazy so
importing/mounting the router has no side effects.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ...logging_config import get_logger
from ..context import WebContext

log = get_logger("web.routes.delivery_attempts")


def _classified_500(exc: Exception, detail: str) -> JSONResponse:
    log.error(f"{detail}: {exc}")
    return JSONResponse({"error": detail}, status_code=500)


class _CreateAttemptRequest(BaseModel):
    source_id: str
    worktree_id: str
    project: str
    story_id: str
    session_id: Optional[str] = None
    node_id: Optional[str] = None
    target_id: Optional[str] = None
    actor: Optional[str] = None


def build_delivery_attempts_router(
    ctx: WebContext,
    *,
    service: Any = None,
    registry_path: Optional[Path] = None,
    map_path: Optional[Path] = None,
    claims_state_path: Optional[Path] = None,
    sync_on_read: bool = True,
) -> APIRouter:
    """Every keyword is a test seam (the delivery-router precedent);
    production uses the defaults: the database's work-attempt
    repository plus a resolver over the Delivery Source registry."""
    _ = ctx
    router = APIRouter()
    holder: dict[str, Any] = {"service": service}

    def _service() -> Any:
        if holder["service"] is None:
            from ...db import get_database
            from ...delivery import DeliveryRegistry
            from ...delivery.attempts import (
                WorkAttemptService,
                resolver_from_registry,
            )

            registry = DeliveryRegistry(registry_path, map_path=map_path)
            holder["service"] = WorkAttemptService(
                get_database().work_attempts,
                resolver=resolver_from_registry(registry),
            )
        return holder["service"]

    @router.post("/api/delivery/attempts")
    async def api_delivery_create_attempt(body: _CreateAttemptRequest) -> Any:
        """Manual attach: explicit refs, ``association.kind='manual'``.
        A session already exactly bound to a live attempt answers 409 —
        end or supersede it deliberately, never double-pin silently."""
        try:
            from ...delivery.attempts import AttemptConflict, AttemptError

            def _create() -> dict[str, Any]:
                return _service().manual_attach(
                    source_id=body.source_id,
                    worktree_id=body.worktree_id,
                    project=body.project,
                    story_id=body.story_id,
                    session_id=body.session_id,
                    node_id=body.node_id,
                    target_id=body.target_id,
                    actor=body.actor or "desk-owner",
                )

            try:
                attempt = await asyncio.to_thread(_create)
            except AttemptConflict as conflict:
                return JSONResponse(
                    {"success": False, "error": str(conflict)}, status_code=409
                )
            except AttemptError as refusal:
                return JSONResponse(
                    {"success": False, "error": str(refusal)}, status_code=400
                )
            return {"success": True, "attempt": attempt}
        except Exception as exc:
            return _classified_500(exc, "delivery attempt creation failed")

    @router.get("/api/delivery/attempts")
    async def api_delivery_list_attempts(
        source_id: str = "",
        project: str = "",
        story_id: str = "",
        session_id: str = "",
        active_only: bool = False,
    ) -> Any:
        """Durable attempts with explicit state + provenance. A
        ``kind='heuristic'`` row always carries ``exact=false`` — the
        ambiguity is visible data, never dressed up as a binding."""
        try:
            def _read() -> dict[str, Any]:
                svc = _service()
                if sync_on_read:
                    try:
                        svc.sync_rider_claims(state_path=claims_state_path)
                    except Exception as sync_exc:  # honest read beats a lost one
                        log.warning(f"rider-claim sync skipped: {sync_exc}")
                return svc.list_attempts(
                    source_id=source_id or None,
                    project=project or None,
                    story_id=story_id or None,
                    session_id=session_id or None,
                    active_only=bool(active_only),
                )

            return await asyncio.to_thread(_read)
        except Exception as exc:
            return _classified_500(exc, "delivery attempts read failed")

    return router
