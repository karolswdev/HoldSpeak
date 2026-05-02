# HS-13-09 evidence — Cross-meeting summary on /history

## What shipped

### Backend

- `holdspeak/connector_packs/meeting_context.py` —
  - The pipeline now keeps a deduped *history* of briefings
    rather than overwriting one row per project. Each run
    looks up the most-recent meeting_context annotation per
    project; if the freshly-synthesized markdown matches the
    previous briefing's `value.markdown`, the run skips the
    write (idempotent). If they differ, a new annotation is
    appended — that's the row /history's timeline walks.
  - Dropped the `since=` filter on `list_activity_records`.
    A project's full record set is scanned every run (the
    synthesizer dedupes by content), so a gh / jira annotation
    that lands on an older record is reflected in the next
    briefing instead of falling outside the time window.
- `holdspeak/web_server.py` — new
  `GET /api/projects/{project_id}/briefings?limit=50` endpoint.
  Walks `meeting_context_briefing` annotations whose
  `value.project_id` matches; returns rows newest-first; 404
  for unknown project ids.

### Shared util

- `web/src/scripts/briefing-markdown.js` (new) — a 60-line
  module exporting `renderBriefingMarkdown` (h1/h2 headings,
  `- ` bullets, `**bold**`, auto-linked http(s) URLs, escaped
  HTML throughout) and `briefingFirstLine` (skip headings,
  return first content line — used as the timeline row
  summary). Both `index.astro` and `history.astro` prepend
  this source to their respective Alpine factories via
  `?raw` + `new Function`, so there is one renderer
  definition and zero duplication. The dashboard's old inline
  renderer was deleted (see commit diff).

### UI

- `web/src/pages/history.astro`
  - New "Project briefing timeline" card under the existing
    project Summary card (Projects tab → project detail
    view). Header carries a "Run briefing now" button that
    drives the same POST-pipeline endpoint the dashboard
    uses. Empty-state copy when the project has no
    briefings; loading state while the endpoint is in
    flight; an error line for pipeline-run failures.
  - Each timeline row is a `<li>` with a `<button>` toggle —
    timestamp + first-line summary + chevron — that expands
    inline to render the full markdown body via the shared
    util. Workbench window grammar throughout (panel,
    pill row, accent-coloured h2, mono timestamps).

- `web/src/scripts/history-app.js`
  - New Alpine state: `projectBriefings`,
    `loadingBriefingTimeline`, `briefingExpanded`,
    `briefingRunInProgress`, `briefingTimelineError`.
  - New methods: `loadProjectBriefings`,
    `toggleBriefing(briefingId)`, `briefingFirstLineFor`,
    `briefingHtmlFor`, `runProjectBriefing`. The last one
    POSTs the pipeline-run endpoint, surfaces step-failure
    messages, and refreshes the timeline on completion.
  - `openProject(projectId)` resets the timeline state and
    fires `loadProjectBriefings()` alongside the existing
    parallel sub-data loads.

## Acceptance criteria

- [x] Selecting a project shows the briefing timeline panel.
  Verified live: `curl /history/` returns 200 and the built
  HTML contains the "Project briefing timeline" markup;
  `loadProjectBriefings()` fires from `openProject`.
- [x] Empty-state copy when no briefings exist. The card's
  `<div x-show="!loadingBriefingTimeline && projectBriefings.length === 0">`
  renders the "No briefings for this project yet…" message.
- [x] Timeline rows expand inline (no modal); markdown
  renders bullets + bold + links. Each row's expanded body
  uses `x-html="briefingHtmlFor(briefing)"` which in turn
  calls the shared `renderBriefingMarkdown`.
- [x] "Run briefing now" runs the pipeline for the selected
  project's id; success refreshes the timeline.
  `runProjectBriefing` POSTs `/api/activity/enrichment/pipelines/meeting_context/run`
  and `await loadProjectBriefings()` runs in the `finally`.
  Note: the meeting_context pipeline writes one annotation
  per active project in the same run — the "scoped to the
  selected project" framing in the story is satisfied at
  the *display* layer (the GET endpoint filters by
  project_id), not at the pipeline-run layer (running the
  pipeline once refreshes every project's briefing). Phase
  14 can add a per-project run-args path on the endpoint if
  the use case justifies it; flagging here so the deviation
  is auditable.
- [x] Workbench window grammar throughout. The new card
  reuses the existing `.detail-card` shape; the timeline
  rows have hard 1-px borders, accent-coloured chevrons,
  VT323-faced headings inside the expanded body, mono
  timestamps in the row toggle.
- [x] Inline renderer extracted to a shared util. Both
  factories pull `briefing-markdown.js?raw`, strip its
  `export` keyword, and prepend it to the factory body.
  Verified at build time: the dashboard bundle has 7
  references and the history bundle has 1 — both call into
  the same definition.

## Tests ran

```
$ uv run pytest -q tests/unit/test_meeting_context_pack.py \
    tests/integration/test_web_activity_api.py
50 passed in 3.28s
```

Full sweep:

```
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
1406 passed, 13 skipped in 34.33s
```

The 13 pre-existing skips (mock meeting WAV, llama-cpp / Qwen
GGUF) are unrelated. +4 over HS-13-08: three new project-
briefings endpoint cases plus the test rename / split that
encodes the new "history kept; deduped by content" contract
in `test_meeting_context_pack.py`.

### Live verification

```
$ uv run holdspeak web --no-open  # background
$ curl /api/projects/no_such/briefings → 404
$ curl /history/ → 200; built HTML contains "Project briefing timeline" + "briefing-row"
$ grep renderBriefingMarkdown holdspeak/static/_built/_astro/*.js → 3 bundles (shared module + both factories)
```

## Why content-hash dedup beats time-window dedup

HS-13-07 originally used delete-and-recreate to avoid
duplicate briefings. That conflicts directly with HS-13-09's
need for a timeline. The two compatible alternatives were:

  1. **Time-window dedup**: keep all briefings, skip writes
     within an N-minute window. Simple, but lossy when an
     upstream produces fast-cadence updates and the user
     refreshes the dashboard right after.
  2. **Content-hash dedup**: skip writes when the synthesized
     markdown matches the previous briefing's body. The chosen
     approach.

(2) is the correct mental model: every meaningful change
appends a snapshot; idempotent re-runs are silent. The
synthesizer's deterministic output makes the equality check
cheap and exact.

## Greenfield

No schema changes; the new endpoint is a read over existing
rows. The pipeline pack's behaviour change (no delete on
re-run) is a content semantics change documented in tests +
evidence; HoldSpeak is greenfield so no migration is needed.
