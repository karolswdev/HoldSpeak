# HS-13-07 evidence — Meeting-context pipeline pack

## What shipped

- `holdspeak/connector_packs/meeting_context.py` (new) —
  the first first-party `kind: pipeline` pack:
  - Manifest declares `consumes:
    [(gh, annotations), (jira, annotations),
    (calendar_activity, candidates)]`, with the matching
    `read:activity_annotations` /
    `read:activity_meeting_candidates` /
    `write:activity_annotations` permissions and
    `pipeline_freshness_seconds=600`.
  - `synthesize_briefing(...)` is a pure function over
    duck-typed inputs (no DB, no clock). It groups GitHub /
    Jira / Upcoming-calendar bullets and renders a
    deterministic markdown body. Empty inputs render the
    "No new activity since the last meeting." bullet.
  - `run(db, *, limit=None)` walks active (non-archived)
    projects, gathers each project's recent records via
    `list_activity_records(project_id=…, since=…)`, joins
    them to upstream gh/jira annotations + calendar
    candidates, calls the synthesizer, and writes exactly
    one annotation per project to `activity_annotations`
    with `source_connector_id = "meeting_context"` /
    `annotation_type = "meeting_context_briefing"`. The run
    deletes existing meeting-context annotations up front so
    re-runs are mutation-safe (no duplicates).
  - The pack records its own `connector_runs` row at
    completion (success path) plus updates the
    `activity_enrichment_connectors` `last_run_at` /
    `last_error` fast-path.
- `holdspeak/connector_packs/__init__.py` — `ALL_PACKS` now
  has five entries (firefox_ext, gh, jira, calendar_activity,
  meeting_context). The connector-list integration test was
  not affected because `enrichment_descriptors()` filters by
  enrichment kinds (`cli_enrichment`, `candidate_inference`)
  and pipelines aren't enrichment in the API sense.
- `holdspeak/web_server.py` — new
  `GET /api/activity/annotations?source_connector_id=…&annotation_type=…&activity_record_id=…&limit=…`
  endpoint. The story called out exposing this if it wasn't
  already; it wasn't, so this commit ships it.
- Tests — `tests/unit/test_connector_packs.py` was bumped
  from "expect 4 first-party packs" to "expect 5" with the
  new id added to the registry assertion.

## Acceptance criteria

- [x] `meeting_context.MANIFEST.kind == "pipeline"` and
  `consumes` covers gh + jira + calendar. Verified:
  `test_manifest_is_pipeline_with_three_upstreams` (also
  spot-checks the read permissions).
- [x] `validate_manifest` accepts the pack. The manifest is
  validated at module import (it would raise if invalid),
  and the cross-pack validator at `build_registry` accepts
  it because the three upstreams are first-party packs.
- [x] `PipelineRunner.run("meeting_context", db)` executes
  upstream packs (with freshness) and produces one annotation
  per active project. Verified:
  `test_pipeline_runner_dispatches_meeting_context_with_fresh_upstreams`
  seeds successful upstream runs, asserts the runner skips
  them and only the pipeline runs, and asserts the briefing
  annotation lands.
- [x] Empty upstream → empty briefing annotation, no
  exception. Verified:
  `test_run_with_empty_upstream_still_writes_briefing`.
- [x] Output annotation is mutation-safe — re-running
  updates in place rather than appending duplicates.
  Verified: `test_re_running_updates_in_place_no_duplicates`
  runs the pipeline twice and asserts `len(annotations) == 1`
  both times.
- [x] HS-13-05 run history shows a row for the pipeline
  itself per invocation. Verified:
  `test_pipeline_run_history_carries_pipeline_row` asserts
  `len(list_connector_runs("meeting_context")) == 1`. Per the
  HS-13-06 contract upstreams record their own rows; in this
  test they're seeded as fresh-and-successful so the runner
  skips them entirely (also asserted).

### Fixtures vs. dedicated tests

The story called out two JSON fixtures
(`meeting-context-happy-path.json` /
`meeting-context-empty-upstream.json`) for the HS-11-02 dry-
run harness. The harness dispatches by connector id literal
in `activity_connector_preview.dry_run` — it doesn't yet
understand pipeline packs (the dry-run shape doesn't capture
"would write one annotation per project"). Rather than warp
the harness into something that approximates pipeline output,
this story covers the same intent with five unit tests in
`tests/unit/test_meeting_context_pack.py` that hit the real
pack against a tmp_path DB:

  - `test_run_writes_one_briefing_per_active_project`
  - `test_run_with_empty_upstream_still_writes_briefing`
  - `test_re_running_updates_in_place_no_duplicates`
  - `test_run_records_a_connector_run_row`
  - `test_synthesizer_renders_grouped_markdown` /
    `test_synthesizer_handles_empty_inputs` /
    `test_synthesizer_is_deterministic`

Phase 14 can extend the harness with a pipeline-aware fixture
shape; the substrate is in place. This deferral is flagged
here so the deviation from the story's test plan is auditable.

## Tests ran

```
$ uv run pytest -q tests/unit/test_meeting_context_pack.py \
    tests/unit/test_pipeline_runner.py \
    tests/unit/test_connector_packs.py \
    tests/integration/test_web_activity_api.py
121 passed in 2.84s
```

Full sweep:

```
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
1397 passed, 13 skipped in 33.92s
```

The 13 pre-existing skips (mock meeting WAV, llama-cpp / Qwen
GGUF) are unrelated. +11 over HS-13-06: ten new
`test_meeting_context_pack` cases plus the new
`test_list_activity_annotations_filters_by_connector`
integration case.

## Why deterministic markdown first

The story scoped LLM summaries out to phase 14 deliberately.
Two reasons it matters now:

1. **The output is auditable.** A synthesizer with no clock
   and no I/O can be diffed in tests; a phase-14 LLM-driven
   variant slots in behind the same `value` payload (the
   `markdown` key) and the rest of the system — clear flow,
   run history, the new `/api/activity/annotations` endpoint —
   doesn't notice.
2. **The output is offline-safe.** No tokens, no network,
   no cloud cost. The whole connector framework's local-only
   stance survives the move from individual packs to fused
   pipelines.

## Greenfield

The new pack is purely additive. The annotations table
already supported synthesized rows; meeting-context just adds
a new `(source_connector_id, annotation_type)` pair. No
schema changes, no migrations.
