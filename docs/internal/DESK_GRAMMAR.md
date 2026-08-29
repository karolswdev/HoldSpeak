# The Desk Grammar

The written law of the desk's world layer, forged in Phase 105
(Workbench) from the owner's standard: an OS, not a gimmick — Workbench
2.0 on steroids. This document records FACT about the shipped tree, in
the Constitution's voice; where a rule and the code disagree, one of
them is a defect to fix consciously, never to paper over. Cited by
stories as law. Read [`AGENT_BRIEF.md`](AGENT_BRIEF.md) before any UI
work; the [Constitution](CONSTITUTION.md) outranks both.

## 1. The icon law (HS-105-01)

1. World art is 64×64 pixel art rendered **1:1** — never fractionally
   scaled, tilted, or size-jittered. Integer-true or absent.
2. One uniform cell for every kind (`sceneModel.ts`: SPRITE 64, LIFT
   80, OBJ_W 104). Importance is expressed by state, never by scale.
3. Distinct silhouette per kind; color supports, never substitutes.
   A directory is a drawer.
4. Every sprite ships as a REAL state set on disk — rest, `_sel`
   (brightened, rimmed), `_stale` (desaturated) — derived by
   `web/scripts/gen-sprite-states.py`. Runtime filters never
   substitute for a state image.
5. Badges ride only NAMED live fields (the audited source map in the
   phase directory): member count bottom-right, freshness (48h)
   top-right, needs-you top-left, posture marks bottom-left. Anchors
   sit on the art at rest and on the box when selected. Absent data
   renders as absence.
6. Default homes grid deterministically (the Clean Up rule); a user
   drag parks anything anywhere and the arrangement is sacred.
7. Density has altitudes: a compact desk with no saved view choice
   leads with the List above 16 objects; an explicit choice always
   wins.

Guard: `web/src/desk/gl/__tests__/iconCell.test.ts`. Art recipe:
`web/ICON-DISCIPLINE.md`.

## 2. The selection and open law (HS-101 round 9 + 105)

Mouse: single click SELECTS (cell box + inverted label chip);
double-click OPENS. Touch/pen: tap opens. Escape closes the front
card only. Windows COEXIST — object cards, drawer windows, and Info
cards are all real desk windows on the one panel system (rect,
stacking, dock chips, restoration).

## 3. The drawer law (HS-105-03)

1. A zone IS a drawer icon in the uniform cell — never a tray, never
   instruction prose.
2. Open = a real window flying from the gesture point; several
   coexist; dive survives only as the context menu's Focus verb.
3. Two views, one truth: Icons (the cell contract) and List (Name /
   Kind / Modified, sortable both ways). THE WINDOW REMEMBERS — view,
   sort, direction per zone (`hs.desk.zone-views`), the open set
   (`hs.desk.zone-windows`), rect via panels — and restores.
4. Take out un-files through the real membership DELETE. Empty says
   "Empty".

Guard: `zoneWindow.test.tsx`.

## 4. The drop law (HS-105-02)

1. The matrix is CONTRACT DATA (`dropMatrix.ts`): a target kind
   declares what it accepts and the NAMED verb; unlisted pairs are
   inert. Components never hardcode kind pairs.
2. A viable target lights via its real `_sel` image; the verb tag
   rides the cursor and states exactly what release does — the
   consent surface.
3. A drop that would run a model instead HOLDS the content as run
   material beside the run verb; the human presses it.
4. A drop is an entrance, not a move: the dragged object returns
   home.

Guard: `dropMatrix.test.ts`.

## 5. The Info law (HS-105-04)

1. ONE Info card for every kind and for drawers, derived from
   `infoContract.ts` — a kind declares its footprint measure and its
   property keys; no kind hand-builds its Info.
2. Identity's name edits in place through the existing update paths.
3. Properties (tooltypes) exist ONLY where a real update path backs
   them; the guard pins the whole vocabulary (today:
   `recipe.runs_on`). Growth is one real field at a time.
4. Receipts wait for a per-object journal route (the kernel's feed);
   until then the section does not render.

Guard: `infoContract.test.ts`.

## 6. The verb law (HS-105-05)

1. A verb is a REGISTERED capability (`verbRegistry.ts`); every face
   renders the registry. Faces today: the menu bar and the ⌘K shelf
   (Go ≡ DESK_TOOLS, pinned). The wire face lands with the kernel's
   userland dispatch — never before its consent model (Article V).
2. Menus GHOST with the reason; they never hide. The system admits
   what it can do.
3. An open menu dismisses on any outside pointer-down and on Escape
   from anywhere.

Guard: `verbRegistry.test.ts`.

## 7. The menu grammar (HS-148)

The menus speak the Amiga's text discipline with a drawn glyph column
where it is earned. Four faces render from one source: the menubar
(Desk, Object, Go, Window), the floor/object/zone context menus, the
window-head menu, and the dock chip menu — all derive from the ONE
verb registry (`verbRegistry.ts`) through data adapters; no face
hardcodes a menu label. The Commodore Amiga UI Style Guide is the
cited reference grammar (`assets/audit-amiga-reference.md`).

### 7.1 Lane layout

Every menu item has two lanes:

- **Left lane (glyph / check).** If ANY entry in a panel carries a
  glyph or is checkable, every row in that panel reserves a fixed-width
  `desk-menu-glyph` column — the lane alignment law
  (`DeskMenu.tsx:panelHasLane`). The lane carries one of: a checkable
  mark (VerbGlyph `check` or `dot`), a text glyph, or an empty spacer.
  A panel whose entries have no glyphs and no checkables omits the lane
  entirely.
- **Right lane (keycap wells).** Each shortcut renders as drawn keycap
  wells (`desk-menu-well` inside `desk-menu-keycaps`): every modifier
  symbol (⌘ ⇧ ⌃ ⌥) and the final key each get their own well,
  flush-right and column-aligned across the panel — the fancy-A's seat,
  honored (`DeskMenu.tsx:KeycapWells`).

### 7.2 Stipple ghosting

A menu item that cannot run is ghosted, never hidden — the system
admits what it can do. Ghosting is a 2x2 checkerboard stipple
(`is-ghost` class) in the panel's own ground color that punches holes
in the text. The Commodore UI Style Guide law, adopted verbatim:

> "Whenever a menu or menu item is inappropriate or unavailable for
> selection, it should be ghosted. Never allow the user to select
> something that does nothing in response."
>
> — Commodore, *Amiga User Interface Style Guide* (1991), ch. 4

Keycaps stay VISIBLE on ghosted rows (stippled with the row) — a
shortcut's existence is taught precisely where the user is learning it.

### 7.3 Ghost-reason collapse (the majority rule)

Every ghosted item carries a reason string. When the single most common
ghost reason appears on three or more ghosted rows in a panel, it
collapses to a quiet panel-footer hint (`desk-menu-ghost-hint`) and the
matching per-row echoes are suppressed. Rows carrying a DIFFERENT reason
keep their per-row display (`DeskMenu.tsx:collapseGhostReason`). On a
tie only the first-encountered reason collapses.

### 7.4 Checkable entries

A `WorkMenuEntry` with `checked?: boolean | "exclusive"` earns ARIA
`menuitemcheckbox` (boolean) or `menuitemradio` ("exclusive")
(`DeskMenu.tsx:WorkMenuRows`). The lane renders:
- Checked boolean: a VerbGlyph `check` (square-check SVG).
- Exclusive: a VerbGlyph `dot` (circle-with-inner-dot SVG).
- Unchecked: an empty spacer (the lane reservation holds).

The conditional role (counsel should-fix) means the primitive never
emits a wrong checkable role on a non-checkable entry
(`DeskMenuItem`, `WorkMenuRows`).

### 7.5 Submenu and ellipsis conventions

- `»` is the submenu indicator (`desk-menu-submark`); `▸` is retired.
- `…` ends every item that opens a dialog or window (the Amiga ellipsis
  rule). Verified: `Reset to seed…`, `Find receipt…`.

### 7.6 Glyph vocabulary jurisdictions

Three glyph languages, each with a bounded scope:

| Language | Scope | Examples | Source |
|---|---|---|---|
| Unicode text-glyphs (geometric / dingbat) | Menus, deck (⌘K palette), and palette — text surfaces | `⌁` `✦` `▣` `⚙` `⚒` `◉` `↗` `⌘` `◷` `§` `≋` `∷` `▤` `◈` `⬡` `◎` `⟁` `⊞` `◰` `▷` `⊙` `✎` `⌶` `⧉` `↦` `⌫` `◆` `⊕` | `tools.ts:DESK_TOOLS`, `tools.ts:KIND_GLYPH`, `verbRegistry.ts` glyph fields |
| VerbGlyph SVG (14x14 stroke) | Window mechanics: head menus, snap/maximize directionals, checkable marks | minimize, maximize, restore, close, check, dot | `components/window/VerbGlyph.tsx` |
| Pixel sprites | Objects on the desk and the dock ONLY | Object icons, dock app icons | `systemSprites.ts`, `gen-sprite-states.py` art |

No emoji, ever. The guard is `__tests__/emojiGuard.test.ts` (HS-148-05).

### 7.7 The variant attribute and panel context

The root `#desk-next` element carries `data-menu-glyphs` with one of
three values (`DeskApp.tsx:menuGlyphsVariant`):

- `none` — no glyph column in any menu (the Purist).
- `launcher` — glyph column ONLY in panels whose
  `data-menu-context="launcher"` (Go, New, Launch submenus) — dock
  parity for nouns, Amiga purity for verbs (the Hybrid, default).
- `all` — glyph column in every menu (the Tribute-Plus).

Every `WorkMenu` panel declares `data-menu-context` on its `<nav>`
element; the default is `"verb"`. Discrimination lives in the panel
declaration plus one render check; it is not scattered across CSS
selectors.

### 7.8 Registry derivation for head and dock menus

The window-head menu and the dock chip menu derive their entries FROM
the verb registry through `windowMenuAdapter.tsx` — labels and keycaps
come from `verbById`, glyphs are VerbGlyph SVGs, and `onSelect`
dispatches to per-window store methods (the scoped context: the
registry's `window.*` verbs act on the front window; the head menu acts
on a SPECIFIC window via its own minimize/maximize/close callbacks). No
hardcoded menu labels exist (the `windowMenuAdapter.tsx` adapter is the
single derivation path).

### 7.9 Recessed separators

Separators are recessed 1px rules: shadow + shine pair in the 2.0 bevel
system (`desk-menu-sep`, `WorkMenuSep`).

Guard: `__tests__/workMenu.test.tsx`, `__tests__/menuGlyphs.test.tsx`,
`__tests__/emojiGuard.test.ts`.

## 8. Standing remainders (recorded, not waived)

Clean up / Snapshot verbs + free member arrangement inside drawer
windows (need drag-reorder); cross-window drag re-filing; the orb as
a drop target; multi-object drops; per-object receipts (kernel journal);
the artifact "paper" sprite reads poorly at cell scale (regenerate per
the icon discipline).
