# HS-145-03 — Shots and the close

- **Project:** holdspeak
- **Phase:** 145
- **Status:** done
- **Depends on:** HS-145-01, HS-145-02
- **Unblocks:** —
- **Owner:** unassigned

## Problem

Polish that is not seen on real glass is a claim, not a fact. The
phase closes only on live shots of both affordances at both widths,
the reusable cold walk still green, and a sweep judged against the
inherited baseline.

## Scope

### In

- **Shots against the real hub** (isolated HOME, real build,
  Playwright): 1440 and 393; the board hint in its `right`/`both`/
  `left` states at 393 and its absence at 1440; the empty rail in
  both empty states (no-calendar → connect affordance;
  configured-but-quiet → no nag). Every shot shows what its name
  claims; the orchestrator looks at every shot before the owner does.
- **The cold walk**: `scripts/door_walk_hs144.py` re-run — all seven
  legs must still pass; the walk's door aggregate assertion now
  expects `calendar_configured` (via the HS-145-02 `mcp_walk.py`
  update if shared, or the walker's own check).
- **Full sweep** (`-n auto`, isolated HOME, readable-run +
  dw-capture pair) with verdict vocabulary: baseline-exact, zero
  branch-new.
- `final-summary.md`, phase status, README cadence updates.

### Out

- The attended speech leg (owner-ordered only, never unattended).
- Push/PR/merge — the owner's word gates it, for this branch AND the
  Phase 144 line beneath it.

## Acceptance criteria

1. The shot set delivered to the owner covers both items, both
   widths, honest states, no byte-identical "different" shots.
2. `door_walk_hs144.py` passes 7/7 on a fresh HOME.
3. Sweep verdict: baseline-exact, zero branch-new (or every
   non-baseline name triaged in the evidence).
4. `final-summary.md` exists; story/phase/README statuses truthful.

## Test plan

- The walk script run + the full suite sweep ARE the tests; captured
  via `dw evidence capture` with the readable-run pairing noted.
