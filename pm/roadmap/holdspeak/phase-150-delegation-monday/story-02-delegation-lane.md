# HS-150-02 — The delegation lane (chips, filter, staleness)

- **Project:** holdspeak
- **Phase:** 150
- **Status:** ready
- **Depends on:** HS-150-01
- **Unblocks:** HS-150-06
- **Owner:** unassigned

## Problem

The walk's verdict: PAINFUL — the server filter exists
(follow_through_service.py:128), the UI offers nothing; the only
gesture is scanning truncated fact lines.

## Scope

### In (settled-design D2 + D1's gesture surface)

- Board projection resolves MAPPED owners read-time (the
  request-scoped memo pattern) → cards carry
  person_label/person_relationship_id ONLY when mapped; the owner
  fragment becomes a quiet person chip (click → filter; unmapped
  renders as today); "waiting Nd" from delegated_at ?? created_at.
- Header person chips (mapped persons present on the board +
  "everyone") driving the existing owner filter (server or client
  — the smaller honest diff, stated).
- The MAPPING GESTURE on the card: "map to person…" from the
  card's surface (picker, suggestion-first by case-insensitive
  equality, NOTHING auto-maps) + the Aliases row on the
  relationship detail.
- The _FollowThroughObserver pin: the new projected fields are
  swallowed by the existing board redaction (prove it).
- Shots: mapped chip, filter active, staleness, the gesture — both
  widths, fresh contexts, occlusion tells.

### Out

- Group-by-person (ledgered); brief surfaces (03).

## Acceptance criteria

1. Map once on a real card → the chip appears on every card
   sharing the alias; click filters the board; "everyone" clears.
2. Unmapped owners byte-identical to today; reserved strings offer
   no gesture.
3. Staleness renders honestly (delegated_at ?? created_at, absent
   when neither).
4. The redaction pin: pipeline_events carries none of the
   projected person fields.

## Test plan

door/follow_through projection tests, DoorBoardLane component
tests (chip/filter/staleness/gesture), the redaction pin, live
shots via the phase rig.
