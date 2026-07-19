# HS-98-08 — The surface floors, written

- **Project:** holdspeak
- **Phase:** 98
- **Status:** done
- **Depends on:** HS-98-07
- **Unblocks:** HS-98-09

## Problem

Phase 96 wrote the tokens as canon and Phase 97 wrote the physics as
floors. The surface idiom needs the same treatment or the next surface
will be built the old way.

## Scope

- In:
  - DESIGN_SYSTEM.md "The surface idiom" finalized as Article VIII
    floors (the six rules, each tied to its guard or walk leg);
  - `web/README.md` add-a-surface path amended: cores compose the
    surface kit, page grammar forbidden (the guard named);
  - the frontend architecture doc's locks list carries the seam guard
    beside the Phase 96/97 gates.
- Out:
  - new capabilities.

## Acceptance criteria

- [ ] Docs land with every value a token name; doc guards green.
- [ ] `npm run check` + python suite green.

## Test plan

- Doc/design-system guards; `npm run check`.

## Evidence required

- Doc diffs, guard output, suite output.
