# HS-148-02 — The content sweep (glyphs, groups, casing, …)

- **Project:** holdspeak
- **Phase:** 148
- **Status:** done
- **Depends on:** HS-148-01
- **Unblocks:** HS-148-03, HS-148-06
- **Owner:** unassigned

## Problem

The data is sterile even where the machinery isn't: zero glyphs in
any dropdown while ⌘K renders the same verbs WITH them (D1 of the
live audit); the Go menu is a 13-row wall with no grouping (D5);
Window-menu casing drifts (D6); dialog-opening items lack `…`; the
mark menu omits Intelligence/People.

## Scope

### In (settled-design D2, D3, D5 non-scope respected)

- `Verb` gains `glyph?: string`; the menubar/floorMenu entry
  builders pass it through; DESK_TOOLS glyphs flow into Go and
  Launch›; the seven create nouns get kind glyphs (unicode,
  deck-style, added to tools/kind metadata so palette + deck + menu
  agree — one glyph language).
- The `data-menu-glyphs` root attribute drives the column per
  variant: `none` (A) / `all` (B) / `launcher` (C, default) —
  launcher = Go, Launch›, New›/create group, the mark menu's app
  section. Verb menus text-pure under C.
- Go grouping: groups on DESK_TOOLS split the 4 keycapped apps from
  the 9 tools (auto-separator fires); casing sweep (Window menu);
  ellipsis audit across all menus (Style Guide rule); mark menu
  gains Open Intelligence / Open People.
- NO new key bindings (blank keycap lanes are honest; the bound-key
  census pin untouched).

### Out

- Grammar mechanics (01); the exhibit (03); head/dock (04).

## Acceptance criteria

1. Under `launcher`: Go and Launch› rows lead with their deck
   glyphs; New›/create rows lead with kind glyphs; Object/Window
   stay text-pure; under `all`/`none` the column obeys everywhere —
   pinned by tests per variant.
2. The same noun shows the SAME glyph in menu, deck, and ⌘K
   (dock-parity pinned for at least the four primary apps).
3. Go shows the 4/9 group separator; Window casing is uniform;
   every dialog-opener ends `…`.
4. verbRegistry tests green with the new field; bound-key set
   byte-identical.

## Test plan

web: floorMenu.test.ts + DeskMenuBar.test.tsx + a new
menuGlyphs.test.tsx (variant matrix, parity pins); verbRegistry
test untouched-key proof — focused vitest.
