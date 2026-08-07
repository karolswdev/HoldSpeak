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
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ...logging_config import get_logger
from ...services.errors import NotFound, ValidationError
from ..context import WebContext
from ..runtime_support import error_500

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



def build_missioncontrol_router(
    ctx: WebContext,
    *,
    runner: Any = None,
    map_path: Optional[Path] = None,
) -> APIRouter:
    """`runner` and `map_path` are test seams (the connector-runtime
    precedent); production uses the defaults."""
    router = APIRouter()

    def _map() -> dict[str, Any]:
        from ...missioncontrol_bridge import load_project_map

        return load_project_map(map_path)

    def _principal(request: Request):
        from ...principals import UNAUTHENTICATED

        return getattr(request.state, "principal", UNAUTHENTICATED)

    def _service():
        service = ctx.mission_control_service
        if service is None:
            raise RuntimeError("MissionControlService is not composed")
        return service

    @router.get("/api/missioncontrol/state")
    async def api_missioncontrol_state(request: Request) -> Any:
        try:
            from ...missioncontrol_bridge import state_payload

            # to_thread: the bridge shells a CLI per repo (the
            # Phase-85 event-loop rule, applied here by HS-86-03).
            payload = await asyncio.to_thread(
                state_payload,
                _map(),
                runner,
                principal=_principal(request),
            )
            _emit_belt_frames(ctx, payload)
            return payload
        except Exception as exc:
            log.warning(f"mission control state failed ({exc})")
            return {"repos": [], "error": "mission control state failed"}

    @router.get("/api/missioncontrol/sessions")
    async def api_missioncontrol_sessions(request: Request) -> Any:
        try:
            from ...missioncontrol_bridge import sessions_payload

            return await asyncio.to_thread(
                sessions_payload,
                _map(),
                runner,
                principal=_principal(request),
            )
        except Exception as exc:
            log.warning(f"mission control sessions failed ({exc})")
            return {"status": "unavailable", "detail": "sessions read failed"}

    @router.get("/api/missioncontrol/events")
    async def api_missioncontrol_events(request: Request, tail: int = 20) -> Any:
        try:
            from ...missioncontrol_bridge import events_payload

            return await asyncio.to_thread(
                events_payload,
                _map(),
                tail,
                runner,
                principal=_principal(request),
            )
        except Exception as exc:
            log.warning(f"mission control events failed ({exc})")
            return {"repos": [], "error": "mission control events failed"}

    @router.get("/api/missioncontrol/receipts")
    async def api_missioncontrol_receipts(request: Request) -> Any:
        """GitHub receipts per map repo (HS-86-03) — the PR and CI
        station lights. Read-only; absence is typed, never a 500."""
        try:
            from ...missioncontrol_bridge import receipts_payload

            return await asyncio.to_thread(
                receipts_payload,
                _map(),
                runner,
                principal=_principal(request),
            )
        except Exception as exc:
            log.warning(f"mission control receipts failed ({exc})")
            return {"repos": [], "error": "mission control receipts failed"}

    @router.get("/api/missioncontrol/evidence")
    async def api_missioncontrol_evidence(
        request: Request, repo: str, project: str, story: str
    ) -> Any:
        """One story's evidence content (HS-86-04), CLI-resolved and
        path-contained — the desk opens it in place. Read-only."""
        try:
            from ...missioncontrol_bridge import story_evidence_payload

            return await asyncio.to_thread(
                story_evidence_payload,
                _map(),
                repo,
                project,
                story,
                runner,
                principal=_principal(request),
            )
        except Exception as exc:
            log.warning(f"mission control evidence failed ({exc})")
            return {"status": "unavailable", "detail": "evidence read failed"}

    @router.post("/api/missioncontrol/rails/remote-events")
    async def api_missioncontrol_rails_remote_events(body: dict[str, Any]) -> Any:
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

    @router.get("/api/missioncontrol/rails/journal")
    async def api_missioncontrol_rails_journal(
        request: Request, limit: int = 50
    ) -> Any:
        """Return the ambient observer journal, newest first."""
        try:
            entries = await asyncio.to_thread(
                _service().list_rails_journal, _principal(request), limit=limit
            )
            return {"entries": [
                {
                    "id": note.id,
                    "title": note.title,
                    "body_markdown": note.body_markdown,
                    "created_at": getattr(note, "created_at", ""),
                }
                for note in entries
            ]}
        except Exception as exc:
            log.warning(f"rails journal read failed ({exc})")
            return {"entries": [], "error": "rails journal read failed"}

    @router.post("/api/missioncontrol/rails/size")
    async def api_missioncontrol_rails_size(
        request: Request, body: dict[str, Any]
    ) -> Any:
        """Hydrated sizes for picked rail refs (HS-88-02) — the grounding
        gauge's honest number. Reads the dw-named files (a receipt) and
        returns SIZES only, never the content; unknown refs come back so
        the picker can drop them."""
        try:
            from ...grounding_rails import hydrate_rails_refs

            refs = body.get("rails") if isinstance(body, dict) else None
            refs = [r for r in refs if isinstance(r, dict)] if isinstance(refs, list) else []
            blocks, unknown = await asyncio.to_thread(
                hydrate_rails_refs,
                refs,
                principal=_principal(request),
                project_map=_map(),
                runner=runner,
            )
            sizes = [
                {
                    "kind": b.kind.replace("rails:", ""),
                    "id": b.ref,
                    "title": b.title,
                    "chars": len(b.text),
                }
                for b in blocks
            ]
            return {"sizes": sizes, "unknown": unknown}
        except Exception as exc:
            log.warning(f"rails size failed ({exc})")
            return {"sizes": [], "unknown": [], "error": "rails size failed"}

    @router.post("/api/missioncontrol/story/propose")
    async def api_missioncontrol_story_propose(
        request: Request, body: _StoryProposeRequest
    ) -> Any:
        """Validate and record a Delivery Workbench story proposal."""
        try:
            from ..routes.actuator_shared import proposal_to_dict

            proposal = await asyncio.to_thread(
                _service().propose_story,
                _principal(request),
                body,
                project_map=_map(),
                runner=runner,
            )
            if ctx.broadcast is not None:
                ctx.broadcast("actuator_proposed", {
                    "id": proposal.id,
                    "meeting_id": proposal.meeting_id,
                    "plugin_id": proposal.plugin_id,
                    "status": proposal.status,
                    "target": proposal.target,
                    "action": proposal.action,
                    "preview": proposal.preview,
                    "reversible": bool(proposal.reversible),
                })
            return JSONResponse({"success": True, "proposal": proposal_to_dict(proposal)})
        except ValidationError as exc:
            return JSONResponse({"success": False, "error": exc.detail}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to propose a story verb")

    @router.post("/api/missioncontrol/proposals/{proposal_id}/decision")
    async def api_missioncontrol_decision(
        request: Request, proposal_id: str, body: _DecisionRequest
    ) -> Any:
        """Decide and, when approved, execute a story proposal."""
        try:
            from ..routes.actuator_shared import proposal_to_dict

            updated = await asyncio.to_thread(
                _service().decide_proposal,
                _principal(request),
                proposal_id,
                decision=body.decision,
                actor=body.actor,
                map_path=map_path,
                runner=runner or _DW_RUNNER,
                broadcast=ctx.broadcast,
            )
            return JSONResponse({"success": True, "proposal": proposal_to_dict(updated)})
        except NotFound:
            return JSONResponse({"success": False, "error": "Proposal not found"}, status_code=404)
        except ValidationError as exc:
            return JSONResponse({"success": False, "error": exc.detail}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to decide a story proposal")

    return router
