# Phase 148 — The Menu Grammar

**Status:** chartered (0/6).

**Last updated:** 2026-08-29.

## Owner mandate

2026-08-29, in the owner's words: the system is "a little too
sterile… it's always been the intent that… we are making a tribute
to the incredible Amiga OS… if you now go and expand the top menu
toolbar such as Desk, Object, Go, Window and so on, they are really
poor, right?" — ruled a good next step and chartered on "OK, go for
it." Graduates the BACKLOG candidate **AA** row "window-head menus
and keyboard equivalents on the verb registry" alongside the craft
pass. Branch `feat/hs148-menu-glyphs` from main `16477660`.

Standing laws with extra weight: **beautify Workbench 2.0, never a
POS** (this phase IS the beauty pass; the owner sees the MOCK
exhibit before live rollout and the shot exhibit before merge);
deep design not mechanical (three audits ran first; the Amiga
reference grammar is cited canon); sprites never emoji; 2px =
radius not borders; no prose in the UI. The standing questions:
*tired Tuesday?* and *does this operate with joy?*

## Evidence base

- [`assets/audit-census.md`](./assets/audit-census.md) — every seam
  file:line. Headline: **the glyph slot is plumbed but empty
  everywhere**; no toggle type exists; the head menu is hardcoded
  off-registry; the DESK_TOOLS glyphs are data waiting for one
  wiring line.
- [`assets/audit-menus-live.md`](./assets/audit-menus-live.md) +
  [`assets/audit-menu-shots/`](./assets/audit-menu-shots/) (16
  before-shots). Headline: **eight measured defects** — zero glyphs
  in any dropdown while ⌘K renders the same verbs WITH them; a REAL
  keyboard bug (D3: ArrowDown never enters an opened bar menu);
  near-invisible ghosting; keycap chaos.
- [`assets/audit-amiga-reference.md`](./assets/audit-amiga-reference.md)
  — the cited Workbench grammar: text-only items, stipple ghosting
  in the shadow color, the fancy-A keycap glyph flush-right, the
  checkmark lane, HIGHCOMP hover, `»`/`…`; icon columns are a
  Windows 95 import, not Amiga.
- [`assets/settled-design.md`](./assets/settled-design.md) — D1–D5.
  The one open input is the OWNER's: the glyph-column variant
  (A Purist / B Tribute-Plus / C Hybrid, orchestrator recommends C),
  ruled at the story-03 mock exhibit on truthful screenshots.

## Settled design

See the spec. In one breath: the full Amiga grammar lands
variant-independent (stipple ghosting + the verbatim ghosting law,
ghost-reason collapse, drawn keycap wells column-aligned, the
checkmark lane with real aria, the lane alignment law, recessed
separators, `»` and `…`, the D3 keyboard repair, casing + Go
grouping); the glyph column is attribute-driven so A/B/C are all
truthful one-flag states; vocabularies have jurisdictions (unicode
text-glyphs for text surfaces, VerbGlyph SVG for window mechanics,
sprites for objects/dock only — no new sprites, no emoji, and at
last an emoji guard); head + dock menus join the verb registry with
keycaps via a windowId-scoped dispatch (the AA row); no new key
bindings this phase.

## Story status

| ID | Story | Status | Story file | Evidence |
| --- | --- | --- | --- | --- |
| HS-148-01 | The grammar core (DeskMenu + material) | ready | [story-01](./story-01-grammar-core.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-148-02 | The content sweep (glyphs, groups, casing, …) | ready | [story-02](./story-02-content-sweep.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-148-03 | The mock exhibit (the owner's variant gate) | ready | [story-03](./story-03-mock-exhibit.md) | [evidence-story-03](./evidence-story-03.md) |
| HS-148-04 | Head + dock menus on the registry (AA) | ready | [story-04](./story-04-head-dock-registry.md) | [evidence-story-04](./evidence-story-04.md) |
| HS-148-05 | The record book + the emoji guard | ready | [story-05](./story-05-record-book-guards.md) | [evidence-story-05](./evidence-story-05.md) |
| HS-148-06 | The walk and the close | ready | [story-06](./story-06-walk-and-close.md) | [evidence-story-06](./evidence-story-06.md) |

## Where we are

Chartered 2026-08-29 from three same-day audits; the design counsel
ruling and the owner's mock verdict are the two gates ahead of the
close. No story started.

## Decision log

- **2026-08-29 — owner direction:** the menus are the next step
  ("go for it"); the Amiga tribute is the explicit frame; AA's
  menus row graduates into this phase (recorded in BACKLOG.md).
- **2026-08-29 — orchestrator rulings (the spec):** text-surface
  glyphs are the existing unicode set (dock-parity for nouns, one
  glyph language across menu/deck/palette); VerbGlyph owns window
  mechanics; NO new sprites, NO new key bindings; the ghosting law
  adopted verbatim from the Commodore Style Guide; ghost-reason
  collapse (my addition — eight "Select an object" echoes become
  one footer hint); keycaps stay visible when ghosted; variants
  A/B/C are one-attribute states so the owner's verdict is cheap
  forever. The owner may overrule any row.
- **2026-08-29 — counsel design ruling:** recorded here when it
  returns.

## Risk register

- The verbRegistry bound-key-set pin and workMenu DOM pins WILL
  need honest updates (named in the census; builders update tests
  WITH the grammar, never weaken).
- The walk's `go-menu-393.png` pair changes by design — the pair
  review is the point, not a regression.
- Glyph column widens panels ~24px; 393 clamp verified in census
  (innerWidth − 232).
- Unicode glyph rendering varies by platform font; the mock exhibit
  is the check (mono stack pins the set already used by deck/⌘K —
  proven surfaces).
- Asset-clobber law stands for glass runs (141–148 dirs).
