# HS-99-07 — The chrome floors, written

- **Project:** holdspeak
- **Phase:** 99
- **Status:** done
- **Depends on:** HS-99-02..06
- **Unblocks:** HS-99-08

## Problem

Every phase that shipped chrome without writing it as floors got
rebuilt the old way within a phase. The ladder, the bar, the control
skin, the scrollbars, the menu vocabulary, and the dock life need
their contract.

## Scope

- In:
  - DESIGN_SYSTEM.md: "The chrome ladder" finalized as Article VIII
    floors (tonal depth, the bar anatomy, control skin, scrollbars,
    menu vocabulary, dock indicators, tint formulas, easing family) —
    each tied to its guard or walk leg;
  - PROZILLAOS_STUDY.md cross-linked as the provenance record
    (Article X);
  - web/README + frontend architecture locks updated.
- Out:
  - new capabilities.

## Acceptance criteria

- [ ] Docs land, every value a token name; doc/design guards green.
- [ ] `npm run check` + python suite green.

## Test plan

- Doc/design guards; `npm run check`.

## Evidence required

- Doc diffs, guard output, suite output.
