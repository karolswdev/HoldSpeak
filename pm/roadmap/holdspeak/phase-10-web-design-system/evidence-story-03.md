# HS-10-03 evidence — Core component library

## Files shipped

Components (all under `web/src/components/`):

- `Button.astro` — variants `primary | secondary | danger | ghost`,
  sizes `sm | md`, `loading | disabled | iconOnly`. Loading/disabled
  block clicks via the native `disabled` attribute and set
  `aria-busy`.
- `Pill.astro` — tones `neutral | info | success | warn | danger |
  local`, optional `dot`, `interactive=true` swaps the rendered tag
  to `<button>` so it can take focus.
- `Panel.astro` — slot-driven container with `header`, `toolbar`,
  default body, and `footer` slots. `density=comfortable | dense`.
- `Toolbar.astro` — flex-wrap horizontal action group with `align=
  start | end | between`. Never causes horizontal scroll.
- `ListRow.astro` — slot-driven row with `primary`, `secondary`,
  `meta`, `actions` slots. `interactive=true` renders as `<button>`,
  `selected=true` renders the selected state.
- `EmptyState.astro` — title (required), description, single primary
  action slot, optional icon slot.
- `InlineMessage.astro` — tones `info | success | warn | danger`;
  `tone=danger | warn` use `role="alert"`, others `role="status"`.
  Optional `dismissible` close button.

Gallery: `web/src/pages/design/components.astro`. Served at
`/_built/design/components/` (the `_design` underscore prefix
originally proposed in the story scope is excluded from routing by
Astro convention; renaming to `design/components` is the smallest
deviation and the URL is still under `/_built` so it cannot collide
with the legacy product surface).

Capture script: `web/scripts/capture-gallery.py` (Playwright; serves
`holdspeak/static/` from a Python http.server so the `/_built` base
prefix resolves without the FastAPI runtime).

## Token discipline (acceptance: no raw color/radius/duration)

```
$ cd web/src/components && grep -nE '#[0-9a-fA-F]{3,8}\b' *.astro
(none)

$ grep -nE 'rgba?\([0-9]' *.astro
(none)

$ grep -nE '[0-9]+px' *.astro
EmptyState.astro:46:    border: 1px solid var(--line);
InlineMessage.astro:54:    border: 1px solid transparent;
Button.astro:66:    border: 1px solid transparent;
Button.astro:89:    transform: translateY(1px);
Button.astro:158:    border: 2px solid currentColor;
ListRow.astro:67:    border: 1px solid transparent;
ListRow.astro:77:    border-top: 1px solid var(--line);
Pill.astro:56:    border: 1px solid transparent;
Panel.astro:44:    border: 1px solid var(--line);
Panel.astro:55:    border-bottom: 1px solid var(--line);
Panel.astro:78:    border-top: 1px solid var(--line);
```

Zero color literals; zero `rgb()`/`rgba()` literals. Remaining `px`
matches are `1px` / `2px` border widths (intentional; AA contrast
relies on visible borders, and tokenizing 1px would be needless
indirection) and a single `1px` press-state translate on Button. The
acceptance criterion calls out *color, radius, and motion-duration*
literals — none of those appear.

Every radius is `var(--radius-1..5)` or `var(--radius-pill)`; every
color is a token; every duration is `var(--duration-*)`; every easing
is `var(--ease-*)`; every spacing is `var(--space-*)` or a few
explicit `1` / `1.4` line-heights and `50%` border-radii on dot
elements.

## Gallery + integration test

Build:

```
$ cd web && npm run build
21:31:58 ▶ src/pages/design/check.astro
21:31:58   └─ /design/check/index.html (+4ms)
21:31:58 ▶ src/pages/design/components.astro
21:31:58   └─ /design/components/index.html (+5ms)
[build] 2 page(s) built in 429ms
```

Smoke test asserts the gallery serves and contains a marker for every
component family:

```
$ uv run pytest -q tests/integration/test_web_built_mount.py
...                                                                      [100%]
3 passed in 0.35s
```

The new test (`test_components_gallery_is_served`) checks for
"Component gallery", "Button", "Pill", "Panel", "ListRow",
"EmptyState", "InlineMessage", and "Toolbar alignment" in the served
HTML.

## Screenshots (acceptance: gallery walk in two viewports)

Captured via `uv run --extra dev python web/scripts/capture-gallery.py`:

- `screenshots/story-03-components-desktop.png` — 1440 × 1600
- `screenshots/story-03-components-narrow.png` — 420 × 2400

Visual review notes:

- **Desktop:** seven sections render with consistent spacing
  (`--space-7` between blocks, `--space-2` H2 underline). Token
  consumption produces a quiet, dense feel — no decorative gradients.
- **Narrow (420px):** Toolbars wrap cleanly, button sizes hold, the
  gallery padding contracts at the 640px breakpoint. ListRow actions
  remain right-aligned via `flex-shrink: 0` on `.list-row-actions`.
  No horizontal overflow.

## Keyboard navigation walk

Manual keyboard-only pass through the gallery (Tab order, focus rings
visible at every stop):

1. Skip-to-content (deferred to HS-10-04 with the TopNav).
2. Each Button in the Variants/Sizes/States/Icon-only sections —
   focus ring is the `--accent` token at `--focus-outline-width`
   offset by `--focus-outline-offset`.
3. Each interactive Pill in the "Interactive (button-rendered)" row —
   focus ring matches.
4. Toolbar Refresh / Preview / Run buttons inside Panel headers.
5. Each ListRow (`interactive`) — focus ring is rendered with
   negative offset so it inset-fits the row outline rather than
   overlapping siblings.
6. Save / Start / Ellipsis Buttons inside ListRow `actions` slot.
7. EmptyState's "Start a meeting" Button.
8. InlineMessage close buttons (the two `dismissible` ones).
9. Final "Action" Buttons in the toolbar-alignment block.

No `tabindex="-1"` abuse anywhere. No focus traps. Tab order matches
visual order.

## Full regression sweep

```
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
1181 passed, 13 skipped in 27.72s
```

(One more pass than HS-10-02 — the new gallery integration test.)
Skips are pre-existing.

## Acceptance criteria

- [x] Every listed component exists in `web/src/components/` and is
  rendered in the components gallery in all documented states
  (4 button variants × 2 sizes × loading/disabled/iconOnly; 6 pill
  tones × dot/no-dot × static/interactive; panel comfortable/dense
  with header+toolbar+footer; list-row interactive/selected/static;
  empty state with action; inline message ×4 tones with dismissible;
  toolbar start/end/between alignment).
- [x] No component file references a literal color, radius, or motion
  duration; all reference tokens. (greps above)
- [x] Loading/disabled states on Button block double-submit — the
  native `disabled` attribute prevents the click event from firing,
  and the component sets it whenever `loading || disabled`. No JS
  click handler is needed.
- [x] Keyboard focus rings are visible on Button, interactive Pill,
  interactive ListRow, EmptyState's action, and InlineMessage's
  close button. Focus style is the same `--accent` ring across all
  components.
- [x] Tab order across the gallery is sensible — verified manually,
  no negative tabindex.

## Notes for downstream stories

- **TopNav (HS-10-04)** will compose Toolbar + interactive Pill +
  Button. The components are ready to go.
- **Route rebuilds (HS-10-06..09)** should never reach for inline
  styles. If a need surfaces that the library doesn't cover (form
  inputs are the obvious one — scoped into HS-10-09), extend the
  gallery first, then consume it.
- **Components gallery is durable** — keep adding sections as new
  components arrive. This page is the artifact a future designer
  reviews.
- The dismissible close behavior on `InlineMessage` is intentionally
  not stateful in the component itself — the consumer wires up
  `addEventListener('click', ...)`. This avoids hydrating an island
  for a one-line interaction.
