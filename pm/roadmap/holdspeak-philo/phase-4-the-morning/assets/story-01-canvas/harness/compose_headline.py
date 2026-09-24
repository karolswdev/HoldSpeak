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

Round six adds the NEXT-DAY fixture (Thu SEP 24 08:02; the producer's
window is SEP 23 17:00 -> SEP 24 08:02, compute_window :144-171, weekday
Tue-Fri days_back = 1). What carries from DAY1 and why:

  o1 Overdue, u1 Unassigned -- YES: _collect_waiting reads the current
      follow-through board (:648-672); no time window.
  l1 Open loop              -- YES: open high loops, no window (:677-681).
  d2 Review decision        -- YES: decisions.list(lifecycle="recorded"),
      no window (:774-783), while the decision stays recorded.
  c1 Commitment due         -- YES: open, due SEP 25 within the 7-day
      horizon (:788-816), priority 110 (due after today).
  m1 Meeting recorded       -- NO: _collect_meetings is windowed
      (:473-516, :488); m1 ended SEP 23 15:30, inside DAY1's window, outside
      DAY2's.
  triage                    -- untouched: the shelf is keyed by brief id
      and item id (:1131, :1157); DAY2 is a new brief with new item ids,
      so every carried row arrives untriaged.

New on DAY2: m2 (ended SEP 23 18:10, inside DAY2's window) and the new
decisions (all recorded after DAY1's generation at SEP 23 17:40, else
the producer would have put them on DAY1).

No DB, no hub: `_compose` reads only its argument. Run with an isolated
HOME:

    HOME=$(mktemp -d) uv run python <this file>

Scratch only; never shipped.
"""
import json

from holdspeak.services.monday_brief_service import BriefItem, MondayBriefService

def item(id, section, text, ref, priority):
    return BriefItem(id=id, section=section, text=text, source_ref=ref, priority=priority)


M1 = item("m1", "changed", "Meeting recorded: Platform sync", "meeting:m1", 50)
M2 = item("m2", "changed", "Meeting recorded: Architecture review", "meeting:m2", 50)
O1 = item("o1", "waiting", "Overdue: Send the vendor review notes", "action_item:a1", 300)
U1 = item("u1", "waiting", "Unassigned: Draft the migration runbook", "action_item:a2", 200)
L1 = item("l1", "waiting", "Open loop: Rate limits for the partner API", "cadence_loop:l1", 100)
C1 = item("c1", "decisions", "Commitment due 2026-09-25: Send the Q4 plan to Dana", "decision:dc1", 110)
D2 = item("d2", "decisions", "Review decision: Adopt the one desk bus", "decision:d2", 200)
DN = item("dn", "decisions", "Review decision: Ship the ingest API behind a flag", "decision:dn", 200)
D3 = item("d3", "decisions", "Review decision: Keep one hub per desk", "decision:d3", 200)
D1 = item("d1", "decisions", "Review decision: Use SQLite for the local store", "decision:d1", 200)

# The decision record's created_at (story 02's recency source). Illustrated:
# the producer does not carry it on a brief item today.
DECISION_CREATED_AT = {
    "decision:dn": "2026-09-24T07:58",
    "decision:d3": "2026-09-24T07:31",
    "decision:d1": "2026-09-23T18:05",
    "decision:d2": "2026-09-22T11:30",
    "decision:dc1": "2026-09-21T10:15",
}

FIXTURES = {
    "day1": [M1, O1, U1, L1, C1, D2],
    # DAY2 carries o1 u1 l1 d2 c1 (m1 does not); m2 + the new decisions.
    "day2_one": [M2, O1, U1, L1, C1, D2, DN],
    "day2_several": [M2, O1, U1, L1, C1, D2, DN, D3, D1],
}


def run(items):
    sections: dict[str, list[BriefItem]] = {}
    for it in items:
        sections.setdefault(it.section, []).append(it)
    headline, finalized = MondayBriefService(db=None)._compose(sections)
    arrival_today = [i for s in ("changed", "broke", "waiting", "decisions") for i in finalized[s]]
    decisions_newest = sorted(finalized["decisions"],
                              key=lambda i: DECISION_CREATED_AT[i.source_ref], reverse=True)
    arrival_story02 = decisions_newest + [i for s in ("changed", "broke", "waiting") for i in finalized[s]]
    return {
        "headline": headline,
        "total": sum(len(v) for v in finalized.values()),
        "sections": {name: [[i.id, i.priority, i.text] for i in its]
                     for name, its in finalized.items() if its},
        "arrival_today": [i.id for i in arrival_today],
        "arrival_story02": [i.id for i in arrival_story02],
        "decisions_created_at": [[i.id, DECISION_CREATED_AT[i.source_ref]] for i in decisions_newest],
    }


print(json.dumps({name: run(items) for name, items in FIXTURES.items()}, indent=2))
