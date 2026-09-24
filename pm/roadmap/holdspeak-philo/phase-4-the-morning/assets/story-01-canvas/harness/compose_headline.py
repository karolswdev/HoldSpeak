"""PHILO-4-01 canvas: DAY1's rows, order and headline from the REAL producer.

Round five. Builds DAY1's six items with the texts, sections and
priorities the producer gives them (monday_brief_service.py):

  `Meeting recorded`  -> changed,   priority 50  (_MEETING_PRIORITY, :85, :511)
  `Overdue`           -> waiting,   priority 300 (follow-through lane, :655-672)
  `Unassigned`        -> waiting,   priority 200 (follow-through lane, :655-672)
  `Open loop`         -> waiting,   priority 100 (high loop, :703, :712)
  `Review decision`   -> decisions, priority 200 (:765-771)
  `Commitment due`    -> decisions, priority 110 (due after today, :809-815)

and runs them through the real `_compose` (:327-387: per-section priority
sort :331-335, headline). It then prints the two Arrival orders:

  today    -- ChairHome.tsx:801 concatenates changed, broke, waiting,
              decisions (decisions LAST), then BRIEF_CAP = 3.
  story 02 -- the decisions section first, newest first by the decision
              record's `created_at` (illustrated below); the other
              sections keep the producer's order.

No DB, no hub: `_compose` reads only its argument. Run with an isolated
HOME:

    HOME=$(mktemp -d) uv run python <this file>

Scratch only; never shipped.
"""
import json

from holdspeak.services.monday_brief_service import BriefItem, MondayBriefService

ITEMS = [
    BriefItem(id="m1", section="changed", text="Meeting recorded: Platform sync",
              source_ref="meeting:m1", priority=50),
    BriefItem(id="o1", section="waiting", text="Overdue: Send the vendor review notes",
              source_ref="action_item:a1", priority=300),
    BriefItem(id="u1", section="waiting", text="Unassigned: Draft the migration runbook",
              source_ref="action_item:a2", priority=200),
    BriefItem(id="l1", section="waiting", text="Open loop: Rate limits for the partner API",
              source_ref="cadence_loop:l1", priority=100),
    BriefItem(id="c1", section="decisions", text="Commitment due 2026-09-25: Send the Q4 plan to Dana",
              source_ref="decision:dc1", priority=110),
    BriefItem(id="d2", section="decisions", text="Review decision: Adopt the one desk bus",
              source_ref="decision:d2", priority=200),
]
# The decision record's created_at (story 02's recency source). Illustrated:
# the producer does not carry it on a brief item today.
DECISION_CREATED_AT = {"decision:d2": "2026-09-22T11:30", "decision:dc1": "2026-09-21T10:15"}

sections: dict[str, list[BriefItem]] = {}
for item in ITEMS:
    sections.setdefault(item.section, []).append(item)

headline, finalized = MondayBriefService(db=None)._compose(sections)

arrival_today = [i for s in ("changed", "broke", "waiting", "decisions") for i in finalized[s]]
decisions_newest = sorted(finalized["decisions"],
                          key=lambda i: DECISION_CREATED_AT[i.source_ref], reverse=True)
arrival_story02 = decisions_newest + [i for s in ("changed", "broke", "waiting") for i in finalized[s]]

print(json.dumps({
    "headline": headline,
    "sections": {name: [[i.id, i.priority, i.text] for i in items]
                 for name, items in finalized.items() if items},
    "arrival_today": [i.id for i in arrival_today],
    "arrival_story02": [i.id for i in arrival_story02],
}, indent=2))
