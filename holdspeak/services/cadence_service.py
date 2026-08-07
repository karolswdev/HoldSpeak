"""Principal-aware cadence query and lifecycle boundary."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Any

from ..intel.providers import endpoint_egress
from ..principals import Principal
from .errors import NotFound

_LOCAL_EGRESS = endpoint_egress(cloud=False, label="Local only")


def _cadence_llm() -> Any:
    from ..config import Config
    if not getattr(Config.load().cadence, "use_llm", False):
        return None
    try:
        from ..intel.providers import build_configured_meeting_intel
        intel = build_configured_meeting_intel()
        return lambda system, user: intel.run_prompt(system_prompt=system, user_prompt=user)
    except Exception:
        return None


class CadenceService:
    def __init__(self, db: Any, config: Any) -> None:
        self._db = db
        self._config = config

    def _loop_dict(self, loop: Any, *, with_next_action: bool = True) -> dict[str, Any]:
        from ..cadence.next_action import generate_next_action
        out = {"id": loop.id, "title": loop.title, "summary": loop.summary,
               "project": loop.project, "source_type": loop.source_type,
               "status": loop.status, "priority": loop.priority,
               "needs_review": loop.needs_review, "owner": loop.owner,
               "due_at": loop.due_at, "snoozed_until": loop.snoozed_until,
               "stale_score": loop.stale_score, "nudge_count": loop.nudge_count,
               "evidence": [{"kind": e.kind, "ref_id": e.ref_id, "label": e.label,
                             "timestamp": e.timestamp, "deep_link": e.deep_link} for e in loop.evidence],
               "egress": _LOCAL_EGRESS}
        if with_next_action:
            action = generate_next_action(loop)
            out["next_action"] = {"kind": action.kind, "title": action.title,
                                  "body_markdown": action.body_markdown, "reversible": action.reversible,
                                  "confidence": action.confidence}
        return out

    def status(self, principal: Principal) -> dict[str, Any]:
        counts: dict[str, int] = {}
        for loop in self._db.cadence.list_loops(include_terminal=True):
            counts[loop.status] = counts.get(loop.status, 0) + 1
        c = self._config
        return {"enabled": c.enabled, "pressure": c.pressure,
                "tick_interval_seconds": c.tick_interval_seconds,
                "quiet_hours": {"start": c.quiet_hours_start, "end": c.quiet_hours_end},
                "max_nudges_per_day": c.max_nudges_per_day,
                "policies": len(self._db.cadence.list_policies()), "counts": counts,
                "egress": _LOCAL_EGRESS}

    def list_loops(self, principal: Principal, *, include_terminal: bool = False) -> dict[str, Any]:
        return {"loops": [self._loop_dict(loop) for loop in self._db.cadence.list_loops(include_terminal=include_terminal)], "egress": _LOCAL_EGRESS}

    def brief(self, principal: Principal) -> dict[str, Any]:
        from ..cadence.brief import build_brief
        brief = build_brief(self._db)
        return {"date": brief.date, "headline": brief.headline, "open_count": brief.open_count,
                "generated_by": brief.generated_by,
                "items": [{"loop": self._loop_dict(item.loop, with_next_action=False),
                           "next_action": {"kind": item.next_action.kind, "title": item.next_action.title,
                                           "body_markdown": item.next_action.body_markdown}} for item in brief.items],
                "egress": _LOCAL_EGRESS}

    def closeout(self, principal: Principal) -> dict[str, Any]:
        from ..cadence.closeout import build_closeout
        closeout = build_closeout(self._db, now=datetime.now())
        return {"date": closeout.date, "open_count": closeout.open_count, "summary": closeout.summary,
                "recs": [{"loop": self._loop_dict(rec.loop), "severity": rec.severity,
                          "action": rec.action, "reason": rec.reason} for rec in closeout.recs],
                "egress": _LOCAL_EGRESS}

    def apply_closeout(self, principal: Principal, payload: dict[str, Any]) -> dict[str, Any]:
        from ..cadence.closeout import apply_decision
        applied = skipped = 0
        for decision in payload.get("decisions") or []:
            if apply_decision(self._db, str(decision.get("loop_id", "")), str(decision.get("action", ""))): applied += 1
            else: skipped += 1
        return {"applied": applied, "skipped": skipped, "egress": _LOCAL_EGRESS}

    def history(self, principal: Principal, *, limit: int = 50) -> dict[str, Any]:
        return {"nudges": self._db.cadence.list_nudges(limit=limit), "egress": _LOCAL_EGRESS}

    def _required_loop(self, loop_id: str) -> Any:
        loop = self._db.cadence.get_loop(loop_id)
        if loop is None:
            raise NotFound("loop", loop_id)
        return loop

    def snooze(self, principal: Principal, loop_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        self._required_loop(loop_id)
        until = payload.get("until")
        if not until:
            until = (datetime.now() + timedelta(hours=float(payload.get("hours", 24)))).isoformat()
        self._db.cadence.snooze(loop_id, until)
        return self._loop_dict(self._required_loop(loop_id))

    def set_status(self, principal: Principal, loop_id: str, status: str) -> dict[str, Any]:
        self._required_loop(loop_id)
        self._db.cadence.set_status(loop_id, status)
        return self._loop_dict(self._required_loop(loop_id))

    def run_now(self, principal: Principal) -> dict[str, Any]:
        from ..cadence.service import CadenceService as TickService
        result = TickService(self._db, self._config).tick(datetime.now())
        return {"at": result.at, "projected": result.projected, "open_loops": result.open_loops,
                "due": [self._loop_dict(loop) for loop in result.due], "egress": _LOCAL_EGRESS}

    def audit(self, principal: Principal) -> dict[str, Any]:
        from ..cadence.audit import export_audit
        return export_audit(self._db)

    async def get_loop(self, principal: Principal, loop_id: str) -> dict[str, Any]:
        loop = self._db.cadence.get_loop(loop_id)
        if loop is None: raise NotFound("loop", loop_id)
        from ..cadence.llm_action import next_action_for
        result = self._loop_dict(loop, with_next_action=False)
        action = await asyncio.to_thread(next_action_for, loop, llm=_cadence_llm())
        result["next_action"] = {"kind": action.kind, "title": action.title,
                                 "body_markdown": action.body_markdown, "reversible": action.reversible,
                                 "confidence": action.confidence, "generated_by": action.generated_by}
        return result
