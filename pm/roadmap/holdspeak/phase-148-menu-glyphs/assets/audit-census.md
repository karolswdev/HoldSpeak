# Phase 148 audit — menu chrome structural census

Read-only opus audit, 2026-08-29, against `feat/hs148-menu-glyphs`
(= main `16477660`). Condensed here with every load-bearing
file:line; the full tables live in the audit transcript. Companion:
[audit-menus-live.md](./audit-menus-live.md) (the before-shots) and
[audit-amiga-reference.md](./audit-amiga-reference.md).

## The machinery

Two layers: primitives `DeskMenuList`/`DeskMenuItem`/`WorkMenuSep`
(DeskMenu.tsx:66-145) and the data-driven `WorkMenu` over
`WorkMenuEntry` (DeskMenu.tsx:149-161, 293-463). The entry union is
`item | sep | sub` — **no checked/toggle/radio type exists**; no
`menuitemcheckbox`/`menuitemradio` role is ever emitted (the one
toggle verb, `desk.toggle-view`, swaps its label instead).

Render sites: mark menu (DeskChrome.tsx:198-214), bar menus
Desk/Object/Go/Window (DeskMenuBar.tsx:53-70,102-111), floor/object/
zone context menus (WorldStage.tsx:313-337 ← floorMenu.ts:32-82),
list-view context (DeskListView.tsx:312-321), window-head menu
(**hardcoded**, DeskWindow.tsx:901-941 — NOT registry-derived; no
keycaps despite CMD+W/CMD+M existing), dock chip menu (Dock.tsx:
272-301, no glyphs/keycaps), create menu (DeskCreateMenu.tsx:52-81).

Keycaps: `Verb.key` (cmd-notation text) → `<kbd
class="desk-menu-key">` (DeskMenu.tsx:280-282,137; css
chrome-menus.css:113-128). Ghosted items suppress keycaps. Keyboard
nav is complete (roving focus, Home/End, type-ahead, submenu
arrows; DeskMenu.tsx:21-63,227-232,374,433) with honest aria.

**The glyph slot is plumbed but empty**: `glyph?: ReactNode` exists
on DeskMenuItem (DeskMenu.tsx:107) and WorkMenuEntry (:155), CSS
`.desk-menu-glyph` exists (16px column, chrome-menus.css:101-104) —
used ONLY by the window-head menu (VerbGlyph SVGs) and the narrow
back-row's hardcoded `◂` (DeskMenu.tsx:400). `Verb` has NO glyph
field (verbRegistry.ts:44-63).

## Content inventory (counts)

| Menu | Items | Keycaps | Toggles | Danger | Seps |
|---|---|---|---|---|---|
| Mark (HoldSpeak) | 7 | 3 | 1 | 0 | 1 |
| Desk | 10 | 2 | 1 | 0 | 1 |
| Object | 9 | 2 (F2, Delete) | 0 | 1 (delete, "danger" group) | 1 |
| Go | 13 | 4 | 0 | 0 | 0 |
| Window | 8 | 4 | 0 | 0 | 2 |
| Floor ctx | ~8 + 2 subs (20 sub-items) | — | 1 | 0 | 1 |
| Zone ctx | 4 | 0 | 0 | 0 | 0 |
| Window head | 3 (hardcoded) | 0 | 0 | 0 | 0 |
| Dock chip | 2 (hardcoded) | 0 | 0 | 0 | 0 |

## Visual material

Panel: min 168px, 2px pad, 1px var(--border), **2px radius (law
held)**, var(--surface-3), z=82 (chrome-menus.css:38-47,92). Items:
28px tall, mono 12px, accent inverse on hover (:60-78). Ghost:
text-faint + inline `<small class="quiet"> · reason</small>`
(DeskMenu.tsx:278; css :143-151). Separator: 1px line (:94-99).
Keycap: margin-left auto, 600 11px mono (:115-128). Bar: 28px,
surface-2, bevel inset (:549-580).

**393**: only Go survives (`display:none` on the others,
chrome-menus.css:781-797); submenus REPLACE the panel with a back
row (NARROW() ≤720, DeskMenu.tsx:164-165,391-412); the other verbs
live only in ⌘K.

## Icon infrastructure

- System sprite sheet: systemSprites.ts + 16 PNGs under
  web/public/desk/sprites/system/ (mark/bell/search/mic/dock/…);
  **no menu-item glyphs exist**; bijection guard
  systemSprites.test.ts (every SYSTEM entry ↔ disk file).
- VerbGlyph.tsx: inline SVG vocabulary, 14×14 viewBox, 1.3px
  stroke, 10 kinds (window verbs + overview/reset) — the existing
  drawn-glyph language.
- DESK_TOOLS already carry unicode `glyph` chars (tools.ts:14-112:
  ⌁ ✦ ▣ ⚙ ⚒ ◉ ↗ ⌘ ◷ § ≋ ∷) rendered in dock/deck
  (`.desk-deck-glyph`, chrome-menus.css:359-364) but NOT in the Go
  menu.
- The shortcut sheet renders physical-look keycaps (well+shadow,
  chrome-menus.css:704-715) — the closest precedent for drawn
  keycaps.
- No emoji-ban guard exists (the sprites law is doctrine, not a
  test).

## Guards / tests / walk

workMenu.test.tsx:54 pins separator/key-column/ghost DOM;
verbRegistry.test.ts:86-106 pins the EXACT bound-key set (breaks if
new keycaps bind); systemSprites.test.ts pins sprite bijection;
DeskMenuBar.test.tsx pins 4 menu ids; windows.test.tsx:231-257 pins
the head menu by role/name. Walk: door_walk_hs144.py:497 (no chrome
before first value), :705-710 (Go→Settings at 1440), :1018-1029
(393 Go menu + `go-menu-393.png` shot).

## Risks (verbatim from the audit)

1. Glyph column widens panels ~24px (min 168→~192); 393 clamp is
   `innerWidth − 232` (DeskMenu.tsx:179).
2. **The alignment trap is real**: the conditional glyph render
   (DeskMenu.tsx:271-275) misaligns labels when glyphs are partial —
   needs an any-glyph-in-menu spacer rule.
3. The narrow back-row must join any always-on glyph column.
4. Test fallout: workMenu.test.tsx DOM pins; verbRegistry
   bound-key-set pin; sprite bijection guard.
5. Walk shots change (pair review), assertions survive.
6. Head-menu registry migration is a DESIGN question: registry
   window verbs act on the FRONT window; the head menu acts on a
   SPECIFIC window id VerbContext doesn't carry.

## Half-built (the good news)

Glyph slot + CSS column + conditional render all exist; VerbGlyph
is one-line-per-kind extensible; ghost+reason works; bar separators
auto-insert on group boundaries; DESK_TOOLS glyphs are data waiting
for one wiring line; the shortcut sheet's keycap look is ready to
adapt.
