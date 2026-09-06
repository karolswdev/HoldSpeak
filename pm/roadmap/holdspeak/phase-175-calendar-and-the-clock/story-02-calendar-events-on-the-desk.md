# HS-175-02 — Calendar events on the desk

- **Project:** holdspeak
- **Phase:** 175
- **Status:** done
- **Depends on:** HS-175-01
- **Unblocks:** HS-175-03, HS-175-05
- **Owner:** unassigned

## Problem

The calendar ingest pipeline exists (calendar_ingest.py,
calendar_ingest_conductor.py:146+) and the `calendar_events` table
(schema.py:3490-3506) is populated by the conductor, but the desk
never reads the events as material. The owner's desk has 0
calendar_events visible. The `next` seam (project_service.py:426)
mentions "next scheduled recording or calendar event" as intent but
does not surface it. Calendar events are ingested and stored, but
invisible.

## Scope

- In:
  - Calendar events from the ingest pipeline surface on the desk as
    readable material: a WEEK section on the desk or in the Room
    showing upcoming events as ledger rows, built to the HS-175-01
    artboard.
  - The `next` seam in `GET /api/desk/needs-you`
    (project_service.py:426) returns the next calendar event alongside
    the next scheduled recording; the Room header shows the next-event
    token.
  - An API route returning calendar events for a date range (the
    ingest conductor already writes them; the route reads from the
    table).
  - The empty state when no calendar source is connected (the 146
    adapter verb as the action; Article VI: honest at zero).
- Out:
  - New calendar ingest sources (the 146 adapter is sufficient).
  - Calendar write-back (creating events from the desk).
  - Real-time sync (the conductor's periodic refresh is sufficient).

## Acceptance criteria

- [ ] Calendar events from the ingest pipeline appear on the desk as
      readable ledger rows matching the HS-175-01 artboard (Article
      IX.2).
- [ ] The `next` seam returns the next calendar event; the Room header
      shows the next-event token.
- [ ] An API route returns calendar events for a date range; response
      includes title, starts_at, ends_at, location, meeting_url,
      source_label.
- [ ] The empty state says "No calendar connected" with the 146
      adapter verb (Article VI.1; UX-CANON.md rule A.8 — no counters
      of zero).
- [ ] Zero egress (Article III); events are read from the local
      `calendar_events` table, never fetched live.

## Test plan

- Unit: `HOME=$(mktemp -d) uv run pytest -q tests/ -k calendar_events_desk`
  - The API route returns events for a date range.
  - The `next` seam returns the next event.
  - The empty state when no calendar source exists.
- Integration: the rig boots a hub with a seeded ICS source, runs the
  conductor, and verifies events appear in the desk API response.
- Manual: the owner's desk shows calendar events after connecting a
  calendar source via the 146 adapter.

## Notes / open questions

- The `calendar_events` table already has `source_id` and
  `source_label` (multi-source since HS-146-01). The desk face should
  show the source label as a provenance chip on each event row.
- The date-range API may need pagination if the owner has many events;
  propose a 7-day default window (the week frame from HS-175-05) with
  optional start/end query params.
