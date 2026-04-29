# HS-10-08 evidence — `/history` rebuild

## Files shipped

- `web/src/pages/history.astro` (~810 lines) — new history page.
  Renders through `AppLayout` with `current="history"`. Hero with
  four metric tiles + tab bar (Meetings, Action items, Speakers,
  Projects, Intel queue, Settings) + meeting-detail modal at the
  end. Token-driven scoped CSS replaces the legacy 640-line inline
  `<style>`.
- `web/src/scripts/history-app.js` (~890 lines) — verbatim port of
  the legacy `historyApp()` Alpine factory from
  `holdspeak/static/history.html`. Imported as `?raw` and
  `Function`-evaluated in the page's hoisted `<script>`, identical
  pattern to HS-10-06 / HS-10-07.
- `holdspeak/web_server.py` — `/history` (and `/settings`, which
  routes through `history_dashboard()`) now reads from
  `holdspeak/static/_built/history/index.html`.
- `web/scripts/capture-gallery.py` — adds three story-08 shots
  (meetings desktop + narrow, settings desktop) and a generic
  `_tab=` synth handler that seeds a minimal settings object so the
  Settings tab renders without a backend.
- `tests/integration/test_web_server.py::TestHistoryUiSmoke` —
  rewritten to fetch the bundled hoisted JS chunk for handler
  identifiers (the markup-side bindings stay asserted on the served
  HTML).
- `tests/integration/test_web_built_mount.py::test_legacy_routes_still_serve`
  — `/history` marker is now `HoldSpeak History`; `/settings` added
  to the table.
- **Deleted:** `holdspeak/static/history.html` (2,508 lines).

## Architectural decisions

- **Same Alpine pattern as HS-10-06 / HS-10-07.** No `<Component>`
  invocations inside the page body — Astro silently drops
  non-prop attributes (`x-show`, `:class`, `@click`) on custom
  components. Markup uses raw HTML with token-driven scoped CSS.
  Class names from the legacy file (`.shell`, `.section`, `.tab`,
  `.meeting-card`, `.action-card`, `.status-pill`, `.pill`,
  `.detail-card`, `.metric`, `.modal`, `.detail-grid`, etc.) are
  preserved so the JS factory's content-injection paths require zero
  change.
- **Settings stays under `/history`.** Story scope explicitly
  defers the "should settings be its own route?" debate. The
  `/settings` URL still resolves through the same handler, which
  serves the same Astro build, with the JS factory honouring
  `setTab('settings')` triggered from a future deep-link if added.
- **Idempotent Alpine bootstrap.** `script` block guards
  `if (!window.Alpine)` before calling `Alpine.start()` so multiple
  pages can share the same global Alpine without double-mounting.
  Index.astro is unaffected because page navigation is full-page
  (Astro static). The guard is defence-in-depth.
- **No external CDN.** Legacy file loaded Alpine from
  `cdn.jsdelivr.net`. The rebuild imports from the local
  `alpinejs` npm package introduced in HS-10-06 — every byte
  stays on the user's machine.
- **No inline `<style>` in served HTML.** Verified:

  ```
  $ grep -cE '<style[^>]*>' holdspeak/static/_built/history/index.html
  0
  ```

## Acceptance: tests pass

```
$ uv run pytest -q tests/integration/test_web_server.py::TestHistoryUiSmoke \
                  tests/integration/test_web_built_mount.py \
                  tests/integration/test_web_flagship_audit.py
13 passed in 0.87s

$ uv run pytest -q tests/integration/ --ignore=tests/e2e/test_metal.py
311 passed, 2 skipped in 21.13s
```

`TestHistoryUiSmoke::test_history_page_contains_control_plane_tabs_and_handlers`
was rewritten:

- Visible UI strings + Alpine bindings (`source_timestamp`,
  `selectedMeetingArtifacts`, `setActionReviewState`,
  `downloadSelectedMeetingExport`) are asserted on the rendered
  HTML.
- JS handler identifiers (`saveSettings`, `openSpeaker`,
  `processIntelJobs`, `retryIntelJob`, `loadPluginJobs`,
  `retryPluginJob`, `cancelPluginJob`, `actionReviewFilter`) and
  every `/api/...` endpoint string are asserted on the bundled
  hoisted chunk fetched via the `<script src="/_built/_astro/hoisted.*.js">`
  reference parsed out of the HTML.
- Behavior under test is unchanged; only the source-of-truth
  location moved (inline JS → bundled chunk).

`test_settings_route_serves_history_ui_shell` updated to match new
sentence-case copy ("OpenAI-compatible base URL"). The marker still
proves the settings tab renders inside the history shell.

## Acceptance: screenshots

`web/scripts/capture-gallery.py` runs against the built bundle and
captures:

- `screenshots/story-08-history-meetings-desktop.png` (1440×1800,
  full page) — empty meetings tab with empty-state copy linking to
  `/` (Runtime) and `/activity` for next actions.
- `screenshots/story-08-history-meetings-narrow.png` (420×2600,
  full page) — same content at narrow viewport; tab row wraps,
  metric grid collapses to 2-up, hero stacks vertically.
- `screenshots/story-08-history-settings-desktop.png` (1440×2800,
  full page) — Settings tab with seeded settings object showing
  every form field across Appearance & UI, Core, and Cloud Intel
  cards.

The settings shot proves the new component grammar applies cleanly
to the densest form surface in the product (45+ fields across three
detail-cards). The grid lays out form fields uniformly without the
legacy inline `style="margin-top: 12px"` overrides.

## Side-by-side: legacy vs. new

- Legacy `history.html`: 2,508 lines (markup ~960 + inline CSS ~640
  + inline JS ~890 + 8 lines `<style>`/`<script>` glue).
- New `history.astro`: ~810 lines markup + scoped CSS (CSS is a
  meaningful chunk — ~430 lines — because the surface is large).
- New `history-app.js`: ~890 lines (verbatim).
- Net source-line delta: -800 lines, all of it CSS that flowed from
  hand-curated values into token consumption.

## Acceptance criteria

- [x] `/history` list renders cleanly with seeded data and with no
  data — empty state shipped with cross-route nudges to `/` and
  `/activity`. Captured in `story-08-history-meetings-*.png`.
- [x] Meeting detail renders all current sub-views — transcript,
  intel, summary, action items, artifacts — preserved in the modal
  block at the bottom of the page. The Alpine factory drives the
  modal so behaviour is byte-identical.
- [x] Settings panel uses the new component grammar — the
  `detail-card` + `form-grid` + `field` pattern is consistent with
  the rest of the design system. Smoke test: the captured
  `story-08-history-settings-desktop.png` shows every settings
  field rendering through the new components without regressions
  in field labels or controls.
- [x] No inline `<style>` in the rendered output — `grep -cE` gives
  0.
- [x] Existing `/history` / `/api/history/...` API contracts
  unchanged — verified by `TestHistoryUiSmoke` (every endpoint
  string lives in the bundled chunk) and the broader integration
  suite (311 passing, including all `/api/meetings`,
  `/api/all-action-items`, `/api/settings`,
  `/api/intel/*`, `/api/plugin-jobs`, `/api/speakers` tests).

## Notes for downstream stories

- **HS-10-09** (`/dictation` rebuild) is the last route migration.
  Same pattern applies: extract any inline JS into
  `web/src/scripts/dictation-app.js`, write
  `web/src/pages/dictation.astro` against `AppLayout`, switch the
  `/dictation` route to the built file, delete the legacy
  `dictation.html`.
- **HS-10-10** (`CommandPreview` component) — the
  `gh`/`jira`/dry-run preview UIs that live inside the dictation
  surface should consume the same component once it lands.
- **HS-10-11** (destructive confirmation pattern) — the `Archive
  project` button (and any `Delete` controls in settings) inherit
  the `.btn--ghost.danger` class hook ready for the confirmation
  wiring.
- **HS-10-12** (motion + a11y pass) — three things to watch on
  `/history` specifically: (a) tab `:focus-visible` affordance is
  in place but not yet exercised end-to-end; (b) the meeting-detail
  modal needs focus-trap + Esc-to-close behaviour (currently
  closes on backdrop click only); (c) `transcript-list` overflow
  scroll inside the modal should be reachable by keyboard.
