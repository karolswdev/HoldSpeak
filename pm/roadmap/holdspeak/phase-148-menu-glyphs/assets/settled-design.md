# Phase 148 settled design — the menu grammar

The design-beat spec, ruled by the orchestrator 2026-08-29 from the
three audits (census / live before-state / Amiga reference); one
Opus counsel ruling taken before builders ride; **the glyph-column
variant is the OWNER's verdict at the mock exhibit** — everything
else here is settled. Builders implement, they do not redesign.

## The one sentence

The desk's menus keep the Amiga's text discipline and gain its full
grammar — stipple ghosting, a drawn keycap column, a checkmark
lane, recessed separators, `»` and `…` — plus a restrained glyph
column exactly where items are nouns with existing identities,
subject to the owner's mock verdict.

## D1 — the grammar core (variant-independent)

- **Stipple ghosting** replaces faint-text: a 2×2 shadow-tone
  checkerboard overlay (CSS repeating-conic trick, ~45% opacity,
  the item's box only; tune sparser if dense on dark). The Style
  Guide law adopted verbatim: a menu item that does nothing is
  ALWAYS ghosted, never hidden.
- **Ghost-reason collapse:** when every item in a panel shares one
  ghost reason (the no-selection Object menu — eight "Select an
  object" echoes today), render ONE quiet panel-footer hint; mixed
  panels keep per-row reasons. Keycaps stay VISIBLE when ghosted
  (stippled with the row) — today they vanish, hiding the
  shortcut's existence exactly when the owner is learning it.
- **Drawn keycaps:** the `<kbd>` text column becomes drawn keycap
  wells — the shortcut sheet's physical-key treatment
  (chrome-menus.css:704-715) adapted to menu scale; modifier
  symbols (⌘ ⇧ ⌃) + character, flush-right, column-aligned
  (the fancy-A's seat, honored).
- **The checkmark lane:** `WorkMenuEntry` item gains
  `checked?: boolean | "exclusive"`; aria `menuitemcheckbox` /
  `menuitemradio`; square check for toggles, circle-dot for
  mutual-exclude (VerbGlyph extensions, 14×14 stroke). Any panel
  containing a checkable reserves the lane on EVERY row (the Amiga
  indentation cue). `desk.toggle-view` becomes the first honest
  checkable (two exclusive states).
- **The lane law (alignment):** if ANY entry in a panel carries a
  glyph or check, every row reserves that fixed lane — the
  conditional-render misalignment trap (DeskMenu.tsx:271-275) dies.
  The narrow back-row participates.
- **Separators** go recessed: 1px shadow + 1px shine-below (the 2.0
  bevel pair on the house tokens).
- **Submenu indicator** becomes `»`; **ellipsis audit**: every item
  that opens a window/dialog ends `…` (Style Guide verbatim).
- **The D3 keyboard repair:** opening a bar menu focuses the first
  item (`autoFocus` from the menubar path) — ArrowDown works from
  the title. A real bug, not craft.
- **Hover** stays accent-inverse (already HIGHCOMP-spirited);
  polish only, no rework.
- **Casing sweep** (Window menu drift) and **Go grouping**: groups
  on DESK_TOOLS split the 4 keycapped apps from the 9 tools so the
  existing auto-separator fires.

## D2 — the glyph question (the OWNER's gate)

Three variants, mocked on REAL glass (the grammar implemented; the
column driven by a `data-menu-glyphs` root attribute so every mock
is a truthful screenshot, not a drawing):

- **A — the Purist:** full grammar, no left column anywhere (the
  literal Amiga).
- **B — the Tribute-Plus:** grammar + glyph column in every menu
  (verbs included).
- **C — the Hybrid (orchestrator's recommendation):** glyph column
  ONLY in launcher contexts — Go, Launch›, New›/create, the mark
  menu's app section — where items are PROGRAMS and KINDS that
  already own glyph identities in the dock, deck, and ⌘K palette
  (dock-parity for nouns); verb menus (Object, Window, context
  verbs) stay text-pure with the checkmark/keycap grammar (Amiga
  purity for verbs).

C ships as the default after the exhibit is delivered; the owner's
verdict at the exhibit (or any later flinch) flips the attribute and
re-ships — the implementation cost of the other variants is zero by
construction.

## D3 — glyph vocabulary jurisdictions (settled)

- **Unicode text-glyphs** (the existing DESK_TOOLS/deck set: ⌁ ✦ ▣
  ⚙ ⚒ ◉ ↗ ⌘ ◷ § ≋ ∷ + new kind glyphs for the seven create
  nouns) are the language of TEXT surfaces: menus, deck, palette.
  One glyph per noun, identical across all three — the palette
  already renders them; menus join it.
- **VerbGlyph SVG** (14×14 stroke) is the language of window
  MECHANICS: head menus, snap/maximize directionals.
- **Pixel sprites** stay the language of OBJECTS and the dock. No
  new system sprites this phase — the sprite-bijection guard sleeps.
- No emoji, ever (and story 05 finally builds the guard the law
  never had).

## D4 — window-head + dock menus (the AA graduation)

Registry-derived entries with keycaps (⌘W/⌘M finally shown where
they act) and VerbGlyph glyphs. The window-id problem (registry
window verbs act on the FRONT window; head menus act on a SPECIFIC
window) resolves by a scoped context: the head menu builds its
entries from the registry's window verbs with an explicit
`windowId` override in the dispatch — one adapter, no parallel verb
system. Dock chip menu gets the same treatment.

## D5 — deliberate non-scope

No new global key bindings (the coverage gaps become honest blank
keycap lanes; new bindings = a ledgered follow-up — the bound-key
census pin stays untouched). No mark-menu identity rework beyond
adding Intelligence/People (D8 stays mostly ledgered). No sprite
forging. No 393 structural changes (the lone Go menu simply wears
the new grammar).
