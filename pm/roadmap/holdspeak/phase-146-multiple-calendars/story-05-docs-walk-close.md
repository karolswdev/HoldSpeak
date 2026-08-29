# HS-146-05 — The walk and the close

- **Project:** holdspeak
- **Phase:** 146
- **Status:** done
- **Depends on:** HS-146-02, HS-146-03, HS-146-04, HS-146-06, HS-146-07
- **Unblocks:** —
- **Owner:** unassigned

> **Amended 2026-08-28 (owner order):** the docs scope moved to the
> dedicated thorough-documentation story [HS-146-06](./story-06-the-calendar-book.md);
> this story is now the walk and the close only, and depends on it
> (docs after features, before closeout — the house law).

## Problem

Multi-calendar is a claim until the shots, the cold walk, and a
baseline-judged sweep say otherwise.

## Scope

### In

- **The adapter leg** (amended 2026-08-28 at the HS-146-07 fold-in):
  the shot set and walk also cover the snapshot-import flow (fixture
  screenshot → review list → confirmed events on the rail as the
  SNAPSHOT source).
- **Shots against the real hub**, both widths, eyeballed by the
  orchestrator first: the list editor (empty / one / two sources,
  egress chips), the rail with two sources (provenance chips, a
  cross-feed duplicate), the single-source rail (no chips).
- **Cold walk**: `scripts/door_walk_hs144.py` 7/7 with the reworked
  leg 5.
- **Close sweep** (readable + dw-capture PAIR), verdict vocabulary
  baseline-exact / zero branch-new; full a/b/c triage of anything
  non-baseline.
- `final-summary.md`; phase/README cadence updates; one counsel
  close pass before the flip.

### Out

- Push/PR/merge — the owner's shot verdicts + merge word gate it.

## Acceptance criteria

1. Shot set delivered; no byte-identical pairs.
2. Walk 7/7; sweep baseline-exact zero branch-new (or triaged).
3. Counsel verdict recorded; final-summary exists; statuses truthful.

## Test plan

The walk + sweep ARE the tests; captured via `dw evidence capture`
with the readable-run pairing noted in the triage note.
