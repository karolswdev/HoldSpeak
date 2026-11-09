"""PARKED 20261108 (evening, the unreached-routes census): routes no client calls.

Parked from ``holdspeak/web/routes/missioncontrol.py``: POST /api/missioncontrol/rails/remote-events.
Not imported. Kept for history; restore with ``git revert`` of the parking commit.
"""
from __future__ import annotations
"""Mission-control bridge routes (HS-82-02).

The Desk consumes exactly the three documents the Delivery
Workbench contract allows a client (their `docs/mission-control.md`
§5) — the state feed, the correlation document, and the event log —
relayed byte-honest from the dw CLI of each rails repo the
operator's project map names. Schema drift and dead CLIs surface
as typed statuses (`compatibility` / `unavailable`) the belt
renders honestly. Design: docs/MISSION_CONTROL_DESK.md §1.
The write half (HS-82-05) rides the native propose→approve→execute
lifecycle: a story verb from the belt is recorded as a desk-origin
proposal, `decide_proposal` transitions it, and the execute leg runs
the two allow-listed `dw story` argv shapes through a gated
connector — argv from the stored payload, the repo path-allow-listed
to the project map, the dw gate keeping final say, its refusal
banner riding back verbatim. Design: docs/internal/MISSION_CONTROL_DESK.md §4.
"""

import asyncio
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ....logging_config import get_logger
from ....services.errors import NotFound, ValidationError
from ...context import WebContext
from ...runtime_support import error_500

log = get_logger("web.routes.missioncontrol")

# Test seam for the dw subprocess (the _GITHUB_RUNNER precedent).
_DW_RUNNER = None

# Last observed state-feed tree per repo (HS-86-03). Process-lifetime
# memory for change detection only — never a truth store; the feed
# itself is re-read every time.
_BELT_TREES: dict[str, str] = {}


def _emit_belt_frames(ctx: WebContext, payload: dict[str, Any]) -> None:
    """Broadcast one `scope:"belt"` frame per repo whose state-feed
    tree changed since the last observation (HS-86-03). Frames ride
    reads: the conveyor's poll is the heartbeat, and every surface on
    the bus hears the same motion. The first observation is a
    baseline, not a change."""
    if ctx.broadcast is None:
        return
    for entry in payload.get("repos", []):
        if entry.get("status") != "live":
            continue
        name = str(entry.get("name") or "")
        tree = str((entry.get("feed") or {}).get("generated_at_tree") or "")
        if not name or not tree:
            continue
        seen = _BELT_TREES.get(name)
        _BELT_TREES[name] = tree
        if seen is None or seen == tree:
            continue
        try:
            ctx.broadcast(
                "intel_status",
                {
                    "state": "ready",
                    "scope": "belt",
                    "capability": {"kind": "belt", "id": name, "name": name},
                },
            )
        except Exception as exc:
            log.debug(f"belt frame dropped: {exc}")


class _StoryProposeRequest(BaseModel):
    repo: str  # project-map NAME, not a path — the path comes from the map
    verb: str  # "status" | "create"
    project: str
    phase: str | int | None = None
    story: str | None = None
    status: str | None = None
    title: str | None = None


class _DecisionRequest(BaseModel):
    decision: str
    actor: str = "desk"





def parked_build_missioncontrol_router(
    ctx: WebContext,
    *,
    runner: Any = None,
    map_path: Optional[Path] = None,
) -> APIRouter:
    router = APIRouter()

    @router.post("/api/missioncontrol/rails/remote-events")
    def api_missioncontrol_rails_remote_events(body: dict[str, Any]) -> Any:
        """A remote node's rail-event envelope (HS-88-04) — the far node's
        worker tails its OWN `dw events` and pushes `{node, ts, events}`
        here; the ambient observer merges them, each stamped with its
        origin node. Events only: a body-carrying event is refused (no
        repo file contents cross the wire). Off-loopback this route is
        token-gated like every write."""
        from ...rails_observer import push_remote_envelope

        accepted, reason = push_remote_envelope(body if isinstance(body, dict) else {})
        if not accepted:
            return JSONResponse(
                {"accepted": False, "reason": reason}, status_code=400
            )
        node = str(body.get("node") or "")
        count = len(body.get("events") or [])
        return {"accepted": True, "node": node, "events": count}

    return router
