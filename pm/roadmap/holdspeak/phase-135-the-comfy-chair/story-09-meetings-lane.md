# HS-135-09 — The Meetings lane

- **Project:** holdspeak
- **Phase:** 135
- **Status:** done
- **Depends on:** HS-135-05
- **Unblocks:** HS-135-13
- **Owner:** unassigned

## Problem

Recent meetings and their intelligence state, third lane — the archive
one glance and one click away.

## Scope

### In

- The lane composes recent meetings (date, title, segment count,
  intel/action state badges) to the curated bound; a LIVE meeting, if
  one is running, pins first with its live state (reuse the realtime
  frames the desk already consumes); header-click opens the Meetings
  window; item-click opens that meeting's detail window
  (single-instance).
- Sparse law applies (no filter chrome on the lane — the window owns
  filtering).

### Out

- Recording controls (the hero owns capture — story 11); meeting
  surface changes.

## Acceptance criteria

- [x] Seeded meetings render with truthful badges; a live meeting
  pins first with live state (test with the frame fixture).
- [x] Header and item clicks open the right windows, single-instance.

## Test plan

- `cd web && npx vitest run` — new lane suite + meetings suites
  touched.
