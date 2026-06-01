# Evidence — HS-26-04 — Extract Activity / Connector / Plugin-Job Routes

- **Shipped:** 2026-05-31
- **Commit:** (pending — same commit as this evidence file)
- **Owner:** Claude (agent)

## What shipped

The activity-intelligence cluster — **38 routes** — moved off
`MeetingWebServer._create_app` into `holdspeak/web/routes/activity.py`
(`build_activity_router(ctx)`), reading from `WebContext`. Handlers moved
verbatim (`self.` → `ctx.`).

Routes moved:

- Activity core: `GET /api/activity/status`, `GET /api/activity/records`,
  `POST /api/activity/refresh`, `PUT /api/activity/settings`,
  `DELETE /api/activity/records`.
- Domain + project rules: `POST|DELETE /api/activity/domains[/{domain}]`,
  `GET|POST /api/activity/project-rules`, `PUT|DELETE .../{rule_id}`,
  `POST .../preview`, `POST .../apply`.
- Enrichment connectors: `GET /api/activity/enrichment/connectors`,
  `PUT .../{connector_id}`, `.../dry-run`, `DELETE .../annotations`,
  `DELETE .../candidates`, `.../runs`, GitHub `preview`+`run`, Jira `preview`+`run`,
  `POST /api/activity/enrichment/pipelines/{pipeline_id}/run`.
- Extension ingest, annotations list, briefing.
- Meeting candidates: `preview`, `GET`, `POST`, `PUT .../{id}/status`,
  `POST .../{id}/start`, `DELETE`.
- Plugin-job queue: `GET /api/plugin-jobs`, `.../summary`, `POST .../process`,
  `POST .../{job_id}/retry-now`, `POST .../{job_id}/cancel`.

## Files touched

- `holdspeak/web/routes/activity.py` — **new** (1351 lines); `build_activity_router`.
- `holdspeak/web/context.py` — added `on_process_plugin_jobs` (default `None`).
- `holdspeak/web/routes/__init__.py` — exports `build_activity_router`.
- `holdspeak/web_server.py` — removed the inline activity + plugin-job routes and
  **relocated 6 activity-only module-level helpers** (`_model_fields_set`, the four
  `_activity_*_payload` builders, and `_meeting_payload_id`) into `activity.py`;
  mounts `build_activity_router(web_ctx)`; dropped 9 now-unused request-model
  imports. **3130 → 1817 lines (−1313).** Cumulative HS-26-02..04: **5658 → 1817**.

## Verification artifacts

```
$ uv run pytest -q tests/ -k "web and (activity or connector or plugin or enrichment or candidate or briefing)"
45 passed

$ uv run pytest -q --ignore=tests/e2e/test_metal.py
1879 passed, 13 skipped        (no regressions; full suite is the gate)

$ uv run ruff check holdspeak/web/ holdspeak/web_server.py
All checks passed!
```

**Route-inventory diff** (built app, `app.routes`, vs the original `origin/main`
baseline `f77c2d9`): identical paths/methods, 122 HTTP routes.

## Decisions / scope

- **Helper relocation, not monolith import.** The four `_activity_*_payload`
  builders, `_model_fields_set`, and `_meeting_payload_id` are used **only** by
  these routes (verified across `holdspeak/` + `tests/`), so they were moved into
  `activity.py` rather than imported back from `web_server` — keeping the module
  decoupled (continuing the HS-26-03 follow-up's direction).
- **Two genuinely-shared helpers are imported** from `web_server`:
  `_meeting_callback_payload` (also used by `routes/meetings.py`) and
  `_parse_iso_datetime` (still used by `web_server` itself). HS-26-06 re-homes the
  shared helpers and drops these imports.
- **`/api/projects/{project_id}/briefings` stays inline.** Although it sits inside
  the activity block and returns activity briefings, its path is `/api/projects/*`
  → it belongs to HS-26-05's project module. It is self-contained (db-backed, no
  `self.`), so leaving it inline is zero-risk; the extraction skips it.
- **No new lifecycle callbacks needed** beyond `on_process_plugin_jobs`: the
  meeting-candidate-start route reuses `on_start` / `on_update_meeting` / `broadcast`
  (added in HS-26-02).
- `activity.py` kept as one module (1351 lines); revisit a split at HS-26-07.

## Acceptance criteria — re-checked

- [x] Listed routes served from `routes/activity.py`; none remain inline in `_create_app()`.
- [x] Existing activity/connector/plugin-job web tests pass unchanged.
- [x] Route-inventory diff shows identical paths/methods for the moved set.

## Follow-ups

- HS-26-05 (device / companion / project routes — incl. the inline briefings
  route + the `/api/projects/*` + `/api/settings` + companion/devices handlers);
  HS-26-06 collapses the callback bag and re-homes the shared helpers.
