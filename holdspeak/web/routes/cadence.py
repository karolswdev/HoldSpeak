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

    @router.get("/loops/{loop_id}")
    async def loop_detail(loop_id: str) -> dict[str, Any]:
        from ...db import get_database

        loop = get_database().cadence.get_loop(loop_id)
        if loop is None:
            raise HTTPException(status_code=404, detail="loop not found")
        return _loop_dict(loop)

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
