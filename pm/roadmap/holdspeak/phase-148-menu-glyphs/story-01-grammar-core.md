# HS-148-01 — The grammar core (DeskMenu + material)

- **Project:** holdspeak
- **Phase:** 148
- **Status:** ready
- **Depends on:** —
- **Unblocks:** HS-148-02, HS-148-03, HS-148-04
- **Owner:** unassigned

## Problem

The menus are grammatically incomplete and carry one real bug: no
toggle/check entry type or aria (audit-census §machinery), ghosting
is near-invisible faint text with per-row reason echoes
(audit-menus-live D4 + the orchestrator's repetition observation),
keycaps are bare text that VANISH when ghosted, the glyph column
misaligns when partial (DeskMenu.tsx:271-275), and ArrowDown from
an open bar title never enters the panel (D3 — keyboard-only users
cannot walk the menus).

## Scope

### In (settled-design D1)

- Stipple ghosting (2×2 shadow-tone checkerboard overlay, ~45%
  opacity, item box only) replacing the faint-text treatment;
  ghost-reason collapse (uniform-reason panels render ONE quiet
  footer hint); keycaps render stippled-but-visible on ghosted rows.
- Drawn keycap wells (the shortcut-sheet treatment,
  chrome-menus.css:704-715, adapted to menu scale), modifier
  symbols + character, flush-right column-aligned.
- `WorkMenuEntry` item gains `checked?: boolean | "exclusive"` with
  `menuitemcheckbox`/`menuitemradio` aria and VerbGlyph
  square-check/circle-dot marks; the lane law — any panel with a
  glyph/check reserves the lane on EVERY row incl. the narrow
  back-row; `desk.toggle-view` becomes the first checkable.
- Recessed separators (shadow+shine pair); `»` submenu indicator.
- The D3 repair: bar-path menus autoFocus their first item.
- Test updates WITH the grammar: workMenu.test.tsx DOM pins,
  DeskMenuBar.test.tsx, new cases for checkable aria, lane law,
  ghost collapse, autoFocus.

### Out

- Any glyph/keycap CONTENT wiring (02); variants attribute (02);
  head/dock menus (04); guards/docs (05).

## Acceptance criteria

1. A ghosted item is unmistakably stippled and never hidden; a
   uniform-ghost panel shows one hint, not N echoes; its keycaps
   remain legible.
2. Checkable items carry honest aria and marks; the lane never
   misaligns a mixed panel (pinned by test).
3. ArrowDown from an open bar title walks the items (pinned).
4. Keycap wells render column-aligned at 1440 and in the 393 Go
   menu; no panel exceeds its clamp.
5. All existing menu behavior (type-ahead, submenus, Escape,
   ghost refusal) regression-free.

## Test plan

web: workMenu.test.tsx (extended), DeskMenuBar.test.tsx,
floorMenu.test.ts, windows.test.tsx menu block — focused vitest.
