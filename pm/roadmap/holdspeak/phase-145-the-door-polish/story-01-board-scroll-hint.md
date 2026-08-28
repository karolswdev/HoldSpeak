# HS-145-01 — The board scroll hint

- **Project:** holdspeak
- **Phase:** 145
- **Status:** ready
- **Depends on:** —
- **Unblocks:** HS-145-03
- **Owner:** unassigned

## Problem

Phase 144 close-counsel concern (1): at 393px the Door board's five
columns sit in a `min-width: 1120px` grid inside a plain
`overflow-x: auto` viewport (`.door-board-viewport`,
`web/src/desk/chair/chair.css:332`; the 480px media block near
`chair.css:541`). Three columns are off-screen with zero visual tell
that they exist. A tired-Tuesday owner on the phone never learns the
board has a WAITING column.

## Scope

### In

- The ruled design ([A1], charter settled design): a rAF-throttled
  scroll/resize listener on the viewport ref
  (`web/src/desk/chair/lanes/DoorBoardLane.tsx:354`) sets
  `data-scroll-hint="none|right|left|both"`; CSS sticky
  `::before`/`::after` edge gradients on `--surface-1`, painted only
  under the matching attribute selector; `position: relative` on the
  viewport. Full spec + behavioral contract:
  `assets/plan-door-polish.md` §Item A.
- Listener cleanup on unmount; no logic when the board is empty (the
  viewport is not rendered then).

### Out

- Any change to column widths, the working-band block, or the board's
  vertical behavior.
- Item B (the calendar affordance) — HS-145-02.

## Acceptance criteria

1. At a width where all five columns fit, no shadow renders (the
   attribute is `"none"` or absent).
2. At 393, load shows the right-edge hint; fully scrolled right shows
   the left-edge hint only; mid-scroll shows both.
3. The gradients use the semantic `--surface-1` token; no hardcoded
   colors.
4. The hint never intercepts pointer events and never fights the
   short-viewport vertical scroll.

## Test plan

- `web/src/desk/chair/lanes/DoorBoardLane.test.tsx`: the hint
  computation proven (extract the pure `scrollLeft/scrollWidth/
  clientWidth → hint` function and unit-test all four states; plus a
  render test that the attribute is present on the populated
  viewport). Focused: `npx vitest run` on the file from `web/`.
- The visual truth at both widths is HS-145-03's shot legs.
