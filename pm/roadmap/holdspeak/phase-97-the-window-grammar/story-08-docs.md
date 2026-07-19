# HS-97-08 — The physics floors, written

- **Project:** holdspeak
- **Phase:** 97
- **Status:** done
- **Depends on:** HS-97-01, HS-97-02, HS-97-03, HS-97-04, HS-97-05, HS-97-06, HS-97-07
- **Unblocks:** HS-97-09

## Problem

Article VIII.2: physics are contracts — drag, resize, raise, persist,
coexist, snap are a floor no change may regress. Phase 97 widened the
floor (placement, order persistence, focus depth, motion, ghost, edge
resize, exposé, one dock) and none of it is written where builders
look. Unwritten floors erode.

## Scope

- In:
  - `docs/internal/DESIGN_SYSTEM.md`: a "window physics floors" section
    naming every contract this phase shipped (token vocabulary only,
    inside the existing guard);
  - `web/README.md`: the add-a-surface path names the placement engine
    and the dock-launcher registration;
  - `docs/internal/ARCHITECTURE*` (frontend doc): the window-grammar
    locks listed beside the Phase 96 gates;
  - doc guards updated where coverage is asserted.
- Out:
  - user-facing docs (the grammar is ambient, not a feature to
    explain); POSITIONING (unchanged by this phase).

## Acceptance criteria

- [x] DESIGN_SYSTEM.md names every Phase 97 floor; the guard passes and
      still fails on raw values.
- [x] web/README and the architecture doc carry the new locks; doc
      guards green.
- [x] `npm run check` + the doc guard suite green.

## Test plan

- `uv run pytest -q tests/ -k "design_system or docs"`; `npm run
  check`.

## Evidence required

- The doc diffs, guard output.
