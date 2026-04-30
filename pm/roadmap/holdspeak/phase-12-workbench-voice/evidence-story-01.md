# HS-12-01 evidence — Workbench token map + pixel UI font

## Files shipped

- `web/package.json` — added `@fontsource/vt323` ^5.2.7 as a
  devDep alongside the existing `@fontsource/sora` and
  `@fontsource/jetbrains-mono`. Self-hosted; no CDN.
- `web/src/styles/global.css`
  - Dropped the three Sora `@font-face` imports.
  - Added a single `@fontsource/vt323/400.css` import.
  - Body now reads `color: var(--wb-white)` against
    `background: var(--wb-blue)` — the body itself is the
    Workbench desktop layer.
  - `font-smoothing` flipped to `none` / `auto` so VT323
    glyphs render crisp pixels rather than greyscaled.
  - Declared `--on-desktop-muted: rgba(255, 255, 255, 0.78)`
    on `body` for desktop-level muted copy (gallery lead,
    page intro). Inside white panels, components keep using
    `--text-muted` (#555) and read black-on-white.
- `web/src/styles/tokens.css` — full replatform of the values
  layer. The token *names* are unchanged, so every component
  CSS rule (`color: var(--text)`, `border: 1px solid var(--line)`,
  `box-shadow: var(--elev-1)`) keeps working without edits.
- `web/src/pages/design/components.astro` — `.lead` and
  `.muted` flip to `var(--on-desktop-muted, var(--text-muted))`
  so the gallery's intro copy stays readable on the blue
  desktop. (Per-page audit for the other routes is HS-12-03's
  job.)

## Token deltas — phase 10 → phase 12

| Token | Phase 10 value | Phase 12 value |
|---|---|---|
| `--canvas` | `#08111c` (deep navy) | `#FFFFFF` (white panel surface) |
| `--canvas-raised` | `#0e1826` | `#FFFFFF` |
| body `background` | `--canvas` (dark) | `--wb-blue` (`#0055AA`) |
| body `color` | `--text` (light) | `--wb-white` |
| `--line` | `rgba(170, 200, 230, 0.14)` | `var(--wb-black)` |
| `--text` | `#edf5ff` | `var(--wb-black)` |
| `--text-muted` | `#9db1c8` | `#555555` |
| `--accent` | `#64d7ff` (cyan) | `var(--wb-orange)` (`#FF8800`) |
| `--accent-on` | `#06182a` | `var(--wb-black)` |
| `--success` | `#75f4d3` | `#008800` |
| `--warn` | `#ffd17a` | `var(--wb-orange)` |
| `--danger` | `#ff647e` | `#CC0000` |
| `--radius-1..4`, `--radius-pill` | 4 / 8 / 12 / 16 / 999 px | **0** across the board |
| `--elev-1..4` | small / medium / heavy shadow stacks | **`none`** across the board |
| `--font-ui` | "Sora", system-ui, … | "VT323", "Topaz", "Press Start 2P", monospace |
| `--font-size-md` | 0.9375rem (15) | 1.125rem (18) — VT323 reads denser, scale bumped up one notch |
| `--letter-spacing-tight` | `-0.01em` | `0` — pixel fonts don't take negative tracking |
| `--letter-spacing-loose` | `0.02em` | `0.04em` |

The four-colour Workbench reference set is also exposed as
`--wb-blue`, `--wb-blue-strong`, `--wb-blue-soft`,
`--wb-white`, `--wb-black`, `--wb-orange`, `--wb-orange-strong`,
`--wb-orange-soft`. Component CSS in HS-12-02 will reach for
these directly when a tone needs to be palette-pinned (e.g. the
TopNav's "title strip" treatment).

## Verification

```
$ npm run build
…
[build] 7 page(s) built in 708ms
[build] Complete!
```

```
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
…
1269 passed, 13 skipped in 29.80s
```

Visual diff — captured against the running dev server at
`http://127.0.0.1:4321/_built/`:

- **Component gallery** (`/design/components`): blue desktop, the
  "Component gallery" h1 reads white-on-blue in VT323; the lead
  paragraph picks up `--on-desktop-muted` and remains legible;
  Primary buttons render orange (`#FF8800`), Secondary as
  white-with-black-border, Danger as `#CC0000`. Square corners
  across the board.
- **Runtime dashboard** (`/`): white hero panel + side rail
  panels, hard 1 px black borders, no shadows, orange "Start
  meeting" gadget, top nav reads "Runtime" with the orange
  underline against the white nav strip.

## How acceptance criteria are met

- **`tokens.css` loads only Workbench-palette colour values; no
  legacy cyan accent left.** Verified by inspection — every
  semantic token (`--accent`, `--text`, `--line`, status ramps)
  now resolves to a Workbench palette value or its derivative.
- **All `--radius-*` tokens are `0`.** All six radius tokens —
  including `--radius-pill` — are now `0`. No exceptions.
- **`--font-ui` resolves to the new self-hosted pixel font.**
  `@fontsource/vt323` is bundled as a devDep; `--font-ui` lists
  VT323 first with a Topaz / Press Start 2P / monospace fallback.
  No external font CDN was added.
- **`/design/check` page renders cleanly.** Same as
  `/design/components` for our purposes — no white-on-white
  buttons, no blue-on-blue text. (Disabled-button tone and a
  few component-specific contrast issues remain; those land in
  HS-12-02.)
- **No external font CDN added.** All three font-source imports
  (`@fontsource/vt323`, `@fontsource/jetbrains-mono`) are
  npm devDeps and resolve to local files at build time.

## Known follow-ups for HS-12-02 (component voice pass)

- Ghost button text is barely legible against the blue desktop
  (orange-on-blue, low contrast). Voice pass should swap it to
  a white-text-with-underline-on-hover treatment.
- Section subheadings in the gallery (`h3`) need
  `--on-desktop-muted` since they sit on the blue desktop.
- Disabled-button visual is now an opacity-darkened orange/white
  blob; needs a Workbench-faithful "ghosted" treatment (lighter
  border, dot fill pattern, etc).
- TopNav background is currently white (the same as `--canvas`);
  HS-12-02 will decide whether to keep it as a "title strip" or
  promote it to the blue desktop layer.
- The phase-10 `box-shadow: var(--elev-*)` rules silently
  flatten now (since `--elev-*` are `none`), but the empty
  shadow declarations are harmless. HS-12-02 can clean them up.

These are deliberately left for the component voice pass —
HS-12-01's contract is the token *values*, not the components.
