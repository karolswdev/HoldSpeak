# HS-26-04 — Extract Activity / Connector / Plugin-Job Routes

- **Project:** holdspeak
- **Phase:** 26
- **Status:** done
- **Depends on:** HS-26-01
- **Unblocks:** HS-26-07
- **Owner:** Claude (agent)

## Problem

Activity-intelligence, connector-enrichment, and plugin-job routes
(`/api/activity/*`, `/api/plugin-jobs*`) form another cohesive cluster to move
behind the HS-26-01 seam.

## Scope

### In

- Move `/api/activity/*` (refresh, project-rules, enrichment connectors,
  meeting candidates) and `/api/plugin-jobs*` routes into `routes/activity.py`.
- Read from the shared context; no behavior change.

### Out

- Other domains (HS-26-02, HS-26-03, HS-26-05).
- Callback removal beyond these routes (HS-26-06).

## Acceptance criteria

- [x] Listed routes are served from the new module; none remain inline.
- [x] Existing activity/connector/plugin-job web tests pass unchanged.
- [x] Route-inventory diff shows identical paths/methods for the moved set.

## Test plan

- Unit: `uv run pytest -q tests/ -k "web and (activity or connector or plugin)"`.
- Integration: activity refresh + connector toggle via the runtime.
- Manual: n/a.

## Notes / open questions

- Connector enable/disable mutates config; confirm it reads the same shared
  context path the other mutation routes use.
- **Resolved:** activity reads close over no server state; only the meeting-
  candidate-start route needs callbacks (`on_start`/`on_update_meeting`/`broadcast`,
  all existing) + the new `on_process_plugin_jobs` for the plugin-job queue.
- **Shipped as one module** (`routes/activity.py`, 1351 lines, 38 routes). 6
  activity-only helpers were **relocated** into it (out of `web_server`);
  `_meeting_callback_payload` + `_parse_iso_datetime` are shared, so imported from
  `web_server` (HS-26-06 re-homes). `web_server.py` 3130 → 1817 (cumulative 5658 →
  1817). `/api/projects/{project_id}/briefings` left inline for HS-26-05 (it is a
  `/api/projects/*` path). See `evidence-story-04.md`.
