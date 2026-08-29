# HS-147-03 — The honest follow (reconciliation + snapshot identity)

- **Project:** holdspeak
- **Phase:** 147
- **Status:** ready
- **Depends on:** HS-147-01
- **Unblocks:** HS-147-07
- **Owner:** unassigned

## Problem

An arm made at tap time lies the moment the feed moves: a time
shift mints a NEW projection id (`calendar_ingest.py:381-385` hashes
`starts_at`; `replace_projection` deletes the old row,
`db/calendar_events.py:62-123`), a cancelled meeting still fires a
recording, and snapshot re-imports mint fresh uuid4 UIDs
(`calendar_snapshot_service.py:289`) orphaning every link.

## Scope

### In (settled-design D3, X1, D5)

- Post-`replace_projection` reconciliation inside the same ingest
  tick, scoped to the refreshed source only (invariant D3a):
  R1 (id survives → refresh duration/title in place when
  `ends_at`/`title` changed — the id hashes `starts_at` only, so an
  extended meeting is invisible to id identity; counsel finding 5),
  R2 (rebind by `(source_id, uid)` to the occurrence nearest the
  old `starts_at`; update id / next_fire_at / duration / title),
  R3 (uid gone → state `cancelled`, `last_outcome="event_removed"`,
  disabled).
- Invariant D3b (counsel finding 1): replace + reconciliation in
  one transaction, or reconciliation idempotent with caught+logged
  errors — a reconcile crash never kills the ingest tick, and a
  dangling link self-heals next refresh.
- Exception X1: rows in `arming`/`recording` are never touched by
  reconciliation — prove it with a deliberate test.
- The race seam (risk register): a deliberate test covering
  reconcile-vs-conductor interleaving on the same schedule row
  (idle→arming flips during an ingest tick).
- D5: snapshot UIDs become content-deterministic
  (`sha256(title\0starts_at\0ends_at\0location)[:16]
  + "@holdspeak-snapshot"`) at
  `services/calendar_snapshot_service.py:289`; re-confirming the
  same week re-uses uids so links survive re-import.
- Door read side: a cancelled arm (R3) simply disappears from the
  rail with its event; no new UI state needed — assert nothing
  dangles.

### Out

- Any new conductor daemon or tick change (D4 ruled: none);
  stop-at-live-event-end (out of scope by spec); UI (02).

## Acceptance criteria

1. Time-shifted event: the linked schedule follows (new
   `calendar_event_id`, `next_fire_at`, duration, title) and fires
   at the NEW time — proven through a real ingest refresh, not a
   direct DB poke. An end-time-only extension refreshes
   `duration_minutes` under the SAME id (the R1 rule).
2. Removed event: the arm cancels with `event_removed`; nothing
   fires; a healthy second source's arms are untouched during the
   broken/changed source's refresh.
3. X1 holds: an `arming` or `recording` row survives a hostile
   refresh untouched.
4. Snapshot re-confirm of identical content yields identical uids;
   an arm on a snapshot event survives re-import.
5. Recurring-uid rebind picks the nearest occurrence (the pinned
   rule from the risk register).

## Test plan

Ingest-conductor integration tests (two-source fixture: shift,
remove, recur; X1 interleave; the race seam), snapshot service
determinism unit tests, an end-to-end arm→shift→fire test against
the real conductor with engine-factory fakes only.
