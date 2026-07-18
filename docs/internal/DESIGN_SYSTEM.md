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
