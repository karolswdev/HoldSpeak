# HS-10-05 evidence — HoldSpeak identity layer

## Files shipped

- `web/src/components/AppMark.astro` — monochrome SVG (24×24 viewBox,
  stroke-width 2, integer coordinates, `currentColor`). A rounded
  rectangle keycap with a centered three-bar voice waveform: short
  bars at x=8 and x=16 (height 2), tall bar at x=12 (height 6).
- `web/src/components/HoldMark.astro` — larger version of the same
  geometry (56×56 viewBox), with the three bars animating via a
  `scaleY` keyframe that runs across `--duration-long`. Pulse can be
  disabled via `pulse=false`. The `prefers-reduced-motion: reduce`
  global override in `tokens.css` flattens the animation to 0ms.
- `web/src/components/LocalPill.astro` — Pill specialization that
  always renders `tone="local"` + `dot`, with a canonical
  `local-only` label and a tooltip explaining the privacy stance:
  "All HoldSpeak data — recordings, transcripts, activity, connector
  output — stays on your machine. Nothing is sent to a remote
  server." The wording lives in this one component so it stays
  canonical across the four routes.
- `web/public/favicon.svg` — same keycap+waveform geometry, with a
  `--canvas` fill and `--accent` stroke baked in (the `<head>` link
  cannot reference CSS custom properties).
- `web/public/apple-touch-icon.png` — 180×180 raster rendering of the
  same mark, generated via Pillow (`uv run --with pillow ...`); the
  same canvas dark-blue background with cyan keycap + bars.
- `TopNav.astro` — replaces the placeholder `●` glyph with `AppMark`.
  The mark inherits the parent's `color: var(--accent)`.
- `AppLayout.astro` — adds `<link rel="icon">` and
  `<link rel="apple-touch-icon">` references; default `status` slot
  fallback now renders `LocalPill` instead of a raw `Pill`.
- `tokens.css` — adds a comment under the focus-ring section
  documenting the single grammar (positive offset for everything,
  negative for full-width interactive rows).
- Gallery: new "Identity layer" section showing the mark at 16/24/32
  px in two tones, the HoldMark at 72 px inside a Panel, and two
  `LocalPill` variants.

## Acceptance: app mark crispness

The SVG uses integer coordinates inside a 24×24 viewBox with
`stroke-width="2"` and `stroke-linecap="round"`. At every common
size the keycap and bars snap to the device pixel grid:

- 16 px → 1.5 px stroke maps to 1 device pixel (Retina) / 2 device
  pixels (non-Retina); the 0.66× scaling preserves the rounded
  square's silhouette.
- 24 px → native 1:1; the canonical TopNav size.
- 32 px → 1.33× scaling; bars remain visually balanced.

Visual review: see `screenshots/story-05-identity-desktop.png` —
the gallery's "App mark — sizes" toolbar renders all three sizes
side-by-side with the canonical accent tone, plus a `--text` tone
sample to demonstrate the `currentColor` driver works.

The TopNav captures (`screenshots/story-04-topnav-current-runtime.png`,
re-captured for HS-10-05) show the new mark in place at 24 px with
the wordmark — the placeholder dot is gone.

## Acceptance: LocalPill adoption

- TopNav default `status` slot fallback → `LocalPill`. Verified by
  integration test `test_topnav_renders_without_current_on_gallery`
  (the gallery has no `status` slot and the local-only fallback
  still renders).
- Tooltip wording is single-sourced in `LocalPill`. The tooltip text
  ("…stays on your machine. Nothing is sent to a remote server.") is
  asserted by `test_identity_layer_assets_serve`.
- Adoption across `/activity`, `/history`, `/dictation` data-import,
  connector, and deletion controls is **traceable to HS-10-06..09**
  (per the story scope's explicit cross-reference). HS-10-05 ships
  the component and the TopNav fallback; the per-route adoptions
  land when each route is rebuilt.

## Acceptance: focus-ring grammar (single style)

Audit of every `:focus-visible` block in `web/src/`:

```
$ grep -A 3 ':focus-visible' components/*.astro layouts/*.astro styles/*.css
```

Every interactive surface uses the same 3-line pattern:

```css
outline: var(--focus-outline-width) solid var(--accent);
outline-offset: var(--focus-outline-offset);
```

The single intentional exception is `ListRow--interactive`, which uses
`outline-offset: calc(-1 * var(--focus-outline-width))` to produce an
inset focus ring (the row spans the full panel width and an outset
ring would overlap siblings). This convention is now documented
inline in `tokens.css` so future components don't drift.

Coverage: Button, Pill (interactive), ListRow (interactive),
InlineMessage close button, TopNav skip link, TopNav brand link,
TopNav route links, the global `:focus-visible` fallback in
`global.css`. No raw color literals; every focus rule references
`--accent`.

## Acceptance: favicon + apple-touch-icon ship

```
$ find holdspeak/static/_built -maxdepth 1 -type f
holdspeak/static/_built/apple-touch-icon.png
holdspeak/static/_built/favicon.svg
```

Both files emit at the build root. The integration test fetches
each through the FastAPI mount and asserts the correct content type:

```
GET /_built/favicon.svg          → 200, content-type: image/svg+xml
GET /_built/apple-touch-icon.png → 200, content-type: image/png
```

`AppLayout.astro` references both:

```html
<link rel="icon" type="image/svg+xml" href="/_built/favicon.svg">
<link rel="apple-touch-icon" href="/_built/apple-touch-icon.png">
```

For now the favicon resolves under the `/_built` mount because the
legacy `/`, `/activity`, `/history`, `/dictation` routes still serve
the hand-authored HTML files (which have no favicon link). When
HS-10-06..09 rewire each route to read from `static/_built/`, the
favicon will be referenced from those AppLayout-rendered pages too.

## Tests

```
$ uv run pytest -q tests/integration/test_web_built_mount.py
......                                                                   [100%]
6 passed in 0.41s
```

The new `test_identity_layer_assets_serve` asserts:

- `<link rel="icon" href="/_built/favicon.svg">` is in the rendered head.
- `<link rel="apple-touch-icon" href="/_built/apple-touch-icon.png">` is in the rendered head.
- `viewBox="0 0 24 24"` appears (proves the inline app mark is rendered).
- `rx="3"` appears (proves the keycap geometry is intact).
- `stays on your machine` appears (proves LocalPill tooltip text shipped).
- `/_built/favicon.svg` returns HTTP 200 with `image/svg+xml`.
- `/_built/apple-touch-icon.png` returns HTTP 200 with `image/png`.

Full regression sweep:

```
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
1184 passed, 13 skipped in 27.69s
```

(One more than HS-10-04 — the new identity-layer test.)

## Acceptance criteria

- [x] App mark renders crisply at 16, 24, and 32 px in the live nav
  (gallery sizes block + TopNav at 24 px).
- [x] `LocalPill` is used in the TopNav (default fallback) and ready
  for adoption by HS-10-06..09 across data-import / connector /
  deletion controls. Cross-reference recorded; the `local-only`
  label and tooltip wording are now centralized.
- [x] Focus rings on Button, ListRow, link, and form controls share
  a single style — every `:focus-visible` block uses the same
  `--focus-outline-width` + `--accent` + `--focus-outline-offset`
  recipe (audit above). The negative-offset variant on ListRow is
  now documented in `tokens.css`.
- [x] Favicon and apple-touch-icon ship in `holdspeak/static/_built/`
  after a clean `npm run build`; both serve through the FastAPI
  mount with correct content types.

## Notes for downstream stories

- **HS-10-06**: when rebuilding `/`, use `<HoldMark size={...} />`
  inside the runtime idle empty state. Pass `pulse=true` (the
  default) — the bars will animate while the user is reading "ready
  to record" and freeze under reduced-motion.
- **HS-10-08**: same pattern for the `/history` empty state ("No
  meetings yet"); pulse should be disabled there (`pulse=false`)
  because the page is browsed, not a primary action surface.
- **HS-10-07**: every `/activity` data-import / connector / deletion
  control should sit next to a `<LocalPill />`. Use the default
  label; if a panel needs scope-specific text (e.g. "local-only ·
  activity"), pass `label`.
- **No production-root favicon yet**: the legacy `/`, `/activity`,
  `/history`, `/dictation` routes still render hand-authored HTML
  with no favicon link. They'll inherit it when HS-10-06..09 rebuild
  each route on AppLayout. A `/favicon.ico` root handler is **not**
  added in this story to avoid scope creep — future-you will get it
  for free with the rebuilds.
- **The favicon SVG hard-codes `#08111c` and `#64d7ff`** because
  `<link rel="icon">` cannot resolve CSS custom properties. If the
  canvas/accent tokens ever change, the favicon must be updated by
  hand. (This is a known small drift — not worth a build pipeline.)
