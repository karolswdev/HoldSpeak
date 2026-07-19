# HS-99-04 — Scrollbars and menus

- **Project:** holdspeak
- **Phase:** 99
- **Status:** done
- **Depends on:** HS-99-01
- **Unblocks:** HS-99-08

## Problem

We ship zero scrollbar CSS — every scrolling window shows the
browser's scrollbar, the loudest webpage tell there is. And our only
menu vocabulary is the room menu; rows and heads have no consistent
popover grammar.

## Scope

- In:
  - product-wide custom scrollbars (webkit + `scrollbar-width`/
    `scrollbar-color`): thin pill thumb on a transparent track,
    token-colored, hover-brightening; the GL canvas untouched;
  - the shared menu vocabulary: one `DeskMenu` popover primitive
    (desk transient material, tint-hover rows, divider, shortcut
    slot) consumed by the existing room menu, the HS-99-02 head menu,
    and the dock chip context menu (close/minimize from the chip);
  - per-corner radius against the anchor (the borrowed touch);
  - Escape/click-away/focus behavior per the Phase 96 menu pattern.
- Out:
  - nested submenus (no current need; rider).

## Acceptance criteria

- [ ] Every scrolling surface shows the pill scrollbar at 1440 (shots
      of Meetings archive + Settings); Firefox fallback set.
- [ ] Room menu, head menu, and dock chip menu all render from the
      one primitive; keyboard behavior green (a11y suite).
- [ ] `npm run check` + python suite green.

## Test plan

- vitest menu tests; shots; a11y suite; `npm run check`.

## Evidence required

- Shots, suite output.
