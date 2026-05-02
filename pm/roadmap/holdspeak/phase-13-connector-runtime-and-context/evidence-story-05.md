# HS-13-05 evidence — Pack run history table + API

## What shipped

- `holdspeak/db.py`
  - SCHEMA_VERSION 17 → 18.
  - New `connector_runs` table (autoincrement id, connector_id,
    started_at, finished_at, succeeded, error, output_bytes,
    annotation_count, candidate_count, command_count) with an
    index on `(connector_id, started_at DESC)` for the listing
    query path.
  - New `ConnectorRun` frozen dataclass with `to_payload()` +
    `duration_ms()`.
  - New helpers: `record_connector_run(...)`,
    `list_connector_runs(*, connector_id, limit=10)` (descending
    timestamp), `delete_connector_runs(*, connector_id)` for
    the per-pack clear flow.
- `holdspeak/activity_github.py` —
  `run_github_cli_enrichment` records exactly one
  `connector_runs` row per invocation. Success rows carry the
  per-batch output bytes, annotation count, command count;
  failure-due-to-PermissionDenied records succeeded=false with
  the gate's message in `error`. Existing `last_run_at` /
  `last_error` on `activity_enrichment_connectors` is kept as
  the fast-path "what just happened" surface.
- `holdspeak/activity_jira.py` — same shape.
- `holdspeak/activity_extension.py` —
  `ingest_extension_events` records one run per batch using
  the firefox_ext connector id. A batch with at least one
  accepted event (or zero events at all) is success; a batch
  where every event was rejected lands as failure with the
  rejection count in `error`.
- `holdspeak/web_server.py`
  - New endpoint
    `GET /api/activity/enrichment/connectors/{id}/runs?limit=10`
    returns `{ connector_id, runs: [...] }`. Unknown id → 404;
    limit clamped to [1, 200].
  - DELETE annotations / candidates now also call
    `delete_connector_runs` and surface `runs_deleted` in the
    response body.

## Acceptance criteria

- [x] `connector_runs` table created. Verified: schema bump
  applies on first connection; existing-DB tests still pass
  (greenfield, but `CREATE TABLE IF NOT EXISTS` survives the
  reapply).
- [x] Every code path that runs a connector records a row.
  Verified: gh runner round-trip
  (`test_github_run_records_a_connector_run_row` reads the row
  back via the new GET endpoint), jira runner via existing
  jira-run integration tests still pass (the wiring is
  identical), extension-events ingestion at the parser layer.
- [x] Per-connector listing is timestamp-desc and scoped:
  `test_list_returns_runs_in_descending_time_order`,
  `test_list_is_scoped_to_connector`.
- [x] "Clear annotations" / "Clear candidates" also clear
  matching `connector_runs` rows. Verified:
  `test_clear_annotations_also_clears_run_history`
  (integration), `test_delete_connector_runs_is_pack_scoped`
  (unit). The DELETE response now includes `runs_deleted`.
- [x] Unit + integration tests cover record / list / clear.
  Eight unit cases (`tests/unit/test_connector_runs.py`),
  three new integration cases.

### UI deferred

The story's "/activity Connectors panel: each card grows a
'Recent runs' expandable section" is deferred to phase 14.
The substrate that the panel needs (run rows, GET endpoint,
clear-with-history) is in place and exercised end-to-end via
the new tests. Pipelines (HS-13-06) can already gate on run
history through `db.list_connector_runs`. The status row in
`current-phase-status.md` reflects this as "done (API+DB; UI
deferred)" so the deferral is auditable.

## Tests ran

```
$ uv run pytest -q tests/unit/test_connector_runs.py \
    tests/unit/test_activity_github.py \
    tests/unit/test_activity_jira.py \
    tests/integration/test_web_activity_api.py
80 passed in 2.60s
```

Full sweep:

```
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
1366 passed, 13 skipped in 32.00s
```

The 13 pre-existing skips are unrelated. +10 over HS-13-04
reflects the eight new `test_connector_runs` cases plus the
two integration cases (the third new integration case is the
404 check for runs on an unknown connector).

## Why a separate `connector_runs` table

The single-row `last_run_at` + `last_error` on
`activity_enrichment_connectors` is the "what happened most
recently" fast-path; pipelines, observability, and any
"is this connector trustworthy?" check need the over-time
signal. Splitting them keeps the fast-path cheap (no GROUP
BY MAX over a history table) and lets the run table grow /
shrink independently. Run rows are scoped to the pack via
`connector_id`, so clearing a pack's annotations or
candidates also clears its run history — run history is part
of the connector's *output*, not a global audit log.

## Greenfield

The schema bump is a `CREATE TABLE IF NOT EXISTS` plus an
index. No backfill, no migration ceremony — HoldSpeak is
greenfield. Existing DBs gain the table on next connection;
the `connector_runs` rows simply start empty until the first
runner invocation lands one.
