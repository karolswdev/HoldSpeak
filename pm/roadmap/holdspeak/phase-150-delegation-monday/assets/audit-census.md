# Phase 150 audit — the owner-string + Monday Brief census

Read-only opus audit, 2026-08-29 (night), against
`feat/hs150-delegation-monday` (= main `c9b0cd25`). Every claim
file:line in the transcript; the load-bearing condensation here.
Companion: [audit-monday-walk.md](./audit-monday-walk.md).

## The two decisive answers

1. **NO code anywhere matches owner strings to People
   relationships** (exhaustive grep: zero) — the INTEGRATION
   contract is clean to build on. The owner field is free TEXT on
   action_items (schema.py:102, indexed :218),
   decision_commitments (:225), cadence_loops (:1647),
   decision_records (:1106); written by five paths (intel
   extraction via parsing.py:20,122-127 — values like "Me",
   "Remote", free names; the delegate verb
   follow_through_service.py:401-409; manual edit
   meetings.py:926-960; commit_decision :253-331; cadence upsert).
   Rendered ONLY as a truncatable fact-line fragment on Door cards
   (DoorBoardLane.tsx:216-221) and in cadence CLI output.
2. **The Monday Brief IS PERSISTED** — monday_briefs +
   monday_brief_items + monday_brief_item_shelf
   (schema.py:2181-2211); generate() is once-per-calendar-day
   idempotent (monday_brief_service.py:89-155). THEREFORE
   People-derived sections may NEVER be written there (the 138 law
   + the 149 F2 ledger item) — read-time overlay only.

## Half-built gifts

- The server-side owner filter EXISTS end-to-end
  (follow_through_service.py:128 → the SQL clauses :492-494,
  :513-515; HTTP follow_through.py:37; MCP tools.py:340) — no UI
  consumes it.
- one_on_one_brief (149) is the ready per-person digest source;
  the request-scoped person-index memo (door_service.py:215-250)
  and resolve_relationship_by_series are the exact patterns to
  clone for owner mappings.
- The People-cards overlay + _FollowThroughObserver redaction
  (follow_through_service.py:20-48, 213-229) already guard the
  board's People content; _MeetingPersonRedactor guards meetings.
- Lanes: _lane (follow_through_service.py:547-577) — unassigned =
  pending-review OR ownerless; staleness exists only as
  cadence stale_score (scoring.py:59-84) or created_at; **no
  delegated_at exists** — the delegate verb records WHO but never
  WHEN.
- The Brief renders in BriefView.tsx (Intelligence) + BriefLane.tsx
  (chair; returns null when no brief exists — the first-load
  absence); collectors :189-523 are all person-blind;
  _collect_waiting builds a FollowThroughService WITHOUT the
  people_projection (People commitments absent from the brief
  today).

## Drift surfaces for builders/orchestrator

test_door_read_model / test_monday_brief_service /
test_brief_collectors / test_door_transport_parity /
test_people_service; the walk script (nine legs); the api-surface
manifest on any new route; the schema grep pin (any new column
must carry NO person reference — delegated_at as a bare timestamp
is lawful).

## Unknowns recorded honestly

decision_records.owner write paths untraced (no
db/decision_records.py; only decisions.py); no intel/extractor.py;
cards without cadence loops have NO staleness signal beyond
created_at.
