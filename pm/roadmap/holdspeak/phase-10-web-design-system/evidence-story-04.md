# HS-10-04 evidence — Unified TopNav and route identity

## Files shipped

- `web/src/components/TopNav.astro` — sticky banner with brand mark
  (placeholder ● glyph + "HoldSpeak" wordmark; HS-10-05 replaces the
  glyph with the real SVG mark), four primary route links (Runtime,
  Activity, History, Dictation), an `aria-label="Primary"` nav, a
  skip-to-content link, and a right-aligned tail with a `status`
  slot (defaults to a `local-only` Pill) plus an `overflow` slot.
- `web/src/layouts/AppLayout.astro` — composes `TopNav` (forwarding
  `current` and conditional `status` / `overflow` slots), renders an
  optional secondary toolbar region, and a focus-rooted
  `<main id="main" tabindex="-1">` target for the skip link.
- `web/src/pages/design/check.astro` — passes `current="runtime"` to
  exercise the selected state in evidence.

## How `current` works

- `current` is a typed `"runtime" | "activity" | "history" | "dictation"`
  prop on AppLayout, forwarded to TopNav.
- The matching link receives `class="topnav-link is-current"` and
  `aria-current="page"`. The visual treatment is `--accent-soft`
  background + an inset 2px bottom border in `--accent` —
  unmistakable in a 1-second glance, no color-only signal.
- All other links render as `topnav-link` (no aria-current attribute).
- Pages that do not pass `current` (the components gallery,
  development utilities) render the nav with no link selected; this
  is the correct behavior for off-route surfaces.

## Acceptance: viewport sweep

Captured via `web/scripts/capture-gallery.py` at 1440, 768, and 360
wide. Screenshots in
`pm/roadmap/holdspeak/phase-10-web-design-system/screenshots/`:

- `story-04-topnav-1440.png` — desktop. Brand left, four links inline,
  local-only Pill right. Sticky against the canvas.
- `story-04-topnav-768.png` — tablet. Same layout; the gap collapses
  slightly via the 640px media query (no wrap yet at 768).
- `story-04-topnav-360.png` — narrow. Brand and local-only Pill share
  row 1; the four route links wrap to row 2 (because
  `flex-basis: 100%` on `.topnav-routes` and `order: 3` push them to
  their own line). **No horizontal scroll** at 360px.
- `story-04-topnav-current-runtime.png` — desktop view of the
  design-check page, demonstrating the `current="runtime"` selected
  state (Runtime link has `--accent-soft` fill + inset accent border;
  others are quiet).

## Skip-to-content (keyboard only)

- The first `<a href="#main" class="topnav-skip">Skip to content</a>`
  is positioned `position: absolute` and translated off-screen by
  default (`translateY(-200%)`).
- On `:focus-visible` it slides back into view (`translateY(0)`) with
  the standard `--focus-outline` ring.
- The target `<main id="main" tabindex="-1">` is focusable
  programmatically when the link is activated. `tabindex="-1"` keeps
  it out of the regular tab order while still allowing the URL hash
  to focus it; `outline: none` avoids a stuck focus ring on the main
  region itself.

Manual keyboard walk:

1. Press Tab → skip link slides into view (top-left), focus ring
   visible.
2. Press Enter → URL becomes `…/design/check/#main`, focus jumps to
   `<main>`, and the next Tab moves into the page content (h1, etc.).
3. Press Tab again from the start → without activating skip, focus
   moves to brand → Runtime → Activity → History → Dictation →
   local-only Pill is non-interactive (default), so focus moves into
   page content.

## Acceptance: integration tests

`tests/integration/test_web_built_mount.py` adds two new cases:

```
$ uv run pytest -q tests/integration/test_web_built_mount.py
.....                                                                    [100%]
5 passed in 0.41s
```

- `test_topnav_renders_with_aria_current` — fetches the design-check
  page (which passes `current="runtime"`), asserts:
  - `Skip to content` link is present;
  - exactly one element carries `aria-current="page"`;
  - all four primary route hrefs (`/`, `/activity`, `/history`,
    `/dictation`) are present in the nav.
- `test_topnav_renders_without_current_on_gallery` — fetches the
  components gallery (no `current` prop), asserts:
  - `Skip to content` is still present;
  - **no** `aria-current="page"` appears anywhere;
  - the `local-only` fallback pill renders (proves the conditional
    slot-forwarding pattern works).

## Acceptance: aria-current verification (via grep)

```
$ grep -oE 'aria-current="[^"]*"' holdspeak/static/_built/design/check/index.html | sort -u
aria-current="page"

$ grep -c 'aria-current="page"' holdspeak/static/_built/design/check/index.html
1
```

Exactly one current link. Selected route prop drives the rendered
attribute.

## Full regression sweep

```
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
1183 passed, 13 skipped in 25.69s
```

(Two more than HS-10-03 — the new TopNav tests.) Skips are
pre-existing.

## Acceptance criteria

- [x] TopNav renders identically across the design-check route and
  the components gallery (the only visual difference is the
  `is-current` style on the Runtime link of the design-check page,
  which is the entire point of the `current` prop).
- [x] Selected-route styling is correct for every legitimate
  `current` value — the prop is typed; the rendered HTML matches
  for the one tested value (`runtime`); the other three slugs follow
  the identical render path.
- [x] Skip-to-content works with keyboard only (manual verification
  above; smoke test asserts the link is in the served HTML).
- [x] Narrow-viewport nav has no horizontal scroll at 360px wide
  (screenshot evidence + 360px capture in viewport sweep).
- [x] Screen reader announces the selected nav item as current —
  `aria-current="page"` is rendered on exactly the right link, and
  the link's accessible name is its label text. macOS VoiceOver
  reads "Runtime, current page, link" (verified manually).

## Notes for downstream stories

- **HS-10-05** replaces the placeholder `●` glyph in `.topnav-mark`
  with the actual SVG app mark. The brand link's accessible name
  ("HoldSpeak — Runtime") stays.
- **HS-10-06..09** call `<AppLayout title="..." current="...">` and
  optionally fill the `secondary` slot for per-page action toolbars.
  The legacy `*.html` per-route navigation (where present) is
  deleted in each rebuild story.
- The `topnav-overflow` slot is currently unused but reserved for
  later — e.g., a "more" menu when product surface area grows. Don't
  add one now; the four primary routes are enough.
- The "settings" surface explicitly stays under `/history` in this
  phase per the HS-10-04 scope.
