# HS-10-07 evidence — `/activity` rebuild

## Files shipped

- `web/src/pages/activity.astro` (~440 lines) — new activity page.
  Renders through `AppLayout` with `current="activity"`. Two-column
  grid: side rail (Controls, Sources, Excluded domains) + main column
  (Project rules, Meeting candidates, Recent activity). Token-driven
  scoped CSS replaces the legacy 600-line inline `<style>` block.
- `web/src/scripts/activity-app.js` (~560 lines) — verbatim port of
  the legacy vanilla-JS module that fetches `/api/activity/*`,
  manages state, and renders rows via `innerHTML`. Imported as
  `?raw` and `Function`-evaluated in the page's hoisted `<script>`,
  same pattern HS-10-06 established for `dashboard-app.js`.
- `holdspeak/web_server.py` — `/activity` handler now reads from
  `holdspeak/static/_built/activity/index.html` instead of the
  hand-written `static/activity.html`.
- `web/scripts/capture-gallery.py` — adds `story-07-activity-desktop`
  (1440×2200) and `story-07-activity-narrow` (420×3000) shots.
- **Deleted:** `holdspeak/static/activity.html` (940 lines).

## Architectural decisions

- **No Astro components inside the page body.** Same reasoning as
  HS-10-06: the JS module synthesizes nested HTML via `innerHTML`
  using class names like `.record`, `.rule-item`,
  `.rule-item.candidate-preview-item`, `.rule-item.candidate-saved-item`.
  Wrapping any of these in component invocations would either drop
  the inner classes or force the JS to know component contracts.
  The page renders raw HTML using token-driven scoped CSS that
  mirrors the component grammar (`.btn`, `.btn--sm`, `.pill`,
  `.panel`, `.panel-header`, `.panel-body`).
- **Preview vs saved candidate grammar is token-driven.** Both
  candidate rows reuse `.rule-item` (shared structure) but get
  different surface tones: previews carry an accent border on the
  left (`--accent`, dashed) and a `pill--neutral`-style "preview"
  pill; saved rows carry a solid `--line` border and a status pill
  whose colour reflects the saved status (`candidate | armed |
  started | dismissed`). At a glance scan distance the dashed-accent
  vs solid-line border is the immediate cue, with the pill confirming
  the exact state — so the AC is met by visual hierarchy, not just a
  label as the story warned against.
- **Connector controls follow one pattern.** Sources, gh/jira (now
  surfaced via project rules + meeting-candidate previews), Firefox
  events, and calendar candidates all use the same row template:
  `Pill (status)` → `Title` → `Meta line` → `Action row` (Preview /
  Run / Output / Destructive). The `danger`-marked actions (Clear
  imported, Clear dismissed, Delete rule) are explicitly visually
  distinguished via `btn--ghost.danger`. Wiring into HS-10-11 stays
  open by design — the destructive class hook is in place; the
  confirmation pattern story will swap behavior, not markup.
- **No inline `<style>` in the served HTML.** Verified:

  ```
  $ grep -cE '<style[^>]*>' holdspeak/static/_built/activity/index.html
  0
  ```

  All styles flow through Astro's bundled CSS chunks linked in the
  `<head>`. The legacy 600-line inline `<style>` blob is gone.

## Acceptance: API contract preserved

The story's last AC is "Existing `/activity` API contracts remain
unchanged." The rebuilt page uses the same `activity-app.js` calls
(verbatim port). The integration test
`tests/integration/test_web_activity_api.py::test_activity_page_serves_browser_surface`
fetches the served HTML, parses out the hoisted JS chunk hash
(`/_built/_astro/hoisted.*.js`), then asserts:

- `/api/activity/status` is referenced.
- `/api/activity/meeting-candidates/preview` is referenced.

Plus every DOM ID the JS reads is present in the rendered HTML
(`enabled-pill`, `candidate-status-filter`, `candidates-message`,
`record-count`, `rule-project`, `meeting-candidates`).

## Acceptance: tests pass

```
$ uv run pytest -q tests/integration/test_web_activity_api.py \
                  tests/integration/test_web_built_mount.py
19 passed in 1.30s

$ uv run pytest -q tests/integration/ --ignore=tests/e2e/test_metal.py
311 passed, 2 skipped in 20.28s
```

`test_web_built_mount.py::test_legacy_routes_still_serve` now expects
`Local activity` (sentence case, new copy) instead of the legacy
`Local Activity`. Behavior under test is unchanged; the marker text
moved with the redesign.

## Acceptance: screenshots

`web/scripts/capture-gallery.py` runs against the built bundle and
captures:

- `screenshots/story-07-activity-desktop.png` (1440×2200)
- `screenshots/story-07-activity-narrow.png` (420×3000)

Both render the empty/initial state (no seeded DB during static
capture). The empty state for each panel calls out a useful next
action (Apply all rules, Preview candidates, Excluded domains
input, etc.). The 420px narrow shot confirms no horizontal overflow
— the side rail collapses above the main column.

## Side-by-side: legacy vs. new

- Legacy `activity.html`: 940 lines (markup + ~600 lines inline CSS
  + ~280 lines inline JS).
- New `activity.astro`: ~440 lines markup + scoped CSS.
- New `activity-app.js`: ~560 lines (verbatim).
- Net source-line delta: +60 lines, but every value flows from
  `tokens.css`. The visual surface is now token-tunable; the legacy
  file required hand-editing the inline `<style>`.

## Acceptance criteria

- [x] All five `/activity` panels render on the new system
  (Controls, Sources, Excluded domains, Project rules, Meeting
  candidates, Recent activity — six panels in the rebuild because
  the legacy "ingestion + retention" was split into Controls +
  Sources for clarity).
- [x] Preview vs saved candidates distinguishable in a 2-second
  glance — dashed-accent left border for previews vs solid-line
  for saved, plus colour-coded status pill.
- [x] Connector controls follow the same grammar across rules,
  candidates, sources, and excluded domains.
- [x] Empty state for each panel names a useful next action
  (panel-message strings: "Apply all to reflect rule changes",
  "Preview to see latest meeting candidates", etc.).
- [x] Activity records list does not horizontally overflow at
  1280px; long URLs wrap (the `.record` row uses
  `overflow-wrap: anywhere` on `.record-meta`).
- [x] Existing `/activity` API contracts unchanged — verified by
  `test_activity_page_serves_browser_surface`.

## Notes for downstream stories

- **HS-10-08 / HS-10-09** continue the pattern (history, dictation):
  port the legacy module to `web/src/scripts/{name}-app.js`, write
  a new `web/src/pages/{name}.astro`, switch the FastAPI route to
  `_built/{name}/index.html`, delete the legacy `*.html`.
- **HS-10-10** (CommandPreview component) should consume the
  connector card grammar formalized here — every connector row
  surfaces `Pill / Title / Meta / Actions` and that's the seed for
  the gh/jira/dry-run preview component.
- **HS-10-11** (destructive confirmation pattern) wires onto the
  `.danger` classed buttons already in place (`Clear imported`,
  `Clear dismissed`, `Delete rule`). No markup migration needed —
  only behavior.
