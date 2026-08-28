# HS-146-04 — Rail provenance + seed repairs

- **Project:** holdspeak
- **Phase:** 146
- **Status:** ready
- **Depends on:** HS-146-01
- **Unblocks:** HS-146-05
- **Owner:** unassigned

## Problem

With two calendars feeding one rail, an EVENT row gives no clue which
calendar it came from (`DoorBoardLane.tsx:237-282`,
`DoorUpcomingItem` :39-49 has no provenance field). And three
seeds/walk legs still speak the single-subscription wire.

## Scope

### In (settled design rows 3, 6)

- `_calendar_event_item` projects `source_label`
  (`door_service.py:197-209`); `DoorUpcomingItem.source_label?`.
- The rail renders a mono provenance chip per EVENT row ONLY when
  the projection holds >1 distinct source; text label → hostname →
  "LOCAL". No dedupe — duplicates show with provenance.
- Seed repairs: `test_hs144_door_glass.py` (:222-224 and the
  settings-glass leg), `test_hs145_door_polish_glass.py:370`, and
  `scripts/door_walk_hs144.py` leg 5 (:714-753) rewritten against
  the sources wire + list editor (coordinate with what 01/02 already
  flipped).

### Out

- Docs (05).

## Acceptance criteria

1. One configured source → no chips (single-calendar rail unchanged
   byte-for-byte in the UI grammar).
2. Two sources → every EVENT row carries its source chip; a
   duplicate UID appears twice, distinguishable by chip.
3. Both door glass e2e files green serially; walk leg 5 green
   against the list editor.

## Test plan

`web/src/desk/chair/lanes/DoorBoardLane.test.tsx` (chip rules),
`tests/e2e/test_hs144_door_glass.py`,
`tests/e2e/test_hs145_door_polish_glass.py`, walk leg 5 exercised
via `scripts/door_walk_hs144.py`.
