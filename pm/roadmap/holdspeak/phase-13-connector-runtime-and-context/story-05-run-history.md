# HS-13-05 - Pack run history table + UI

- **Project:** holdspeak
- **Phase:** 13
- **Status:** backlog
- **Depends on:** HS-13-01
- **Unblocks:** observable connector behaviour
- **Owner:** unassigned

## Problem

Today's `connector.last_error` and `last_run_at` are a single
row of state. If `gh` enrichment succeeded twice and failed
once today, the user sees the most recent of those — they
can't tell whether enrichment is *flaky* or *broken*. Run
history is the difference between "connector is unreliable
sometimes" and "connector worked 9 of 10 times in the last
hour."

## Scope

- **In:**
  - New `connector_runs` table: `id, connector_id, started_at,
    finished_at, succeeded, error, output_bytes,
    annotation_count, candidate_count, command_count`. Indexed
    on `(connector_id, started_at DESC)`.
  - `db.record_connector_run(...)` helper invoked by every
    connector run (gh / jira / calendar / firefox-ext
    ingestion) at completion.
  - `db.list_connector_runs(*, connector_id, limit)` for the
    UI.
  - New `GET /api/activity/enrichment/connectors/{id}/runs`
    endpoint.
  - `/activity` Connectors panel: each card grows a "Recent
    runs" expandable section showing the last N runs as a
    dense list (timestamp, success ✓ / fail ✗, duration ms,
    bytes, counts).
  - Retention: `connector_runs` rows are deleted alongside
    other connector output when the user clicks "Clear
    annotations" / "Clear candidates" — the run history is
    *part of* the connector's output, scoped per pack.
- **Out:**
  - Aggregate metrics dashboard (failure rate over time, p95
    latency). Phase 14 territory if useful.
  - Streaming live updates via the existing meeting WS — the
    panel reloads on click.

## Acceptance Criteria

- [ ] `connector_runs` table created via migration; existing
  DBs gain it without losing data.
- [ ] Every code path that runs a connector records a row
  (success or failure) — covered by integration tests.
- [ ] `/activity` Connectors panel shows the last 10 runs per
  connector, sortable timestamp-desc.
- [ ] "Clear annotations" / "Clear candidates" also clear
  matching `connector_runs` rows for that pack.
- [ ] Unit + integration tests cover record / list / clear.

## Test Plan

- Unit: record_connector_run + list_connector_runs round-trip.
- Integration: gh enrichment run produces one connector_runs
  row with succeeded=true; a forced failure produces succeeded=
  false with the error text.
- Integration: clearing annotations also clears the
  connector_runs rows for that pack.
- UI: the rendered Recent Runs list shows expected entries
  in the page screenshot.

## Notes

Run history is the strongest signal for "is this connector
trustworthy?" — useful for users debugging an integration and
for future automated reliability checks (HS-13-06 pipelines
might gate on "pack X has succeeded ≥ N of the last M runs").
