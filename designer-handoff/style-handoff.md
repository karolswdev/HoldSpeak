# Style Handoff

## Current Visual Language

Phase 12 replatformed the values layer onto a **Workbench-evoking
voice** — symbolic of Amiga Workbench, not a literal pixel
reproduction. The component layer from phase 10 is unchanged;
only token values, the chrome font, and a small number of
component CSS rules were touched.

### The four anchors

```
--wb-blue:    #0055AA   the desktop layer (body background)
--wb-white:   #FFFFFF   panel surfaces
--wb-black:   #000000   1 px hairlines, body text on white
--wb-orange:  #FF8800   the primary accent
```

These read as Workbench at a glance. They are the *symbolic*
palette, not the working palette — the working palette extends
them.

### Supporting palette

The 4-colour Workbench 1.3 mode is the inspiration, not a
hardware ceiling. Modern web frontends need disabled-vs-primary
contrast, distinct status hues, hover states. So:

- **Blue family** — `--wb-blue-deep / -mid / -soft / -tint` for
  hover, title-strip variations, the Workbench inverse-bar
  selected-row idiom.
- **Orange family** — `--wb-orange-deep / -mid / -soft` for
  primary-button hover and orange-tinted highlights.
- **Grey ramp** — `--wb-gray-1..7` for muted text, disabled
  states, sunken fields, footer strips, near-white alternate
  rows. Dense data needs a real neutral ramp.
- **Status hues, fully distinct** — `--wb-green` (success),
  `--wb-amber` (warn — not orange, so it doesn't compete with
  the primary accent), `--wb-red` (danger), `--wb-purple`
  (info / neutral advisory).

Semantic tokens compose these as groups: `--disabled-bg/fg/
border`, `--selected-bg/fg/soft`, `--field-bg/border/focus-
border`. Component CSS reaches for the semantic groups, not raw
hex.

### Typography

```
--font-ui:       Sora (body chrome, list rows, controls, copy)
--font-display:  VT323 (TopNav, page h1, panel titles)
--font-mono:     JetBrains Mono (code, dense data values)
```

VT323 is the canonical *Workbench moment* font. It only fires
in three places: the TopNav, page-level h1, and the blue title
strip on every panel. Putting it everywhere read as fatiguing
and museum-y; restricting it to symbolic moments lets the voice
land without making the frontend hard to read.

### Geometry

- **Radius: 0 across the board.** No rounded corners, including
  on pills.
- **Hard 1 px borders.** No drop shadows on panels (one
  exception: ConfirmDialog uses a hard 4 px black drop-shadow
  to read as "lifted off the desktop" — symbolic, not soft).
- **Panel grammar = window grammar.** Every panel renders a
  blue title strip with the panel name in white VT323, then a
  white body with hard black border. This is the strongest non-
  stripe Workbench cue we ship.
- **Tabs as Workbench notebook tabs.** Square corners, hard
  border on three sides, the active tab merges into the panel
  below by losing its bottom border. Used on `/history`.
- **Disabled gadgets** carry a diagonal-hatch overlay on the
  disabled-grey ramp — the Workbench "ghosted" idiom done in
  CSS. Label stays readable.

### Motion

The phase-10 motion tokens are unchanged. `--duration-short` is
120 ms, `--duration-medium` 220 ms, `--duration-long` 360 ms;
all collapse to 0 ms under `prefers-reduced-motion: reduce` via
the global rule in `tokens.css`.

The single live-status animation that survived phase 12 is the
`.is-live` dot pulse on `recording`/`stopping`/`analyzing`/
`connecting` pills. Tone changes still flip the colour; only
the dot animates.

## Desired Direction (still)

A private local workbench — calm, precise, fast to scan,
technical without being chaotic, confident around destructive
actions.

Avoid (still):

- Marketing-style hero layouts.
- Decorative gradients.
- Nested cards inside cards.
- One-note palette dominance — the slice-3 status-hue
  expansion exists specifically so the frontend isn't all
  orange.

## Component Library

Inventory unchanged from phase 10; values updated by phase 12.
The full set lives in `web/src/components/` and renders in
`/design/components`:

| Component | Purpose | Voice notes |
|---|---|---|
| `Button` | primary/secondary/danger/ghost × sm/md, with loading/disabled | Flat with hard 1 px border. Disabled = grey + diagonal hatch. Ghost inherits foreground colour. |
| `Pill` | tone-driven status pills, optional dot, optional `interactive` | Each tone is its own hue; hard 1 px border in the deep variant. |
| `Panel` | header / toolbar / body / footer slots | Blue title strip with white VT323 caption, hard black border, no shadow. |
| `Toolbar` | right-aligned action strip in panel headers | Inherits the panel-header white text. |
| `ListRow` | dense row primitive | Hard separator between consecutive rows; hover lights pale-blue tint; selected = blue fill, white text (inverse-bar). |
| `EmptyState` | "nothing here" frame | Title in display font; icon tile pale-grey-7 + hard black border. |
| `InlineMessage` | tone-driven panel notice | Hard 1 px border in the tone's deep variant; soft tint fill. |
| `TopNav` | unified app shell nav | The original Workbench *moment* — entirely VT323 against a white title strip. |
| `AppMark` / `HoldMark` | identity glyphs | `currentColor`, scale-aware. |
| `LocalPill` | "local-only" privacy signal | Workbench blue tone. |
| `CommandPreview` | shell command / dry-run trace | Pale-grey-7 fill, hard border, 4 px tone-coloured left edge. |
| `ConfirmDialog` | destructive-action confirmation | Blue title strip, hard 4 px black drop-shadow, scope note as inset blue inverse-bar. |

## Accessibility And Responsiveness

- Visible focus ring (`--focus-outline-width` solid `--accent`)
  on every interactive element.
- All decorative SVGs declare `aria-hidden="true"`; identity
  marks expose `role="img"` + `aria-label` when consumers pass
  one.
- ConfirmDialog traps focus, defaults to Cancel, restores
  focus to the originating control on close.
- `--danger` (`#CC0000`) on `--wb-white` reads at 5.94:1 — AA
  for both body and large text.
- Mobile (`/activity` mobile shot, 390 × 1200) keeps the dense
  list layout legible.

## Resolved Style Questions

- **Single dark theme, or light + dark tokens?** — Phase 12 is
  a *light theme* (white surfaces) on the Workbench-blue
  desktop, replacing phase 10's dark canvas. A separate dark
  theme is no longer the relevant question; the *Workbench*
  voice is the answer.
- **Unified nav across activity, history, dictation?** — Yes;
  TopNav mounted by AppLayout is the only nav surface.
- **Local-only signal grammar?** — `LocalPill.astro` carries
  the canonical signal; the panel-internal Workbench-blue
  background reads as "this is local" by colour alone.
- **Connector command preview look?** — `CommandPreview`
  renders pale-grey-7 sunken-shell-window with a 4 px tone-
  coloured left edge.
- **Meeting candidate state across surfaces?** — Pill tones
  (`info` for candidate, `success` for saved, `warn` for needs
  review, `neutral` for dismissed) — distinct hues thanks to
  the slice-3 palette expansion.

## Deferred Style Questions

- A second theme (true dark mode) is technically possible —
  tokens.css can grow a `:root[data-theme="dark"]` block — but
  no current ask. Phase 13+ if needed.
- Per-route hero illustrations beyond `HoldMark` — only revisit
  if a route's empty state genuinely needs a different motif.
- Page-level transitions / route animations — explicitly out
  of scope (conflicts with Workbench's discrete feel).

## What was *intentionally* not taken from Workbench

These were tested or considered and explicitly skipped:

- **Diagonal-stripe title bar pattern.** Adds visual noise on
  dense routes (`/activity`, `/history`).
- **Full inset/outset gadget bevels** (light top/left, dark
  bottom/right) on every button. Too retro-faithful, fights
  density.
- **Pixel arrow cursor.** Cute for two seconds, painful to use.
- **Clamped 4-colour rendering.** The 1.3 mode was a hardware
  ceiling, not an aesthetic axiom.

The brief was always *evoke* not *emulate*. The result reads as
"a Workbench fan made this in 2026 for themselves" — which is
exactly the relationship we want.
