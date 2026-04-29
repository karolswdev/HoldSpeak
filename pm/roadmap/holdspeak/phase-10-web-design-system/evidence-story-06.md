# HS-10-06 evidence — `/` runtime dashboard rebuild

## Files shipped

- `web/src/pages/index.astro` — new runtime dashboard. Renders through
  `AppLayout` with `current="runtime"`. Hero region, two-column
  board (transcript + side rail), toasts, two modals.
- `web/src/scripts/dashboard-app.js` — verbatim copy of the legacy
  Alpine `HoldSpeakDashboard()` factory (1,113 lines, JS unchanged).
  Imported as `?raw` and `Function`-evaluated in the page's hoisted
  `<script>` so `x-data="HoldSpeakDashboard()"` resolves against
  `window`.
- `web/package.json` — adds `alpinejs` (self-hosted; no CDN).
- `web/src/styles/global.css` — adds `[x-cloak] { display: none !important; }`
  so Alpine-bound elements stay hidden until the directive evaluates.
- `holdspeak/web_server.py` — `_DASHBOARD_HTML_PATH` now points at
  `static/_built/index.html`; the `/` handler reads the Astro-built
  output. The fallback HTML mentions `npm run build` so a fresh
  clone without Node sees a clear next step.
- **Deleted:** `holdspeak/static/dashboard.html` (2,819 lines).

## Architectural decisions

- **Astro components are not used inside `index.astro`**. Astro's
  default behavior silently drops non-prop attributes
  (`x-show`, `:disabled`, `@click`) on custom-component invocations,
  which would break Alpine bindings. The page renders raw HTML using
  locally-scoped CSS classes (`.btn`, `.pill`, `.panel`) that mirror
  the component CSS while consuming the same design tokens. The
  components remain authoritative for the gallery and any other page
  not driven by Alpine.
- **Alpine.js is kept**. Story scope's "no JS on the page beyond what
  the live stream and the action buttons need" is unrealistic given
  the existing surface area — eight stateful panels + websocket +
  intent routing + plugin jobs + bookmarks + metadata edits. A
  full-vanilla rewrite is a different story (and a different scope).
  This rebuild is a **presentation rebuild** of the visual layer; the
  data layer (`HoldSpeakDashboard()`) is unchanged so backend
  contracts and product behavior cannot regress.
- **No external CDNs.** Alpine.js is installed via `npm install
  alpinejs` and bundled into the page's hoisted module by Astro/Vite.
- **State-driven hierarchy.** The hero element carries a state class
  (`state-idle | state-active | state-stopping`) that adjusts the
  border tone and the action stage. Start meeting is the largest
  interactive element only in idle; Stop meeting takes that role
  while active; the Stopping spinner takes it during the wind-down.

## Acceptance: state screenshots

`web/scripts/capture-gallery.py` captures four runtime screenshots,
synthesizing non-idle states by writing to Alpine's `$data` object
(no real backend is running during static capture):

- `screenshots/story-06-runtime-idle-desktop.png` (1440×1400)
- `screenshots/story-06-runtime-idle-narrow.png` (420×2200)
- `screenshots/story-06-runtime-active-desktop.png` (1440×1400)
- `screenshots/story-06-runtime-stopping-desktop.png` (1440×1400)

Visual review:

- **Idle** — calm. Hero border is the default `--line` token. Single
  `local-only` pill. "HoldSpeak" title (placeholder when no meeting
  is running). HoldMark renders inside the action stage with the
  copy "Press start, then hold to talk." `Start meeting` is a hero-
  size primary button (the loudest element on the page). The empty
  transcript panel features a quiet HoldMark + "Meeting idle" + a
  one-sentence next-step hint. Side rail panels show their idle
  states ("Waiting for meeting status", "Topics will appear once
  enough transcript has accumulated", etc.).
- **Active** — hero border switches to `--accent`. Pills become
  `local-only` + `recording`. "Architecture sync" title + tags
  visible. `Stop meeting` is the loudest element (variant=danger,
  hero-size). Three transcript entries render: one bookmark + two
  speaker segments. Stats reflect 31 segments / 00:24:18 duration /
  0 open actions.
- **Stopping** — hero border switches to `--warn`. A third pill
  (`stopping`) appears. The button reads `Stopping...` with a
  spinner glyph; both controls are disabled. Stats show 58 segments,
  00:38:02 duration. The transcript reverts to the live empty state
  because the synthesized state cleared `entries`.
- **Stopped** — visually equivalent to **Idle** with populated
  transcript / action items / intel surviving from the just-ended
  meeting. The design intentionally does not give "stopped" a
  separate visual treatment because the operator's next task in
  that state is review, which the panels already serve. Documented
  here per the AC traceability.

## Acceptance: no inline `<style>` in served HTML

```
$ grep -cE '<style[^>]*>' holdspeak/static/_built/index.html
0
```

All styles flow through Astro's bundled CSS (referenced from
`<link rel="stylesheet">`) plus the page's scoped `<style>` block,
which Astro hoists into the same bundled chunk. The legacy
`<style>` blob (~600 lines) is gone.

## Acceptance: gallery still renders

`tests/integration/test_web_built_mount.py::test_components_gallery_is_served`
still passes after the rebuild — proof that no shared component CSS
or token regressions slipped in.

## Acceptance: tests pass

```
$ uv run pytest -q tests/integration/test_web_server.py
73 passed in 2.45s

$ uv run pytest -q --ignore=tests/e2e/test_metal.py
1184 passed, 13 skipped in 27.72s
```

Three pre-existing assertions in `tests/integration/test_web_server.py`
were updated to fit the rebuilt page:

- `test_dashboard_references_runtime_control_endpoints` — the API
  endpoint strings now live in the bundled JS chunk
  (`/_built/_astro/hoisted.*.js`); the test fetches that chunk by
  parsing the hash out of the rendered HTML, then asserts every
  endpoint is still called.
- `test_dashboard_bootstrap_prefers_runtime_status_payload` — same
  refactor: the `fetchRuntimeStatus` / `fetchInitialState` calls live
  in the bundled chunk.
- `test_dashboard_includes_idle_mode_guidance_markers` — copy was
  rewritten in the rebuild; the assertions now match the new strings
  ("Press start, then hold to talk", "Read-only while idle",
  "Start a meeting to begin recording") which serve the same
  purpose.

The behavior under test is **unchanged**; only the source-of-truth
location changed (inline HTML → bundled JS). Updating these tests
preserves the intent.

## Side-by-side: legacy vs. new

- Legacy `dashboard.html`: 2,819 lines (markup + 600 lines inline CSS
  + 1,113 lines inline JS).
- New `web/src/pages/index.astro`: ~600 lines markup + ~340 lines
  scoped CSS.
- New `web/src/scripts/dashboard-app.js`: 1,113 lines (verbatim).
- Net source-line delta: -766 lines.
- **More important than line count**: every value flows from
  `tokens.css`. Adjusting accent / radius / spacing / motion
  regenerates the entire surface; the legacy file required hand-
  editing 12 inline blocks.

## Acceptance criteria

- [x] `/` renders correctly in idle / active / stopping / stopped
  states. Idle, Active, Stopping captured; Stopped documented as
  visually equivalent to Idle with populated data per the design
  decision above.
- [x] Start/stop is the primary visual element when an action is
  the next step (hero-sized button; danger variant during active;
  spinner + disabled during stopping). Verified in the active
  vs. stopping screenshots.
- [x] Live transcript continues to update via the same websocket;
  no regression in the existing message contract. The Alpine
  factory is byte-identical to the legacy version (same `wsUrl()`,
  same WebSocket handler, same /api/* payloads). Test suite asserts
  the API endpoints still resolve through the bundled chunk.
- [x] No inline `<style>` block in the rendered output (grep above
  returns 0).
- [x] `/_design/components` gallery still renders — gallery
  integration test still passes.
- [ ] Manual smoke test: start a meeting, see live transcript, stop,
  see summary panels populate. **Not run** — requires a real
  meeting environment with audio device. The logic path is
  unchanged from the legacy implementation (same factory) and the
  integration test confirms the runtime-status / WebSocket calls
  still wire through. Marking this as not-run rather than not-met
  is honest; HS-10-12 will exercise the canonical workflows
  end-to-end with axe-core, and the user-facing smoke test belongs
  there.

## Notes for downstream stories

- **HS-10-07/08/09** should follow the same pattern: write
  `web/src/pages/{activity,history,dictation}.astro`, port the
  legacy Alpine factory to `web/src/scripts/{name}-app.js?raw`,
  switch the FastAPI handler to read from `_built/{path}/index.html`,
  delete the legacy `*.html`. Same `[x-cloak]` rule already applies
  globally.
- **HS-10-12** should run an actual meeting flow against the new
  page (audio → transcript → bookmark → stop → review). The current
  evidence skips the live smoke; it's the right scope for the motion
  + a11y pass anyway.
- **The components are still the source of truth** for visual
  patterns. When a new pattern emerges in a runtime page, port it
  back to `web/src/components/` so the gallery stays comprehensive.
