# HS-148-05 — The record book + the emoji guard

- **Project:** holdspeak
- **Phase:** 148
- **Status:** ready
- **Depends on:** HS-148-01, HS-148-02, HS-148-04
- **Unblocks:** HS-148-06
- **Owner:** unassigned

## Problem

The dedicated docs story, plus the guard the law never had: the
menu grammar must become written canon (DESK_GRAMMAR.md is the
law book), and the sprites-never-emoji doctrine has no test
(census §4F).

## Scope

### In

- `docs/internal/DESK_GRAMMAR.md` gains the menu-grammar section:
  the lanes, the stipple law (Style Guide quote and citation), the
  keycap wells, checkable aria, `»`/`…`, glyph jurisdictions
  (unicode text-glyphs / VerbGlyph / sprites), the variant
  attribute and the owner's verdict.
- USER_GUIDE touch only if user-visible behavior changed in ways
  the guide describes (menus are largely self-describing — judge
  honestly, smallest true change; the ⌘K parity note may earn a
  line).
- **The emoji guard**: a unit test sweeping menu/deck/tool label +
  glyph sources for emoji codepoints (the allowed set = the
  established unicode glyph vocabulary, explicitly listed) — the
  Phase-129 doctrine finally enforced.
- A menu-grammar guard: lane-law + ghost-collapse pins at the
  component level if story 01's tests left gaps (judge; never
  duplicate).
- Doc-drift guards updated where claims change.

### Out

- Any product code beyond guard tests.

## Acceptance criteria

1. A cold reader of DESK_GRAMMAR can name every lane, the ghost
   law, and the glyph jurisdictions; anchors verified.
2. The emoji guard fails on an injected emoji and passes on the
   real vocabulary.
3. Doc guards green.

## Test plan

The new guard files + `pytest -q tests/unit -k doc` + focused
vitest for any component-level pins.
