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
import hashlib
import json
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ...logging_config import get_logger
from ..context import WebContext
from ..runtime_support import error_500

log = get_logger("web.routes.missioncontrol")

# Test seam for the dw subprocess (the _GITHUB_RUNNER precedent).
_DW_RUNNER = None

MC_PLUGIN_ID = "missioncontrol_desk"
MC_PLUGIN_VERSION = "0.1.0"

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


def execute_dw_proposal(
    ctx: WebContext,
    db: Any,
    proposal: Any,
    *,
    actor: str,
    map_path: Optional[Path] = None,
    runner: Any = None,
) -> Any:
    """The execute leg for an approved Delivery Workbench story verb.

    The repo is re-resolved from the project map at execution time —
    a payload naming a path outside the map fails honestly here, the
    lifecycle's path-allow-list. The connector admits exactly two
    argv shapes and the dw gate downstream still refuses anything
    dishonest; an approved-but-refused proposal lands `failed` with
    the banner verbatim in its error field. That is the stack
    working, not a bug.
    """
    from ...missioncontrol_bridge import build_dw_story_connector, load_project_map
    from ...plugins.actuator_executor import ActuatorExecutor
    from ..routes.actuator_shared import actuator_result_event

    payload = dict(proposal.payload or {})
    repo_path = str(payload.get("repo") or "")
    allowed = set(load_project_map(map_path)["projects"].values())
    if repo_path not in allowed:
        updated = db.actuators.transition_proposal(
            proposal.id, to_status="failed", actor=actor,
            detail="mission control: repo not in the project map at execution time",
            error=f"repo {repo_path!r} is not in the operator's project map",
        )
        ctx.broadcast("actuator_result", actuator_result_event(updated))
        return updated

    executor = ActuatorExecutor(
        db,
        connector=build_dw_story_connector(
            Path(repo_path), runner=runner or _DW_RUNNER
        ),
        allow_actuators=True,
        actor=actor,
        on_result=lambda event: ctx.broadcast("actuator_result", event),
    )
    return executor.execute(proposal.id)


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

    @router.get("/api/missioncontrol/state")
    async def api_missioncontrol_state() -> Any:
        try:
            from ...missioncontrol_bridge import state_payload

            # to_thread: the bridge shells a CLI per repo (the
            # Phase-85 event-loop rule, applied here by HS-86-03).
            payload = await asyncio.to_thread(state_payload, _map(), runner)
            _emit_belt_frames(ctx, payload)
            return payload
        except Exception as exc:
            log.warning(f"mission control state failed ({exc})")
            return {"repos": [], "error": "mission control state failed"}

    @router.get("/api/missioncontrol/sessions")
    async def api_missioncontrol_sessions() -> Any:
        try:
            from ...missioncontrol_bridge import sessions_payload

            return await asyncio.to_thread(sessions_payload, _map(), runner)
        except Exception as exc:
            log.warning(f"mission control sessions failed ({exc})")
            return {"status": "unavailable", "detail": "sessions read failed"}

    @router.get("/api/missioncontrol/events")
    async def api_missioncontrol_events(tail: int = 20) -> Any:
        try:
            from ...missioncontrol_bridge import events_payload

            return await asyncio.to_thread(events_payload, _map(), tail, runner)
        except Exception as exc:
            log.warning(f"mission control events failed ({exc})")
            return {"repos": [], "error": "mission control events failed"}

    @router.get("/api/missioncontrol/receipts")
    async def api_missioncontrol_receipts() -> Any:
        """GitHub receipts per map repo (HS-86-03) — the PR and CI
        station lights. Read-only; absence is typed, never a 500."""
        try:
            from ...missioncontrol_bridge import receipts_payload

            return await asyncio.to_thread(receipts_payload, _map(), runner)
        except Exception as exc:
            log.warning(f"mission control receipts failed ({exc})")
            return {"repos": [], "error": "mission control receipts failed"}

    @router.get("/api/missioncontrol/evidence")
    async def api_missioncontrol_evidence(repo: str, project: str, story: str) -> Any:
        """One story's evidence content (HS-86-04), CLI-resolved and
        path-contained — the desk opens it in place. Read-only."""
        try:
            from ...missioncontrol_bridge import story_evidence_payload

            return await asyncio.to_thread(
                story_evidence_payload, _map(), repo, project, story, runner
            )
        except Exception as exc:
            log.warning(f"mission control evidence failed ({exc})")
            return {"status": "unavailable", "detail": "evidence read failed"}

    @router.get("/api/missioncontrol/rails/journal")
    async def api_missioncontrol_rails_journal(limit: int = 50) -> Any:
        """The ambient observer's journal (HS-88-03) — the local model's
        running note of what the rails did, newest first. Read-only; the
        journal entries are notes, openable and groundable like any
        primitive."""
        try:
            from ...db import get_database
            from ...rails_observer import list_journal

            entries = await asyncio.to_thread(list_journal, get_database(), limit=limit)
            return {
                "entries": [
                    {
                        "id": n.id,
                        "title": n.title,
                        "body_markdown": n.body_markdown,
                        "created_at": getattr(n, "created_at", ""),
                    }
                    for n in entries
                ]
            }
        except Exception as exc:
            log.warning(f"rails journal read failed ({exc})")
            return {"entries": [], "error": "rails journal read failed"}

    @router.post("/api/missioncontrol/rails/size")
    async def api_missioncontrol_rails_size(body: dict[str, Any]) -> Any:
        """Hydrated sizes for picked rail refs (HS-88-02) — the grounding
        gauge's honest number. Reads the dw-named files (a receipt) and
        returns SIZES only, never the content; unknown refs come back so
        the picker can drop them."""
        try:
            from ...grounding_rails import hydrate_rails_refs

            refs = body.get("rails") if isinstance(body, dict) else None
            refs = [r for r in refs if isinstance(r, dict)] if isinstance(refs, list) else []
            blocks, unknown = await asyncio.to_thread(
                hydrate_rails_refs, refs, project_map=_map(), runner=runner
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
    async def api_missioncontrol_story_propose(body: _StoryProposeRequest) -> Any:
        """Record a story-verb proposal (§4): fields validated against
        the LIVE feed, never trusted from the UI; the preview names
        the act and the gate's standing right of refusal."""
        try:
            from ...db import get_database
            from ...missioncontrol_bridge import (
                ALLOWED_STORY_STATUSES,
                build_story_preview,
                state_entry,
            )
            from ..routes.actuator_shared import proposal_to_dict

            project_map = _map()
            repo_path = project_map["projects"].get(body.repo)
            if not repo_path:
                return JSONResponse(
                    {"success": False, "error": f"repo {body.repo!r} is not in the project map"},
                    status_code=400,
                )
            entry = state_entry(body.repo, repo_path, runner)
            if entry.get("status") != "live":
                return JSONResponse(
                    {"success": False, "error": f"rails unreadable: {entry.get('detail')}"},
                    status_code=400,
                )
            projects = {
                p.get("slug"): p for p in entry["feed"].get("projects") or []
            }
            project = projects.get(body.project)
            if project is None:
                return JSONResponse(
                    {"success": False, "error": f"project {body.project!r} is not on the roadmap"},
                    status_code=400,
                )
            verb = str(body.verb or "").strip()
            if verb == "status":
                story = next(
                    (s for s in project.get("stories") or [] if s.get("story_id") == body.story),
                    None,
                )
                if story is None:
                    return JSONResponse(
                        {"success": False, "error": f"story {body.story!r} is not on the {body.project} roadmap"},
                        status_code=400,
                    )
                status = str(body.status or "").strip().lower()
                if status not in ALLOWED_STORY_STATUSES:
                    return JSONResponse(
                        {"success": False, "error": f"status {status!r} is not one of {', '.join(ALLOWED_STORY_STATUSES)}"},
                        status_code=400,
                    )
                payload = {
                    "repo": repo_path, "verb": "status",
                    "project": body.project, "phase": str(story.get("phase")),
                    "story": body.story, "status": status,
                }
                preview = build_story_preview(
                    payload, story.get("title") or "", story.get("status") or ""
                )
                action = "dw_story_status"
            elif verb == "create":
                phases = {str(p.get("number")) for p in project.get("phases") or []}
                phase = str(body.phase or "").strip()
                title = str(body.title or "").strip()
                if phase not in phases:
                    return JSONResponse(
                        {"success": False, "error": f"phase {phase!r} is not on the {body.project} roadmap"},
                        status_code=400,
                    )
                if not title:
                    return JSONResponse(
                        {"success": False, "error": "a story create needs a title"},
                        status_code=400,
                    )
                payload = {
                    "repo": repo_path, "verb": "create",
                    "project": body.project, "phase": phase, "title": title,
                }
                preview = build_story_preview(payload)
                action = "dw_story_create"
            else:
                return JSONResponse(
                    {"success": False, "error": f"verb {verb!r} is not an allow-listed story verb"},
                    status_code=400,
                )

            payload_key = hashlib.sha256(
                json.dumps(payload, sort_keys=True).encode("utf-8")
            ).hexdigest()[:16]
            db = get_database()
            proposal = db.actuators.record_proposal(
                meeting_id=None,
                origin="desk",
                window_id="desk:missioncontrol",
                plugin_id=MC_PLUGIN_ID,
                plugin_version=MC_PLUGIN_VERSION,
                idempotency_key=f"mc-story:{payload_key}",
                target="delivery-workbench",
                action=action,
                preview=preview,
                payload=payload,
                reversible=True,
                required_capabilities=["actuator"],
            )
            ctx.broadcast(
                "actuator_proposed",
                {
                    "id": proposal.id,
                    "meeting_id": proposal.meeting_id,
                    "plugin_id": proposal.plugin_id,
                    "status": proposal.status,
                    "target": proposal.target,
                    "action": proposal.action,
                    "preview": proposal.preview,
                    "reversible": bool(proposal.reversible),
                },
            )
            return JSONResponse(
                {"success": True, "proposal": proposal_to_dict(proposal)}
            )
        except Exception as exc:
            return error_500(exc, log, "Failed to propose a story verb")

    @router.post("/api/missioncontrol/proposals/{proposal_id}/decision")
    async def api_missioncontrol_decision(
        proposal_id: str, body: _DecisionRequest
    ) -> Any:
        """The approval tap (§4): the shared lifecycle transitions the
        proposal and, on approve, the dw execute leg runs."""
        try:
            from ...db import get_database
            from ..routes.actuator_shared import decide_proposal, proposal_to_dict

            updated, err, status_code = decide_proposal(
                ctx,
                get_database(),
                proposal_id,
                decision=body.decision,
                actor=body.actor,
                belongs=lambda p: (
                    getattr(p, "origin", "") == "desk"
                    and p.target == "delivery-workbench"
                ),
                executors={
                    "delivery-workbench": lambda c, d, p, *, actor: (
                        execute_dw_proposal(
                            c, d, p, actor=actor,
                            map_path=map_path, runner=runner,
                        )
                    )
                },
            )
            if err is not None:
                return JSONResponse(
                    {"success": False, "error": err}, status_code=status_code
                )
            return JSONResponse(
                {"success": True, "proposal": proposal_to_dict(updated)}
            )
        except Exception as exc:
            return error_500(exc, log, "Failed to decide a story proposal")

    return router
