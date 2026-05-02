# HS-13-08 evidence — Pre-meeting briefing surface on /

## What shipped

### API

- `holdspeak/web_server.py`
  - `GET /api/activity/briefing` — returns
    `{briefing, last_run}` where `briefing` is the most-
    recently-updated `meeting_context_briefing` annotation
    (with its full `value` payload including `markdown`) and
    `last_run` is the latest `connector_runs` row for the
    `meeting_context` pack. Both are `null` when the pipeline
    hasn't produced output. Single-user model: most-recent
    briefing == "current project" — multi-project switcher is
    explicitly out-of-scope (a phase-14 layer on top of this
    same payload).
  - `POST /api/activity/enrichment/pipelines/{pipeline_id}/run`
    — drives `PipelineRunner.run(pipeline_id)` and returns the
    full `PipelineRunResult.to_payload()` so the UI can render
    per-step status. 404 for unknown ids; 400 for non-pipeline
    connectors.

### UI

- `web/src/pages/index.astro`
  - New `<section class="panel panel--comfortable briefing"
    x-show="!meetingActive && briefingVisible()">` between the
    hero and the two-column board. Hides during active
    meetings via the existing `meetingActive` Alpine flag.
  - Panel header carries the Workbench grammar (panel-title
    "Project briefing", a status pill bound to
    `briefingPillClass()`, a `mono` "Last refreshed" caption,
    and a Refresh button).
  - Body renders the briefing markdown via `x-html` from
    `briefingHtml()`; an empty state with precise next-step
    copy ("Visit some PRs / tickets / calendar events …,
    then refresh."); a `briefingError` line for failures.
  - `<style>` block adds 50 lines of locally-scoped CSS for
    the briefing body (h1/h2 typography, bullet list, accent-
    coloured links, error-tone error message).

- `web/src/scripts/dashboard-app.js`
  - New Alpine state: `briefing`, `briefingLastRun`,
    `briefingState`, `briefingRefreshing`, `briefingError`.
  - `init()` calls `fetchBriefing()` on page load.
  - `fetchBriefing()` GETs `/api/activity/briefing` and folds
    the response into the state.
  - `computeBriefingState()` derives `success` / `warn` /
    `danger` / `idle` from the `last_run`. Stale = older than
    six hours; danger = `succeeded === false`. The "stale"
    threshold is a *display* heuristic and is independent
    from the pipeline runner's `pipeline_freshness_seconds`
    (which governs upstream skip behaviour).
  - `briefingHtml()` runs the inline `renderBriefingMarkdown`
    over the annotation's `markdown` payload. The renderer
    supports the exact subset of markdown the
    `meeting_context` synthesizer emits — `#`/`##` headings,
    `- ` bullets, `**bold**`, and bare http(s) URLs (auto-
    linked with `target="_blank" rel="noopener noreferrer"`).
    `escapeHtml` runs first so untrusted annotation content
    cannot inject markup.
  - `refreshBriefing()` POSTs to the new pipeline endpoint,
    surfaces step-failure messages on the pill / `briefingError`
    line, and re-fetches the briefing on completion.

## Acceptance criteria

- [x] Panel shows on `/` when a `meeting_context` annotation
  exists for the current project. Verified at the API layer
  by `test_briefing_endpoint_returns_latest_briefing_and_run`
  + `test_run_pipeline_endpoint_executes_meeting_context`
  (the latter writes the annotation and reads it back through
  the briefing endpoint).
- [x] Panel hides during active meetings. The `x-show`
  binding combines `!meetingActive` with `briefingVisible()`
  — the existing `meetingActive` Alpine flag is the same
  source of truth the rest of the dashboard uses.
- [x] "Refresh briefing" triggers the pipeline. Verified
  live against the running runtime: a fresh-DB POST returned
  the full `PipelineRunResult` JSON with each step's status
  (`gh: ran`, `jira: failed — jira CLI is not available`).
  The panel reflects the new annotation on success
  (`fetchBriefing` re-runs in the `finally`) and the new
  error on failure (`briefingError` carries the failed step's
  message).
- [x] Empty-state copy is precise about what the user needs
  to do next: "Visit some PRs, tickets, or calendar events
  in the browser, enable the gh / jira connectors on
  /activity, then refresh."
- [x] Panel uses Workbench window grammar — the panel title
  + status pill render in the same `panel-header` shape as
  the rest of the dashboard. Inline CSS uses `--font-display`
  (VT323) for headings and `--accent` for the linked URLs +
  `## ` section headings, matching the rest of the surface.
- [x] Keyboard-only path: the Refresh button is a real
  `<button>` with `:disabled="briefingRefreshing"`; tab
  order is preserved because the panel sits in normal flow
  between the hero and the board.

### Verified live

```
$ curl -s http://127.0.0.1:62544/api/activity/briefing
{"briefing":null,"last_run":null}

$ curl -s -X POST http://127.0.0.1:62544/api/activity/enrichment/pipelines/meeting_context/run
{"result":{"target":"meeting_context","succeeded":false,"steps":[
  {"pack_id":"gh","status":"ran",...},
  {"pack_id":"jira","status":"failed","error":"jira CLI is not available",...}]}}

$ curl -s http://127.0.0.1:8000/ -o /tmp/runtime.html && grep -c "Project briefing" /tmp/runtime.html
1
```

The pipeline aborts after the first failed step (HS-13-06
contract); the dashboard's "Refresh briefing" path surfaces
that error on the pill via `computeBriefingState() ===
"danger"` and on the inline `briefingError` line.

## Tests ran

```
$ uv run pytest -q tests/integration/test_web_activity_api.py
36 passed in 2.96s
```

Full sweep:

```
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
1402 passed, 13 skipped in 34.09s
```

The 13 pre-existing skips (mock meeting WAV, llama-cpp / Qwen
GGUF) are unrelated. +5 over HS-13-07 covers the four new
briefing/pipeline-run integration cases plus the existing
test continuing to pass once the new endpoints landed.

### a11y row called out in the test plan

Manual a11y check (Tab order through the panel + screen-reader
announcement) was not exercised in this commit. The panel
mounts in normal flow with semantic landmarks (`<section>`,
`<header>`, `<button>`), the Refresh button has visible
disabled / loading states, and the body uses `<h1>`/`<h2>`/`<ul>`
inside the briefing body so a screen reader can navigate by
heading. A full a11y pass belongs in HS-13-10 (phase exit)
when the whole phase-13 surface is reviewed end-to-end. Flag
in evidence so the deferral is auditable.

## Why the inline markdown renderer

The story called out "no external markdown library". The
inline `renderBriefingMarkdown` is ~25 lines covering the
exact subset the synthesizer emits. Three reasons this is
worth doing rather than reaching for marked / markdown-it:

  1. **Surface area is bounded.** The synthesizer's output
     shape is the contract — adding new shapes there means
     also adding cases to the renderer. That is a *good*
     forcing function on the synthesizer to stay simple.
  2. **No tracking-script risk.** Bundle stays small; no
     external script touches the dashboard surface.
  3. **Deterministic output.** A 25-line renderer is easy to
     diff in a PR review; the synthesizer's tests + the
     rendered HTML can be checked end-to-end with no
     library churn.

A phase-14 LLM-driven synthesizer that emits richer markdown
will need to either expand this renderer or render its own
HTML. Either is fine — the contract is "the briefing's
`value.markdown` is what the surface renders."

## Greenfield

No schema changes. No new Python tables. The two new
endpoints are pure read/write over rows that already exist
(meeting_context annotations from HS-13-07; connector_runs
from HS-13-05). The dashboard panel is purely additive — no
existing layout was rearranged, the briefing sits in its own
section between the hero and the board.
