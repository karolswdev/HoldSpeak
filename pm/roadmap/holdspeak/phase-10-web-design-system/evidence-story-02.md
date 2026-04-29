# HS-10-02 evidence — Design token layer

## Files shipped

- `web/src/styles/tokens.css` — single source for color, typography,
  spacing, radius, elevation, motion, focus, and z-index. Imports
  Open Props once at the top so consumers do not.
- `web/src/styles/global.css` — imports `tokens.css` plus self-hosted
  Sora (400/500/600) and JetBrains Mono (400/500), applies a small
  reset, sets default body type/colors and the focus-visible style.
- `web/src/layouts/AppLayout.astro` — single shell that imports
  `global.css`. All future pages render through this.
- `web/src/pages/design/check.astro` — promoted to render through
  `AppLayout`, includes a swatch grid that consumes accent / warm /
  success / warn / danger / canvas-raised tokens, and a motion-box
  for the reduced-motion check.
- `web/package.json` — added `@fontsource/sora` and
  `@fontsource/jetbrains-mono` (devDependencies).

## Inventory: legacy `:root` blocks → new tokens

| Legacy | Files | New token |
|---|---|---|
| `--canvas: #07111d` | dashboard, history, dictation, runtime-setup | `--canvas: #08111c` (slight desaturate) |
| `--canvas-2: #0d1a2a` | dashboard | `--canvas-raised: #0e1826` |
| `--bg: #07111d` | activity (drift) | `--canvas` (unified) |
| `--panel: rgba(9,18,31,0.84)` and variants | dashboard, history, dictation, runtime-setup | `--canvas-raised` / `--canvas-elevated` (solid; transparency was decorative) |
| `--panel: #0d1a2a` | activity (drift) | `--canvas-raised` |
| `--panel-2: #102237` | activity | `--canvas-elevated: #142136` |
| `--panel-strong: rgba(12,23,38,0.96)` | dashboard, history, dictation | `--canvas-elevated` |
| `--panel-soft: rgba(13,27,44,0.76)` | dashboard | `--canvas-overlay: rgba(8,17,28,0.72)` |
| `--line: rgba(158,196,229,0.16)` and variants 0.18 | all 5 (drift) | `--line: rgba(170,200,230,0.14)` |
| `--line-strong: rgba(158,196,229,0.28)` | dashboard, history, dictation | `--line-strong: rgba(170,200,230,0.26)` |
| `--text: #edf5ff` | all 5 | `--text: #edf5ff` (kept) |
| `--muted: #9db1c8` | all 5 | `--text-muted: #9db1c8` (kept; renamed) |
| `--muted-strong: #c3d2e2 / #c8d7e6` | dashboard, history (drift) | `--text` (no separate tier needed) |
| `--accent: #64d7ff` | all 5 | `--accent: #64d7ff` (kept) |
| `--accent-2: #75f4d3` | dashboard, history, dictation, runtime-setup | `--success: #75f4d3` (renamed; was used as a status color) |
| `--ok: #75f4d3` | activity | `--success` (unified) |
| `--warm: #ffb86b` | dashboard, history | `--warm: #ffb86b` (kept) |
| `--warn: #ffb86b` | activity, dictation (drift — used same hex for warn AND warm) | `--warn: #ffd17a` (split: warm is decorative, warn is status) |
| `--danger: #ff647e` | dashboard, history, dictation, activity | `--danger: #ff647e` (kept) |
| `--shadow: 0 24px 60px rgba(0,0,0,0.38 / 0.35)` | dashboard, history (drift) | `--elev-4: 0 24px 60px rgba(0,0,0,0.48)` (with `--elev-1..3` added) |
| `--radius-xl: 30px` | dashboard, history | `--radius-5: 24px` (down-tuned; 30px read as decorative on dense panels) |
| `--radius-lg: 22px` | dashboard, history | `--radius-4: 16px` |
| `--radius-md: 16px` | dashboard, history, dictation | `--radius-4: 16px` (unified) |
| `--radius-sm: 12px` | dashboard | `--radius-3: 12px` |
| `--font-ui: "Sora", ...` | dashboard, history, dictation, runtime-setup | `--font-ui` (kept; activity also adopts Sora) |
| `--font: "Avenir Next", ...` | activity (drift) | `--font-ui` (unified) |
| `--font-mono: "JetBrains Mono", ...` | dashboard, history, dictation, runtime-setup | `--font-mono` (kept) |
| `--mono: "SFMono-Regular", ...` | activity (drift, no JetBrains Mono) | `--font-mono` (unified) |

New token families introduced (no legacy equivalent):

- Spacing: `--space-1..--space-8` (4 px base).
- Status soft fills: `--accent-soft`, `--warm-soft`, `--success-soft`,
  `--warn-soft`, `--danger-soft`, `--local-soft`.
- Local-only signal: `--local`, `--local-soft` (HS-10-05 will consume).
- Motion: `--duration-short/medium/long`, `--ease-standard/emphasized/decelerate`.
- Focus: `--focus-ring`, `--focus-outline-width`, `--focus-outline-offset`.
- Z-index: `--z-base/sticky/overlay/dialog/toast`.

The mapping is exhaustive — every value in the five legacy `:root`
blocks resolves to one of the new tokens.

## Self-hosted fonts (no external CDN)

Built output `holdspeak/static/_built/_astro/` contains 31 font files
(Sora 400/500/600, JetBrains Mono 400/500, latin / latin-ext / cyrillic
/ greek / vietnamese subsets, woff2 + woff fallbacks). Sample:

```
sora-latin-400-normal.CRt88UEn.woff2
sora-latin-500-normal.01eiPEn0.woff2
sora-latin-600-normal.Cdg4DaK0.woff2
jetbrains-mono-latin-400-normal.V6pRDFza.woff2
jetbrains-mono-latin-500-normal.BWZEU5yA.woff2
```

The built CSS (`check.sqlBVcYb.css`) contains zero external HTTP URLs:

```
$ grep -oE 'https?://[^"'\'')]*' check.sqlBVcYb.css | grep -v w3.org
(empty)
```

`@font-face` `src` values point at the local `/_built/_astro/...woff2`
paths. No `fonts.googleapis.com`, `fonts.gstatic.com`, `cdn.*`,
`jsdelivr`, or `unpkg` references anywhere in the build output.

## `prefers-reduced-motion` flattens durations

`tokens.css` and `global.css` both ship a
`@media (prefers-reduced-motion: reduce)` block. The compiled output
preserves it:

```
$ grep -oE '@media[^{]*prefers-reduced-motion[^{]*' check.sqlBVcYb.css
@media (prefers-reduced-motion: reduce)
```

The reduced-motion block:

1. Overrides `--duration-short/medium/long` to `0ms` on `:root`.
2. Adds a global `*, *::before, *::after`
   `transition-duration: 0ms !important; animation-duration: 0ms !important`
   guard so any third-party CSS that does not consume the duration
   tokens is also flattened.

Manual DevTools verification: opening the design-check page and
toggling "Emulate CSS prefers-reduced-motion: reduce" causes the
motion-box hover to apply instantly (no slide animation).

## WCAG AA contrast — all token text/foreground colors

Computed via the WCAG 2.x contrast formula (relative luminance, then
`(L_lighter + 0.05) / (L_darker + 0.05)`). AA threshold for normal
body text is ≥ 4.5; large-text threshold is ≥ 3.0.

| Foreground | Background | Ratio | Result |
|---|---|---|---|
| `--text` `#edf5ff` | `--canvas` `#08111c` | **17.25** | AA pass |
| `--text-muted` `#9db1c8` | `--canvas` | **8.63** | AA pass |
| `--text-faint` `#6b7e95` | `--canvas` | **4.55** | AA pass (tertiary metadata only; sits just above the threshold) |
| `--accent` `#64d7ff` | `--canvas` | **11.48** | AA pass |
| `--warm` `#ffb86b` | `--canvas` | **11.13** | AA pass |
| `--success` `#75f4d3` | `--canvas` | **14.12** | AA pass |
| `--warn` `#ffd17a` | `--canvas` | **13.23** | AA pass |
| `--danger` `#ff647e` | `--canvas` | **6.66** | AA pass |
| `--text` on `--canvas-raised` `#0e1826` | | **16.23** | AA pass |
| `--text-muted` on `--canvas-raised` | | **8.12** | AA pass |
| `--accent` on `--canvas-raised` | | **10.79** | AA pass |

The acceptance criterion required three (body, muted, accent on
canvas) — all eleven sampled combinations clear AA. `--text-faint`
clears AA but is intentionally reserved for tertiary metadata
(timestamps, build markers) where the lower contrast is appropriate.

## Smoke test

`tests/integration/test_web_built_mount.py` updated for the new
H1 ("Design system online"):

```
$ uv run pytest -q tests/integration/test_web_built_mount.py
..                                                                       [100%]
2 passed in 0.29s
```

## Full regression sweep

```
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
1180 passed, 13 skipped in 30.98s
```

Skips are pre-existing (audio fixtures, optional llama-cpp); zero
relate to HS-10-02.

## Acceptance criteria

- [x] `tokens.css` exists, is the single source of color/type/space/
  radius/motion variables, and is consumed by the design-check route
  (the swatch grid + motion-box demonstrate consumption end-to-end).
- [x] Tokens cover every value in the five legacy `:root` blocks; the
  mapping table above proves it.
- [x] Self-hosted fonts load from `holdspeak/static/_built/_astro/`
  post-build; zero external font requests in built CSS.
- [x] `prefers-reduced-motion: reduce` flattens duration tokens to 0ms
  and adds a belt-and-suspenders global override.
- [x] WCAG AA contrast verified for body, muted, and accent on canvas
  (and for 8 additional combinations).

## Notes for downstream stories

- HS-10-03 should consume tokens *only*. Any new value a component
  needs is either an existing token or a new token added to
  `tokens.css` and re-exported by adoption.
- The legacy `holdspeak/static/*.html` files still ship their own
  inline `:root` blocks — those die when each route is rebuilt
  (HS-10-06..09).
- `--text-faint` is the closest-to-threshold token; if HS-10-03
  components need a "very quiet" tertiary text style, prefer
  `--text-muted` and explore alternative emphasis (size, weight)
  before reaching for `--text-faint`.
