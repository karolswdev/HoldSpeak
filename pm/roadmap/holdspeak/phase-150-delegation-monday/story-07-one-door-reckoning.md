# HS-150-07 — The one-door reckoning (owner-ordered rider)

- **Project:** holdspeak
- **Phase:** 150
- **Status:** done
- **Depends on:** HS-150-06
- **Unblocks:** —
- **Owner:** unassigned

## Problem

The owner's order (2026-08-29, verbatim intent: "nip it in the
bud"): the same functionality must not be reachable through
parallel doors that drift apart. The orphaned-BriefLane find
exposed the class; the census then found (a) a second true orphan
— `FollowThroughLane.tsx`, imported by nothing since 144's
front-door rebuild, still wearing a live board fetch — and (b) a
live era mismatch: the Intelligence pullout's Follow-through view
(the DEEP room: provenance quotes, open-decision/receipts jumps,
reopen, the AttentionDrawer's overdue drill) renders owners as
bare INITIALS with none of the 150 person grammar.

## The ruling (census-based)

The Door board is the TRIAGE door; Intelligence Follow-through is
the DEEP room. Neither retires the other — but the deep room must
speak the same person grammar, and nothing may exist unmounted.

## Scope

### In

1. **Kill the orphan**: delete `FollowThroughLane.tsx` (+ its
   test) with grep proof — superseded by the Door board (144),
   imported by nothing, dead code wearing a live API call.
2. **The deep room learns the grammar**: person chip + staleness
   on cards in FollowThroughView where the owner string is MAPPED,
   composed at the `/api/follow-through/board` ROUTE ADAPTER —
   the exact 150 counsel-ratified pattern (the service stays
   person-free for observers and the MCP tool; enrichment never
   enters `follow_through_service.board()`). No filter, no map
   gesture there — the gesture lives on the Door; the deep room
   displays. Unmapped owners keep initials.
3. **The orphan guard (orchestrator-authored)**: a unit test that
   every non-test component under `desk/chair/lanes/` and
   `desk/pullouts/views/` is imported by live code — the class
   that let BriefLane and FollowThroughLane rot dies.
4. Pins: the route-adapter composition gets the write-count /
   observer / MCP-person-free checks mirrored from
   test_person_overlay (scaled to size).
5. Record book touch: one honest line where entry points are
   described (USER_GUIDE brief/board sections), and
   PEOPLE_INTEGRATION's projection-site list if it enumerates
   composition sites.

### Out

- Retiring the Intelligence Follow-through view (census: it holds
  capabilities the board lacks).
- Any change to the AttentionDrawer drill or the Decisions view.

## Acceptance criteria

1. Grep proof: zero references to FollowThroughLane anywhere.
2. The deep room shows the same person chip + staleness a mapped
   card shows on the Door; unmapped stays initials; MCP board
   output byte-unchanged.
3. The orphan guard is green AND fails when a view import is
   removed (proven both directions).
4. Shots of the deep room at 1440; at 393 the census found the
   pullout host does not operate at narrow AT ALL (pre-existing —
   the navigate event no-ops, the Desk menu is hidden; the 149
   "People at 393" reachability family) — the rig RECORDS that
   posture honestly and goes loud if narrow reachability ever
   ships. The gap joins the ledger, not this story's scope.

## Test plan

Focused vitest (FollowThroughView, guard) + Python route-adapter
pins; rig shots against the real hub; evidence captured.
