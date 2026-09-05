# HS-175-05 — The week brief

- **Project:** holdspeak
- **Phase:** 175
- **Status:** backlog
- **Depends on:** HS-175-02, HS-175-04
- **Unblocks:** HS-175-06
- **Owner:** unassigned

## Problem

The Monday brief's window (monday_brief_service.py:89-108,
`compute_window()`) uses a 1-day lookback (3 on Monday back to Friday
17:00). The brief has zero calendar-event awareness. It ran once (1839
items on 2026-08-24) and never again. The arc says: "the week as the
brief's frame" — the brief should cover the full calendar week: what
happened (meeting Watch entities, Watch changes, commitments) AND what
is coming (calendar events, due commitments).

## Scope

- In:
  - Widen `compute_window()` to the full calendar week (Monday 00:00
    to Sunday 23:59, or the owner's configured work-week); the brief
    says "This week" not "Since yesterday."
  - A new collector reading `calendar_events` for the coming week:
    meetings count, next event title and time, events with armed
    recordings.
  - A new collector reading meeting Watch entities (HS-175-04) for the
    past week: meetings with new decisions, meetings with new
    commitments, commitments due this week.
  - The existing collectors (Watch changes, pipeline events, breakage)
    widen to the week window.
  - The brief's shade section (from Phase 171) shows the week frame:
    "This week: 4 meetings, 12 Watch items changed, 2 commitments
    due Fri."
  - The brief still recurs on its own cadence loop (Phase 171); this
    story changes the window, not the recurrence.
- Out:
  - Daily briefs in addition to the weekly frame (the brief is one
    per day; the window widens, the cadence stays).
  - Calendar write-back.
  - External calendar API reads (the brief reads from the local
    `calendar_events` table).

## Acceptance criteria

- [ ] `compute_window()` returns the full calendar week (Monday to
      Sunday or the owner's configured work-week); the brief says
      "This week" (Article VI: honest frame).
- [ ] A calendar-events collector returns meetings count, next event,
      events with armed recordings for the coming week.
- [ ] A meeting-Watch collector returns meetings with new decisions
      and commitments for the past week.
- [ ] The existing collectors (Watch changes, pipeline events,
      breakage) use the widened week window.
- [ ] The brief's shade section shows the week frame at both widths
      (Article IX.2).
- [ ] Zero egress (Article III); all reads from local tables.

## Test plan

- Unit: `HOME=$(mktemp -d) uv run pytest -q tests/ -k week_brief`
  - `compute_window()` returns Monday-to-Sunday on any day of the week.
  - The calendar-events collector returns events in the week range.
  - The meeting-Watch collector returns decisions/commitments counts.
  - The empty state: "Nothing material this week" (Article VI).
- Integration: the rig seeds calendar events, meetings with intel, and
  commitments; generates the brief; verifies the week frame in the
  output.
- Manual: the owner's brief shows the week frame in the shade.

## Notes / open questions

- The existing `compute_window()` uses a business-day lookback. The
  week frame is a different shape: it looks back to Monday and forward
  to Sunday. Propose keeping the lookback for "what happened" and
  adding a look-ahead for "what's coming" — two halves of the same
  week.
- The brief's "what's coming" section must not repeat events that
  already appeared in "what happened" (dedup by calendar_uid).
