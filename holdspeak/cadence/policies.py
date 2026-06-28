"""Default cadence policies (CAD-1-04).

The per-source push rhythms from the design (§4.5/§7.2), seeded on first run and
user-editable later (Phase 2). Phase 1's scheduler reads config-level quiet hours +
the daily cap; these policies are the durable home the richer scheduling (Phase 6)
will consume. Timing values are in minutes.
"""
from __future__ import annotations

from .models import CadencePolicy

_DEFAULTS: list[dict] = [
    {
        "name": "agent_blocker",
        "config": {"source_types": ["agent_question"], "initial_delay_minutes": 5,
                   "repeat_after_minutes": 15, "escalation_after_count": 3, "max_nudges_per_day": 20},
    },
    {
        "name": "meeting_aftercare",
        "config": {"source_types": ["meeting_action", "meeting_decision"], "initial_delay_minutes": 20,
                   "repeat_after_minutes": 240, "escalation_after_count": 2, "max_nudges_per_day": 6},
    },
    {
        "name": "proposal_pending",
        "config": {"source_types": ["proposal"], "initial_delay_minutes": 30,
                   "repeat_after_minutes": 240, "escalation_after_count": 4, "max_nudges_per_day": 8},
    },
    {
        "name": "stale_loop",
        "config": {"source_types": ["meeting_action", "manual"], "initial_delay_minutes": 1440,
                   "repeat_after_minutes": 1440, "escalation_after_count": 2, "max_nudges_per_day": 4},
    },
]


def default_policies() -> list[CadencePolicy]:
    return [CadencePolicy(name=d["name"], config=d["config"]) for d in _DEFAULTS]


def seed_policies(db) -> int:
    """Upsert any default policy that is not already present. Returns # seeded."""
    existing = {p.id for p in db.cadence.list_policies()}
    seeded = 0
    for policy in default_policies():
        if policy.name not in existing:
            db.cadence.upsert_policy(policy)
            seeded += 1
    return seeded
