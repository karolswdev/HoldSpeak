"""Cadence Engine HTTP routes (CAD-2-02/03).

A read API over the Phase-1 substrate + local lifecycle actions (snooze/kill/close)
+ a synchronous run-now. Every loop carries its evidence, a deterministic prepared
next action, and an honest egress badge. NO autonomous external side effect: lifecycle
actions are local cadence_* writes; a `next_action` that maps to a connector is a DRAFT
(executing it is the actuator approve→execute path, Phase 6/7).
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Body, HTTPException

from ..context import WebContext

# Phase 2 reads/writes are local-only; the badge is honest about that.
_LOCAL_EGRESS = {"scope": "local", "label": "Local only"}


def _cadence_llm():
    """The capability-gated LLM callable (CAD-7) — None unless `cadence.use_llm` is on.

    Builds the user's configured intel provider; returns (system, user) -> text. The
    next-action generator is fail-closed, so a None or a failing llm is harmless."""
    from ...config import Config

    if not getattr(Config.load().cadence, "use_llm", False):
        return None
    try:
        from ...intel.providers import build_configured_meeting_intel

        intel = build_configured_meeting_intel()
        return lambda sysp, usr: intel.run_prompt(system_prompt=sysp, user_prompt=usr)
    except Exception:
        return None


def _loop_dict(loop, *, with_next_action: bool = True) -> dict[str, Any]:
    from ...cadence.next_action import generate_next_action

    out: dict[str, Any] = {
        "id": loop.id,
        "title": loop.title,
        "summary": loop.summary,
        "project": loop.project,
        "source_type": loop.source_type,
        "status": loop.status,
        "priority": loop.priority,
        "needs_review": loop.needs_review,
        "owner": loop.owner,
        "due_at": loop.due_at,
        "snoozed_until": loop.snoozed_until,
        "stale_score": loop.stale_score,
        "nudge_count": loop.nudge_count,
        "evidence": [
            {"kind": e.kind, "ref_id": e.ref_id, "label": e.label,
             "timestamp": e.timestamp, "deep_link": e.deep_link}
            for e in loop.evidence
        ],
        "egress": _LOCAL_EGRESS,
    }
    if with_next_action:
        na = generate_next_action(loop)
        out["next_action"] = {
            "kind": na.kind, "title": na.title, "body_markdown": na.body_markdown,
            "reversible": na.reversible, "confidence": na.confidence,
        }
    return out


def build_cadence_router(ctx: WebContext) -> APIRouter:
    router = APIRouter(prefix="/api/cadence", tags=["cadence"])

    @router.get("/status")
    async def status() -> dict[str, Any]:
        from ...config import Config
        from ...db import get_database

        db = get_database()
        c = Config.load().cadence
        counts: dict[str, int] = {}
        for loop in db.cadence.list_loops(include_terminal=True):
            counts[loop.status] = counts.get(loop.status, 0) + 1
        return {
            "enabled": c.enabled,
            "pressure": c.pressure,
            "tick_interval_seconds": c.tick_interval_seconds,
            "quiet_hours": {"start": c.quiet_hours_start, "end": c.quiet_hours_end},
            "max_nudges_per_day": c.max_nudges_per_day,
            "policies": len(db.cadence.list_policies()),
            "counts": counts,
            "egress": _LOCAL_EGRESS,
        }

    @router.get("/loops")
    async def loops(all: bool = False) -> dict[str, Any]:
        from ...db import get_database

        db = get_database()
        items = db.cadence.list_loops(include_terminal=all)
        return {"loops": [_loop_dict(loop) for loop in items], "egress": _LOCAL_EGRESS}

    @router.get("/brief")
    async def brief() -> dict[str, Any]:
        from ...cadence.brief import build_brief
        from ...db import get_database

        b = build_brief(get_database())
        return {
            "date": b.date,
            "headline": b.headline,
            "open_count": b.open_count,
            "generated_by": b.generated_by,
            "items": [
                {"loop": _loop_dict(it.loop, with_next_action=False),
                 "next_action": {"kind": it.next_action.kind, "title": it.next_action.title,
                                 "body_markdown": it.next_action.body_markdown}}
                for it in b.items
            ],
            "egress": _LOCAL_EGRESS,
        }

    @router.get("/closeout")
    async def closeout() -> dict[str, Any]:
        from datetime import datetime

        from ...cadence.closeout import build_closeout, escalation_severity
        from ...db import get_database

        now = datetime.now()
        co = build_closeout(get_database(), now=now)
        return {
            "date": co.date,
            "open_count": co.open_count,
            "summary": co.summary,
            "recs": [
                {"loop": _loop_dict(r.loop), "severity": r.severity,
                 "action": r.action, "reason": r.reason}
                for r in co.recs
            ],
            "egress": _LOCAL_EGRESS,
        }

    @router.post("/closeout/apply")
    async def closeout_apply(body: dict = Body(default={})) -> dict[str, Any]:
        """Batch-apply lifecycle decisions: [{loop_id, action}]. Local only."""
        from ...cadence.closeout import apply_decision
        from ...db import get_database

        db = get_database()
        applied, skipped = 0, 0
        for d in (body.get("decisions") or []):
            if apply_decision(db, str(d.get("loop_id", "")), str(d.get("action", ""))):
                applied += 1
            else:
                skipped += 1
        return {"applied": applied, "skipped": skipped, "egress": _LOCAL_EGRESS}

    @router.get("/history")
    async def history(limit: int = 50) -> dict[str, Any]:
        from ...db import get_database

        return {"nudges": get_database().cadence.list_nudges(limit=limit), "egress": _LOCAL_EGRESS}

    @router.get("/audit")
    async def audit() -> dict[str, Any]:
        """The telemetry-free local audit snapshot (CAD-8) — nothing leaves the machine."""
        from ...cadence.audit import export_audit
        from ...db import get_database

        return export_audit(get_database())

    @router.get("/loops/{loop_id}")
    async def loop_detail(loop_id: str) -> dict[str, Any]:
        from ...db import get_database

        loop = get_database().cadence.get_loop(loop_id)
        if loop is None:
            raise HTTPException(status_code=404, detail="loop not found")
        # The single-loop detail is where a drafted next action is worth the LLM call
        # (gated; fail-closed to deterministic). The list/brief stay deterministic.
        from ...cadence.llm_action import next_action_for

        out = _loop_dict(loop, with_next_action=False)
        na = next_action_for(loop, llm=_cadence_llm())
        out["next_action"] = {"kind": na.kind, "title": na.title,
                              "body_markdown": na.body_markdown, "reversible": na.reversible,
                              "confidence": na.confidence, "generated_by": na.generated_by}
        return out

    def _require(loop_id: str):
        from ...db import get_database

        db = get_database()
        loop = db.cadence.get_loop(loop_id)
        if loop is None:
            raise HTTPException(status_code=404, detail="loop not found")
        return db, loop

    @router.post("/loops/{loop_id}/snooze")
    async def snooze(loop_id: str, body: dict = Body(default={})) -> dict[str, Any]:
        db, _ = _require(loop_id)
        until = body.get("until")
        if not until:
            hours = float(body.get("hours", 24))
            until = (datetime.now() + timedelta(hours=hours)).isoformat()
        db.cadence.snooze(loop_id, until)
        return _loop_dict(db.cadence.get_loop(loop_id))

    @router.post("/loops/{loop_id}/kill")
    async def kill(loop_id: str) -> dict[str, Any]:
        db, _ = _require(loop_id)
        db.cadence.set_status(loop_id, "killed")  # stays killed across re-collection
        return _loop_dict(db.cadence.get_loop(loop_id))

    @router.post("/loops/{loop_id}/close")
    async def close(loop_id: str) -> dict[str, Any]:
        db, _ = _require(loop_id)
        db.cadence.set_status(loop_id, "closed")
        return _loop_dict(db.cadence.get_loop(loop_id))

    @router.post("/loops/{loop_id}/reply")
    async def reply_to_agent(loop_id: str, body: dict = Body(default={})) -> dict[str, Any]:
        """Deliver a USER-TYPED reply into a waiting agent's terminal (CAD-3-03).

        Never autonomous: requires an explicit non-empty `text`. Only valid for an
        `agent_question` loop whose session still has a tmux pane. The delivery uses
        the existing `send_text_to_pane` transport — the side effect lives HERE, not in
        the cadence package (which the no-side-effects guard keeps clean).
        """
        db, loop = _require(loop_id)
        if loop.source_type != "agent_question":
            raise HTTPException(status_code=400, detail="not an agent loop")
        text = str(body.get("text", "")).strip()
        if not text:
            raise HTTPException(status_code=400, detail="reply text is required")

        from ...agent_context import list_recent_awaiting_agent_sessions
        from ...tmux_transport import TmuxTransportError, send_text_to_pane

        session = next(
            (s for s in list_recent_awaiting_agent_sessions() if s.session_id == loop.source_id),
            None,
        )
        pane = getattr(session, "tmux_pane", None) if session else None
        if not pane:
            raise HTTPException(status_code=409, detail="no terminal pane for this agent session")
        try:
            delivery = send_text_to_pane(pane=pane, text=text, submit=True)
        except TmuxTransportError as exc:
            raise HTTPException(status_code=502, detail=f"delivery failed: {exc}") from exc

        # The reply answers the agent — close the loop (its question is handled).
        db.cadence.set_status(loop_id, "closed")
        db.cadence.bump_nudge(loop_id)
        return {"delivered": True, "pane": delivery.pane, "submitted": delivery.submitted,
                "egress": _LOCAL_EGRESS}

    @router.post("/run-now")
    async def run_now() -> dict[str, Any]:
        from ...cadence.service import CadenceService
        from ...config import Config
        from ...db import get_database

        result = CadenceService(get_database(), Config.load().cadence).tick(datetime.now())
        return {
            "at": result.at,
            "projected": result.projected,
            "open_loops": result.open_loops,
            "due": [_loop_dict(loop) for loop in result.due],
            "egress": _LOCAL_EGRESS,
        }

    return router
