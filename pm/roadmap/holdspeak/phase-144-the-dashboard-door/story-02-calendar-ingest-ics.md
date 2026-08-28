# HS-144-02 — Calendar ingest (ICS first)

- **Project:** holdspeak
- **Phase:** 144
- **Status:** done
- **Depends on:** HS-144-01
- **Unblocks:** HS-144-04
- **Owner:** unassigned

## Problem

The hub cannot know the owner's future meetings: zero
calendar-protocol code exists (audit A §2.2 — no ICS/CalDAV/OWA
anywhere; the Phase 135 "ICS first" ruling was never implemented).
`activity_meeting_candidates` are stale browser-history heuristics.
Without this story, "upcoming meetings" means only recording
schedules — a front door that cannot say "next meeting in 45 min."

This story executes the Phase 135 ruling. It is also the charter's
named amputation point (settled design §4): if the owner cuts it, the
upcoming rail ships scheduled-recordings-only and nothing else in the
phase changes.

## Scope

### In

- **One calendar subscription** — a file path or an HTTPS URL to an
  `.ics` feed, stored in settings (one subscription this phase; the
  plural is a follow-on). Every text input gets the speak-to-fill mic.
- **A bounded parser** into a `calendar_events` projection table
  (declarative schema, `holdspeak/db/schema.py`, additive-only):
  uid, title, starts_at, ends_at, location/meeting_url if present,
  last_seen_at, subscription revision. Recurring events expand to a
  bounded horizon (14 days). Malformed events are SKIPPED with a
  named receipt — a hostile feed can never crash the hub or blank the
  Door (risk register). Prefer stdlib/self-contained parsing; if a
  dependency (`icalendar`) is genuinely needed, it enters
  `pyproject.toml` visibly and the evidence names why.
- **Refresh cadence**: on hub boot and a bounded periodic re-read
  (reuse the conductor-tick pattern, `scheduled_recording_conductor.py`
  precedent); a URL fetch carries the **egress badge** truth — the
  subscription surface names that the URL is fetched and when
  (one badge, never prose). No auth headers, no credential storage
  this phase.
- **The Door aggregate extends**: HS-144-01's `upcoming` timeline
  merges calendar events with scheduled-recording fires behind the
  SAME shape, server-side.
- Focused tests: parser against real-world and hostile `.ics`
  fixtures (folding, timezones, RRULE expansion bound, garbage),
  refresh honesty (a vanished event vanishes), merge ordering,
  file-vs-URL sources.

### Out

- OWA/Playwright scraping, CalDAV, Google Calendar API (unruled).
- Multiple subscriptions, calendar WRITES, invitation actions.
- Any linkage that auto-creates scheduled recordings from events
  (a follow-on candidate, not this phase).
- Glass (HS-144-04 renders the rail).

## Acceptance criteria

- [ ] A file-path subscription and an HTTPS subscription both project
  events into `calendar_events`; re-read updates and removes honestly
  (tests).
- [ ] A hostile/malformed feed skips bad events with named receipts
  and never crashes boot or the Door route (tests with garbage
  fixtures).
- [ ] RRULE expansion is bounded to the horizon; timezone-bearing
  events land at correct UTC instants (tests).
- [ ] `GET /api/door` `upcoming` merges calendar events +
  scheduled-recording fires in one ordered timeline (test).
- [ ] The subscription settings surface carries the egress badge for
  URL feeds and a mic on the text input (verified in HS-144-04's
  shots).

## Test plan

- `HOME="$(mktemp -d)" uv run --python 3.13.11 pytest -q tests/ -k
  "calendar or ics"` plus the door aggregate suite from HS-144-01.
