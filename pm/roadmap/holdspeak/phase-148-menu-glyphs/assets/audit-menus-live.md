# Phase 148 audit — the live before-state (menus on real glass)

Opus walk agent, 2026-08-29, real hub, isolated HOME, seeded desk.
Sixteen before-shots in [`audit-menu-shots/`](./audit-menu-shots/).
Companion to [audit-census.md](./audit-census.md).

## Minute-one impression (the agent's verdict, kept verbatim)

"Structurally complete and functionally correct... but visually
STERILE. Every row is naked monospace text with no leading glyph,
no visual weight differentiation. The Go menu lists 13 programs as
a flat text wall... The menus read as a developer's debug list, not
an OS's application menu."

## The eight measured defects

- **D1 — zero glyphs in any dropdown** (the primary finding). The
  ⌘K palette renders the SAME verbs WITH their DESK_TOOLS glyphs;
  the menus are the only face that refuses them.
- **D2 — keycap inconsistency**: Desk 2/10, Go 5/13, Window 5/8,
  Object 2/9 — and Object's keycaps HIDE when ghosted, so the
  common no-selection state shows zero keycaps at all.
- **D3 — REAL KEYBOARD BUG**: ArrowDown on an open bar menu does
  NOT move focus into the panel (the WorkMenu `autoFocus` is not
  passed from the menubar path) — keyboard-only users cannot walk
  menu items from the bar.
- **D4 — ghost contrast near-invisible**: `--text-faint` on
  `--surface-3` barely reads; the ghost reason (`small.quiet`) is
  fainter still; the no-selection Object menu is a wall of
  near-invisible text.
- **D5 — Go menu has no grouping**: 4 primary apps (keycapped) and
  9 config/inspect tools sit in one undifferentiated block; the
  DESK_TOOLS table has no groups so the auto-separator never fires.
- **D6 — casing drift in Window menu**: "Cycle windows" vs "Cycle
  Windows (Reverse)"; "Close window" vs "Snap Left".
- **D7 — 393 is Go-only** (by design) — the one narrow menu must
  carry the craft alone.
- **D8 — the mark menu is a shortcut list, not a system menu** (7
  items; no identity, no Intelligence/People).

Also observed: no window-head menu BUTTONS exist (the head menu is
right-click only, shot 10); the object/zone context menus could not
be triggered from the list rows under Playwright (the GL canvas owns
contextmenu; list rows wire it separately — noted for the walk leg).

## Shot index (all 1440×900 unless noted)

00 desk · 01 Desk menu · 02 Object menu all-ghosted · 03 Go menu ·
04 Window menu ghosted · 05 hover state · 10 Settings window (no
head menus) · 20 bar at 393 · 21 Go menu 393 · 22 ⌘K palette 393
(glyphs present!) · 30 floor · 31 floor context · 32 New› submenu ·
33 Launch› submenu · 34 Window menu with a live window · 37 mark
menu.

## Where craft lands hardest (the agent's ranking, adopted)

1. Go menu glyphs (the data already exists in DESK_TOOLS — one
   wiring line per the census).
2. Desk create-verb kind-glyphs (the desk already draws these kinds
   as sprites).
3. Keycap coverage (or deliberate no-keycap rulings) + the
   ghosted-keycap-visibility question.
4. Go menu grouping separator (4 apps / 9 tools).
5. Object verb-action glyphs (identity even when ghosted).
6. Window layout-verb directional glyphs.
7. The D3 keyboard fix (autoFocus from the bar path).
8. Ghost contrast raise.
Lower: casing sweep; mark-menu enrichment; chevron.
