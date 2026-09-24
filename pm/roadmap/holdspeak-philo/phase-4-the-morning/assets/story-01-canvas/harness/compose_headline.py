"""PHILO-4-01 canvas: DAY1's headline from the REAL producer.

Builds DAY1's four items in the sections the producer gives them
(monday_brief_service.py: `Meeting recorded` -> changed :507, `Open loop`
-> waiting :708, `Review decision` -> decisions :768, `Commitment due`
-> decisions :812) and runs them through the real `_compose`. No DB, no
hub: `_compose` reads only its argument. Run with an isolated HOME:

    HOME=$(mktemp -d) uv run python <this file>

Scratch only; never shipped.
"""
import json

from holdspeak.services.monday_brief_service import BriefItem, MondayBriefService

ITEMS = [
    BriefItem(id="m1", section="changed", text="Meeting recorded: Platform sync",
              source_ref="meeting:m1", priority=50),
    BriefItem(id="l1", section="waiting", text="Open loop: Rate limits for the partner API",
              source_ref="cadence_loop:l1", priority=100),
    BriefItem(id="c1", section="decisions", text="Commitment due 2026-09-25: Send the Q4 plan to Dana",
              source_ref="decision:dc1", priority=110),
    BriefItem(id="d2", section="decisions", text="Review decision: Adopt the one desk bus",
              source_ref="decision:d2", priority=200),
]

sections: dict[str, list[BriefItem]] = {}
for item in ITEMS:
    sections.setdefault(item.section, []).append(item)

headline, finalized = MondayBriefService(db=None)._compose(sections)
print(json.dumps({
    "headline": headline,
    "sections": {name: [i.text for i in items] for name, items in finalized.items()},
}, indent=2))
