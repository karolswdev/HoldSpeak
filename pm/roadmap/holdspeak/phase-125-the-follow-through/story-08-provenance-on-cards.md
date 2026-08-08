# HS-125-08 — Provenance on every card

- **Project:** holdspeak
- **Phase:** 125
- **Status:** done
- **Depends on:** HS-125-02
- **Unblocks:** HS-125-09
- **Owner:** unassigned

## The thesis (the bar)

When the board says "you owe the API design by Thursday," there must
be a path to the exact meeting segment where that was promised. The
infrastructure exists: `resolve_provenance_segment()` resolves a
verified timestamp to a `segments` row, and
`DecisionLifecycleService.get_moment()` returns the decision's source
moment. This story surfaces that provenance on every board card.

### What changes

1. `FollowThroughService.board()` enriches each card with a
   `provenance` field:
   - `meeting_id` — the source meeting
   - `segment` — the resolved transcript segment (if available)
   - `moment` — the decision moment (if from a commitment)
   - `available` — boolean; honestly `false` when provenance cannot
     be resolved

2. Uses `resolve_provenance_segment()` for action items with
   `source_timestamp`, and `get_moment()` for decision-backed cards.

3. Cards that cannot resolve provenance get `available: false` —
   honest about the gap, never invented.

### What this story does NOT do

- Render provenance in the UI (HS-125-09).
- Add new provenance resolution logic — uses existing infrastructure.

## Acceptance criteria

1. A card from an action item with `source_timestamp` has a resolved
   `segment` with speaker and text.
2. A card from a decision commitment has a `moment` from
   `get_moment()`.
3. A card with no resolvable provenance has `available: false`.
4. Provenance resolution never raises — failures are honest.

## Test plan

- Unit: action with valid `source_timestamp`, verify segment resolved.
- Unit: decision commitment, verify moment resolved.
- Unit: action with no timestamp, verify `available: false`.
