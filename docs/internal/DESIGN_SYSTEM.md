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

Window interiors are one visual product with the desk. The Signal
page grammar (`page-grid`, `span-*`, `Panel`, `data-list`/`data-row`,
`signal-eyebrow`, permanent `button-row` walls) is forbidden inside
`pages/cores/` — mechanically, by
`tests/unit/test_native_surfaces_guard.py`, whose per-file allowlist
only shrinks. Cores compose the surface kit
(`web/src/desk/surface/`), which owns the six rules:

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
