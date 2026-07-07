"""Telemetry-free local audit export (CAD-8).

A complete, inspectable, LOCAL snapshot of the cadence engine's state — every loop,
its evidence, and the nudge history — so "what did Qlippy do, and why" is provable
after the fact without any telemetry leaving the machine. Pure read; produces a dict
(JSON-serializable) and writes only where the caller points it.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional


def export_audit(db, *, now: Optional[datetime] = None, nudge_limit: int = 500) -> dict:
    """A local-only snapshot of all cadence state. No network, no telemetry."""
    now = now or datetime.now()
    loops = db.cadence.list_loops(include_terminal=True)
    by_status: dict[str, int] = {}
    by_source: dict[str, int] = {}
    for loop in loops:
        by_status[loop.status] = by_status.get(loop.status, 0) + 1
        by_source[loop.source_type] = by_source.get(loop.source_type, 0) + 1
    from ..intel.providers import endpoint_egress

    return {
        "generated_at": now.isoformat(),
        "egress": endpoint_egress(
            cloud=False, label="Local audit — nothing leaves this machine"
        ),
        "totals": {"loops": len(loops), "by_status": by_status, "by_source": by_source},
        "loops": [
            {
                "id": l.id, "source_type": l.source_type, "source_id": l.source_id,
                "title": l.title, "status": l.status, "priority": l.priority,
                "needs_review": l.needs_review, "owner": l.owner, "project": l.project,
                "stale_score": l.stale_score, "nudge_count": l.nudge_count,
                "created_at": l.created_at, "updated_at": l.updated_at,
                "snoozed_until": l.snoozed_until,
                "evidence": [
                    {"kind": e.kind, "ref_id": e.ref_id, "deep_link": e.deep_link}
                    for e in l.evidence
                ],
            }
            for l in loops
        ],
        "nudges": db.cadence.list_nudges(limit=nudge_limit),
        "policies": [{"name": p.name, "enabled": p.enabled} for p in db.cadence.list_policies()],
    }
