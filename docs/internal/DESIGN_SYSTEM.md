# The HoldSpeak Design System

**Status:** canon since Phase 96 (owner-directed; built with the vendored
`design-system` and `ui-styling` skills). Governed by the
[Constitution](CONSTITUTION.md), Articles VII (the interface serves) and
VIII (native-grade craft). Every value in this document is a token name;
raw values live only in `web/design-tokens.json`.

## The token architecture (HS-96-01)

One source of truth: `web/design-tokens.json`, three layers per the
skill's architecture, generated into `web/src/styles/tokens.css` and the
TS mirror `web/src/lib/tokens.gen.ts` by
`node web/scripts/generate-tokens.cjs`.

| Layer | Prefix / home | Rule |
|---|---|---|
| Primitive | `--p-*` | Raw values with doc strings. Components never reference these. |
| Semantic | the Signal vocabulary (`--bg`, `--surface-*`, `--text*`, `--accent*`, status ramps, `--shadow-ink-*`, `--wash-*`) | What components use for color, type, spacing, radius, elevation, motion, focus. |
| Component | `--desk-*`, `--glow-*`, `--zone-tint-*` | The Desk OS chrome: the z ladder, window physics, glass/fills, per-kind glows. |

The z ladder (component layer, one home):
`--desk-z-stage` (-1) < `--desk-z-canvas` (0) < `--desk-z-world-overlay`
(25) < `--desk-z-chrome` (30) < `--desk-z-dock-under` (40) <
`--desk-z-window-base` (42+, focus-ordered) < `--desk-z-dock` (80) <
`--desk-z-transient` (81) < `--desk-z-popover` (82).

## The locks (HS-96-02)

- `npm run tokens:check` — the generated CSS/TS must match the JSON.
- `npm run tokens:gate` — no raw color, z-index, or ms literal in
  component CSS; exceptions live in `web/token-allowlist.json`, each with
  a reason, and STALE entries fail the gate (the list only shrinks).
- Both run first in `npm run check` and in CI's web checks.
- The TS mirror means window physics and GL palettes cannot drift from
  the CSS ladder: they import `tokens.gen.ts`.

## The state contract (HS-96-03)

Two grammars cover every interactive element:

- **Focus:** the global `:focus-visible` rule (accent outline,
  `--focus-outline-width`/`--focus-outline-offset`) applies everywhere;
  a component may widen the offset, never remove the outline.
- **Pressed:** one settle — `translateY(1px)`, compositor-only — via the
  shared `:active` families in `global.css` (`.btn`) and `desk.css` (the
  chrome list). The orb, being a circle, presses inward
  (`scale(0.92)` on its core).

### Component matrices

Values are token names; "—" inherits the default row.

**Signal Button (`.btn`, variants `--primary/--secondary/--ghost/--danger`)**

| State | Background | Text | Border | Extra |
|---|---|---|---|---|
| default | per variant (`--accent` / `--surface-2` / transparent / `--danger-fill`) | `--text-on-accent` or `--text` | `--border` (secondary) | min-height 44px |
| hover | variant hover (`--accent-hover`, `--surface-hover` wash) | — | — | |
| focus-visible | — | — | — | global accent outline |
| active | `--accent-press` (primary); all variants settle `translateY(1px)` | — | — | |
| disabled | `--disabled-bg` | `--disabled-fg` | `--disabled-border` | no hover/press |
| busy | — | — | — | the Signal spinner; `aria-busy`; pointer blocked |

**Desk chip (`.desk-chip`, incl. quiet)**

| State | Treatment |
|---|---|
| default | `--desk-glass` fill family, `--border`, `--radius-pill` |
| hover | `--surface-hover` wash |
| focus-visible | global accent outline |
| active | settle `translateY(1px)` |
| disabled | `--disabled-fg`, no hover/press |

**Window verbs (`.desk-window-verb`, `.desk-window-close`)**

| State | Treatment |
|---|---|
| default | transparent, `--text-muted`, `--radius-sm` |
| hover | `--wash-2` fill, `--text`; close: accent-tinted fill |
| focus-visible | global accent outline |
| active | settle `translateY(1px)` |

**Dock (`.desk-dock-main`, `.desk-dock-x`, `.desk-dock-reset`)**

| State | Treatment |
|---|---|
| default | chip on the `--desk-glass` bar; front chip wears `--accent-tint`; parked chip dims |
| hover | `--surface-hover`; the ✕ reveals (width transition, `--duration-short`) |
| focus-visible | global accent outline; the ✕ also reveals on focus |
| active | settle `translateY(1px)` |

**The orb (`.desk-orb`)**

| State | Treatment |
|---|---|
| idle | accent ring, `--accent-glow` halo |
| recording | `--accent-glow-strong` pulse (reduced-motion: static strong halo) |
| busy | disabled; no press |
| focus-visible | global accent outline |
| active | core `scale(0.92)` |

**Window frame (`DeskWindowFrame` shell)**

| State | Treatment |
|---|---|
| rest | `--desk-window-fill`, `--border`, `--elev-2`, `--radius-lg` band |
| focused (front) | z = `--desk-z-window-base` + order; `--elev-3` |
| dragging | no transitions; head cursor grabbing |
| maximized | fixed band inside `--desk-snap-top`/`--desk-snap-bottom` margins |
| minimized | parked (display none), dock chip dims |
| sheet (≤720px) | bottom sheet, `--radius-5` top corners |

**Inputs (Signal `TextInput`/`TextArea`/`Select`)**

| State | Background | Border |
|---|---|---|
| default | `--field-bg` | `--field-border` |
| focus | — | `--field-focus-border` + global outline |
| disabled | `--disabled-bg` | `--disabled-border` |
| invalid | — | `--danger-signal` + message via `InlineMessage` |

**Switch / Tabs / StatusPill / InlineMessage**

- Switch: track `--surface-3` → checked `--accent`; thumb `--text`;
  focus-visible outline on the control; never color-only (label text
  states the position).
- Tabs: active tab `--accent` underline + `--text`; inactive
  `--text-muted`; focus-visible outline; roving arrow keys (HS-96-05).
- StatusPill: `--ok/--warn-signal/--danger-signal/--info` soft fills;
  always paired with text, never color alone.
- InlineMessage: status soft fill + `--radius-md`; `role="status"` or
  `role="alert"` per tone.

**GL world states (desk objects and zones, from `tokens.gen.ts`)**

| State | Treatment |
|---|---|
| rest | kind glow (`--glow-*`) at 0.5 alpha; bob per `objMotion` |
| hover | glow 0.82 + additive highlight; cursor grab |
| selected | dashed accent ring at 1.15 scale; glow 0.55 |
| new | accent glow 0.95; NEW badge; ring pulse ×3 |
| editing | settled (no bob); glow 0.9 |
| dragging | z 20 within the layer; motion paused |
| drop-ready (zone) | lift −4px, scale 1.04, emphasized panel |

## The window physics floors (HS-97)

Article VIII.2: physics are contracts — once shipped, a floor no change
may regress. The Phase 97 grammar, all proven by the `desk_gl_walk.py`
legs (`placement`, `arrangement`, `depth`, `frame`, `switcher`,
`shelf`) on the production bundle:

- **Land well.** A window opening without a persisted rect is seated by
  `placeWindow` (exported beside `snapForPointer`): seeded at its CSS
  default home, moved off other windows' title bars (head occlusion
  dominates a min-overlap scan, then overlap area, then distance from
  home), always whole inside the working band between
  `--desk-snap-top` and `--desk-snap-bottom`. A persisted rect is
  clamped into the band on open (`clampIntoBand`) and otherwise
  untouched. The cascade survives only at true saturation.
- **Remember everything.** `hs.desk.panels` persists `{rects, order,
  max}`; windows rehydrate at their remembered plane (`presentPanel`);
  a closed window leaves the order (`retirePanel`) so a reopen
  presents. Minimize is session-scoped by design and never persisted.
- **Depth is focus.** Exactly one front window (the last open,
  non-minimized id in the order) wears `--desk-window-shadow` plus a
  1px `--desk-window-keyline` ring; the rest wear
  `--desk-window-shadow-rest`. The dock's front chip mirrors the rule.
- **Motion tells the story.** Open springs in; close scales/fades out;
  minimize contracts into the window's own dock chip and restore
  returns from it (WAAPI, compositor-only transform/opacity). All of
  it instant under reduced motion.
- **Hands on the frame.** The head drags; a snap region shows its
  landing tile live (`SnapGhost`) and the release lands exactly on it;
  the frame resizes from its left/right/bottom edges and both bottom
  corners (`resizeEdge`); double-click on the head toggles maximize.
- **Switch visibly.** Exposé (the dock's ⊞ verb, Ctrl+ArrowUp) fans
  every open window into a non-overlapping pick grid (`exposeLayout`);
  minimized windows join as dimmed cards; Escape cancels. Ctrl+`
  cycles MRU with a transient strip naming every open window and the
  landing target.
- **One shelf.** The dock, centered on the bottom edge, is the only
  shelf: launcher verbs (registered through `announceLauncher`), the
  record orb at its center, a chip per open window, the overview and
  reset verbs. No floating pills. Window identity in the head is icon
  plus title — the eyebrow is demoted (Article VII.1).

## The surface idiom (HS-98)

Window interiors are one visual product with the desk — these six
rules are Article VIII floors, like the physics above: once shipped,
no change may regress them. The Signal page grammar (`page-grid`,
`span-*`, `Panel`, `data-list`/`data-row`, `signal-eyebrow`,
permanent `button-row` walls, modal confirms) is forbidden inside
`pages/cores/` — mechanically, by
`tests/unit/test_native_surfaces_guard.py`. The Phase 98 conversion
ledger CLOSED with HS-98-07: the allowlist is empty and the guard
refuses reopening it. Every core composes the surface kit
(`web/src/desk/surface/`), which owns the six rules (proven by the
`reflow` walk leg and the closeout's `surfaces` leg on the production
bundle):

1. **One material, no double chrome.** The window frame is the only
   chrome. Content sits directly on `--desk-window-fill`;
   `SurfaceSection` groups with a hairline (`--border` over `--wash-1`)
   and a quiet label (`--desk-surface-label-size`, `--text-muted`) —
   never a nested card, never an eyebrow restating the title.
2. **The window is the viewport.** `.desk-surface-body` is a size
   container (`container-type: inline-size`, name `surface`). Kit
   layouts (`SurfaceSplit`, `MetricStrip`) reflow via `@container
   surface` queries at the one narrow breakpoint, **560px** (a raw px
   constant in `surface.css` — container queries cannot read custom
   properties; this line is its canon) — a core must never consult a
   viewport media query.
3. **A denser scale.** Rows sit on `--desk-surface-row-h` with
   `--desk-surface-row-pad-x`; body copy is `--desk-surface-body-size`,
   details `--desk-surface-detail-size`, section labels
   `--desk-surface-label-size`. Sections breathe at
   `--desk-surface-section-gap`, rows at `--desk-surface-gap`.
4. **Rows say what they mean.** `SurfaceRow` renders title + detail
   slots; times pass through `humanTime`, labels through `deSnake`,
   values through `presentValue` — an unknown is omitted, never
   printed as "unknown"/"0" theater.
5. **Verbs have homes.** Primary verbs ride `SurfaceVerbs` (one bar at
   the surface top); row verbs live in the row's verb slot and reveal
   on hover/focus-within (always visible under coarse pointers and
   reduced motion); destructive verbs use the inline two-step
   `ConfirmVerb` (arm → fire, self-disarming), not a modal.
6. **One state grammar.** `SurfaceState` renders loading, error, and
   empty as one quiet treatment — glyph plus a short label in the
   product voice, retry as a dense ghost button, no prose.

The kit inherits the HS-96-03 state contract (global focus ring, the
1px pressed settle) and adds nothing of its own.

## The chrome ladder (HS-99)

The OS chrome program (owner-directed; provenance and the full
borrow/embrace/skip inventory in
[PROZILLAOS_STUDY.md](PROZILLAOS_STUDY.md), MIT-attributed). All
seven rules SHIPPED in Phase 99 and are Article VIII floors — no
change may regress them. Verification gotchas that are themselves
canon: custom scrollbars must be verified HEADED (the headless shell
suppresses them), and the standard `scrollbar-width/color` properties
stay Firefox-scoped (`@supports not selector(::-webkit-scrollbar)`)
because modern Chromium disables `::-webkit-scrollbar` styling when
they are set. The bare-control inheritance means NO component may
ship a raw `select`/`input`/`textarea` inside the desk shell — the
foundation catches it mechanically.

1. **Depth is tonal.** The window ladder:
   `--desk-window-head-fill` (head, one step above) >
   `--desk-window-fill` (body) > `--desk-window-rail`
   (toolbars/rails) > `--desk-window-well` (inputs/wells, below).
   Surfaces separate by tone; borders are reserved for the window's
   own outline and hairlines within content.
2. **The title bar is a bar** (HS-99-02): head on the head tone with
   NO border-bottom; verb buttons are full-height `aspect-ratio: 1`,
   flush to the window edge; hover fill is a variable the close
   button overrides to the danger ramp; `focus-visible` shares the
   hover rule; corners square off when maximized; right-click on the
   bar offers Minimize/Maximize/Close.
3. **Scrollbars belong to the OS** (HS-99-04): thin pill thumb
   (`--desk-scrollbar-thumb`, hover variant) on a transparent track,
   product-wide; Firefox via `scrollbar-width`/`scrollbar-color`.
4. **Controls wear the skin** (HS-99-03): selects are
   `appearance: none` with a drawn chevron on the well tone at
   `--desk-control-h`; date/search/file/number inputs and the
   checkbox row wear the same treatment; options inherit surface
   colors.
5. **The dock is alive** (HS-99-05): frosted two-layer material, a
   running underline per open window (grows on hover), compositor
   hover scale, enter/exit motion — all instant under reduced motion.
6. **Motion has a family**: `--ease-quart` (default) / `--ease-expo`
   (large moves) / `--ease-back` (small playful) beside the duration
   tokens; chrome transitions name them.
7. **Tint math**: hover and selected states use the existing
   `--wash-*` / `--accent-tint` formulas — never new ad-hoc rgba.

## The interior canon (HS-101)

Chartered by the owner's Phase-100 close verdict ("a lot of the
windows … still feel like a bunch of HTML slapped inside a nicer
looking container") and the standing order ("just not be shy — really
push this into OS territory"). Articles VI (honest), VII (the
interface serves), VIII (native-grade craft). Status: **proposed —
nothing below ships before the HS-101-02 gate.** The HS-98 surface
idiom and HS-99 chrome ladder stay floors; this canon governs what
composes ON them.

### The interior type scale

Window bodies are nearly monosize today (13/12/11px). Real
applications have display numbers, primary lines, secondary metadata,
captions. The ratified scale, five steps, all component tokens:

| Step | Token(s) | Use |
|---|---|---|
| display | `--desk-type-display-size/-weight/-lh` (26px/650/1.15, `--font-display`) | the ONE big fact a face leads with: the day's count, the destination's model, the spoken utterance |
| primary | `--desk-type-primary-size/-weight/-lh` (15px/600/1.4) | what the material IS: the journal entry's text, the block's name, a destination's name |
| body | `--desk-surface-body-size` (13px) | continuous copy and dense-row titles (HS-98, unchanged) |
| secondary | `--desk-surface-detail-size` (12px) | metadata: times, sources, counts |
| caption | `--desk-surface-label-size` (11px) | section labels, eyebrows, keycaps |

Rules: a window face uses at least THREE steps; display appears at
most once per face (it is the headline, not a heading style); numbers
at display scale ride `--font-display`. A face whose computed text
sizes collapse to one step is a defect the geometry walk catches.

### The composition rules

1. **Data is the material, not data in fields.** A presented value
   edits in place — click (or Enter) on the presented text turns THAT
   text editable in situ; Escape reverts, blur/Enter commits. A
   label-over-input stack is legal only inside a configuring face
   (the gear door, Settings). Everywhere else it is a defect.
2. **Purpose-built compositions.** A surface composes the shape its
   material actually has: the Journal reads like a journal (a dated
   stream), Blocks like a library (the injection text is the face),
   Runs on like a switchboard (destinations are bays with lamps), a
   transcript like a script. `SurfaceRows` is legal only for
   genuinely homogeneous row material (settings groups, pick lists,
   receipts); reaching for it first is the tell that a surface was
   assembled, not designed.
3. **Verbs live on the material.** Hover/selection reveals a verb
   where the data is (row verbs, HS-98 rule 5, unchanged); the
   surface-top verb bar shrinks to the rare global verb (at most one
   per face). Coarse pointers and reduced motion keep verbs visible.
4. **Direct manipulation reaches through the glass.** The desk's
   physics extend INTO windows and back OUT: drag a desk object into
   a window to hand it over (ground an ask, give a KB to an agent);
   drag a result chip out of a window onto the desk to keep it; drop
   a transcript or audio file anywhere on the desk and a Meeting
   imports. Drop targets light BEFORE the drop (the HS-95 drop-ready
   grammar); a refused drop names why.
5. **Motion is meaning.** State changes animate what changed — the
   correction-learned moment, an approve leaving the queue, a wing
   switch — riding the `--duration-*`/`--ease-*` families,
   compositor-only, instant under reduced motion. Nothing else moves.

### The kit that carries it (designed here, wired at the build)

- `SurfaceStream` — the dated stream: day headers (caption step) over
  entries whose text is primary-step material; per-entry verbs on
  hover; the day's count at display step in the stream head.
- `SurfaceLibrary` — the library: content-forward tiles whose FACE is
  the payload (a block's injection text, an artifact's body), name at
  primary, provenance at secondary; a tile opens in place.
- `SurfaceSwitchboard` — the switchboard: one bay per destination —
  lamp (live/offline, never color-only), name at primary, model/route
  at secondary, boundary badge at the point of decision; the active
  route is visibly THE route.
- `EditInPlace` — the in-place edit affordance behind rule 1: renders
  presented text; focus/click swaps to an editor of the same
  geometry; commit/revert grammar as above; disabled state names why.
- `SystemShade` — one system surface behind the bell (see below).
- The glass-drop contract — `dragKind` (desk-object / chip / file) ×
  drop target (window face, desk, dock chip) with the drop-ready
  lighting and named refusals; one implementation, every window.

### OS territory (AGENT_BRIEF §6, ratified for the gate)

1. **The system shade.** The attention bell opens a real shade — one
   surface for what happened while you were away: the approve queue,
   finished intelligence runs, learned corrections, recovered
   captures. Honest counts (zero says zero), verbs inline, dismiss is
   real. Re-shapes today's AttentionDrawer; same projections feed.
2. **The global keyboard grammar.** ⌘1–⌘4 open/switch the four
   applications; ⌘W closes and ⌘M minimizes the front window; ⌘/
   draws the shortcut sheet (drawn, not a doc link). ⌘K, Ctrl+`,
   Escape, exposé stay as shipped.
3. **Right-click is universal.** Every desk object, row of material,
   window head, dock chip, and the desk itself answer with the ONE
   menu vocabulary (`DeskMenuList`). If a thing can be acted on, its
   context menu says how.
4. **Drag-and-drop is a system verb.** Composition rule 4, system-
   wide: file drop imports, desk objects hand through the glass, chips
   pull out onto the desk.
5. **System moments.** Arrival boots fast, quiet, composed — never a
   spinner pile. Recording state lives in the bar as a system
   indicator. State that changes while a window is closed surfaces in
   the shade, not in silence.
6. **Files-grade browsing.** List mode grows into the desk's Finder:
   sortable columns, type filters, keyboard range-selection, the same
   context menus. Spatial for arranging, Files for finding.

### The mockup roster (HS-101-01)

Census-derived; each ships at 1440 AND 393, real content, looked at:

- `journal` — Speak's Journal as a dated stream (worst innard 1)
- `blocks` — Blocks as a library (worst innard 2)
- `runs-on` — Runs on as a switchboard (worst innard 3)
- `shade` — the system shade, open over the desk
- `drag` — one drag-through-the-glass moment, mid-flight

## Adding a surface (styling rules)

See `web/README.md` for the full add-a-surface path. Styling rules:
component tokens only (the gate will catch you); the state grammars above
are inherited — never hand-roll a focus or pressed treatment; new
recurring values become tokens with doc strings, not allow-list entries.

## Decisions

- **Dark-only stays** (HS-30-03); the semantic layer is the future light
  theme's attach point.
- **The skills' shadcn/Tailwind stack is not adopted** — the Signal
  grammar is standing canon (Article X records the deviation); the
  skills' methods (tokens, validator, matrices, a11y patterns) are.
- **The Radix question** is HS-96-05's recorded decision.
