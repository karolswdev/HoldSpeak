# Phase 13 - Connector Runtime + Pipelines + Meeting Context

**Last updated:** 2026-05-04 (HS-13-10 done — phase exit; phase 13 closed).

## Goal

Phase 11 built the connector framework; phase 13 turns it on and uses
it. Three sequential arcs land here:

- **A. Runtime substrate** — make the manifests the runtime's source
  of truth, not documentation. Pack-driven registry, permission
  enforcement, pack-declared settings, local-user pack discovery,
  pack run history.
- **B. Pipelines** — packs that consume other packs' output.
  Pipeline manifest type, dependency-graph runner, a first-party
  meeting-context pipeline pack that fuses `gh` + `jira` + calendar
  outputs into a single project briefing annotation.
- **C. Meeting-side context engine** — consumer-facing payoff. Pre-
  meeting briefing surface on `/` shows the project briefing for
  the current context. Cross-meeting summary on `/history` gives
  per-project narratives across sessions.

The phase is intentionally sequential: B builds on A, C builds on B.
Closing the substrate gap now (instead of layering more features on
top of it) means phases 14+ build on solid ground.

## Scope

- **In:**
  - Replace `activity_connectors.KNOWN_CONNECTORS` with a registry
    derived from `connector_packs/ALL_PACKS`.
  - Permission enforcement at the runtime gates: `shell:exec`
    checked before subprocess; `network:outbound` checked before
    any non-loopback fetch.
  - Per-pack settings (timeout, max_bytes, limits) move from
    hard-coded module constants into pack-declared defaults
    overridable via the existing connector settings JSON.
  - Local-user pack discovery from `~/.holdspeak/connector_packs/`
    with a sandboxed loader.
  - `connector_runs` table + run-history surface in `/activity`
    Connectors panel.
  - Pipeline manifest type (`kind: pipeline`); deterministic
    dependency-graph runner; a `meeting_context` pipeline pack.
  - Pre-meeting briefing surface on `/`; cross-meeting project
    briefing on `/history`.
  - Phase exit + fixture coverage for permission-violation
    rejections + pipeline graph resolution.
- **Out:**
  - Remote pack distribution / marketplace.
  - Cloud-backed connector packs.
  - OAuth or token management.
  - Multi-user / role-based permissions — single-user model
    stays.
  - Page-level transitions on `/` or `/history`.

## Story Status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-13-01 | Pack-driven runtime registry | done | [story-01-pack-registry.md](./story-01-pack-registry.md) | [evidence-story-01.md](./evidence-story-01.md) |
| HS-13-02 | Permission enforcement at runtime gates | done | [story-02-permission-enforcement.md](./story-02-permission-enforcement.md) | [evidence-story-02.md](./evidence-story-02.md) |
| HS-13-03 | Pack-declared settings + defaults | done | [story-03-pack-settings.md](./story-03-pack-settings.md) | [evidence-story-03.md](./evidence-story-03.md) |
| HS-13-04 | Local-user pack discovery | done | [story-04-user-pack-discovery.md](./story-04-user-pack-discovery.md) | [evidence-story-04.md](./evidence-story-04.md) |
| HS-13-05 | Pack run history table + UI | done (API+DB; UI deferred) | [story-05-run-history.md](./story-05-run-history.md) | [evidence-story-05.md](./evidence-story-05.md) |
| HS-13-06 | Pipeline manifest + dependency-graph runner | done | [story-06-pipeline-runner.md](./story-06-pipeline-runner.md) | [evidence-story-06.md](./evidence-story-06.md) |
| HS-13-07 | Meeting-context pipeline pack | done | [story-07-meeting-context-pack.md](./story-07-meeting-context-pack.md) | [evidence-story-07.md](./evidence-story-07.md) |
| HS-13-08 | Pre-meeting briefing surface on / | done | [story-08-prebriefing-surface.md](./story-08-prebriefing-surface.md) | [evidence-story-08.md](./evidence-story-08.md) |
| HS-13-09 | Cross-meeting summary on /history | done | [story-09-history-project-summary.md](./story-09-history-project-summary.md) | [evidence-story-09.md](./evidence-story-09.md) |
| HS-13-10 | Phase exit + DoD | done | [story-10-dod.md](./story-10-dod.md) | [evidence-story-10.md](./evidence-story-10.md) |

## Where We Are

A-arc opening story (HS-13-01) is closed: `connector_packs/`
ships a fourth pack (`calendar_activity`), and
`activity_connectors.KNOWN_CONNECTORS` is now derived from
`connector_packs.ALL_PACKS` instead of a hand-written tuple.

HS-13-02 ships `holdspeak/connector_runtime.py` with a
`PermissionGate` enforcing the manifest's declared permissions
at the runtime gates.

HS-13-03 extends the manifest with a `settings_schema` and
adds `resolve_setting(manifest, settings, key)`; the web run
endpoints + PUT validation read through the schema.

HS-13-04 ships local-user pack discovery; descriptors carry
a `source` field; doctor surfaces every discovered pack.

HS-13-05 ships `connector_runs` and run-history API; UI panel
deferred to phase 14.

HS-13-06 opens the B-arc with `kind: pipeline` + the
`PipelineRunner`.

HS-13-07 ships the meeting_context pipeline pack: deterministic
markdown briefing per active project, mutation-safe re-runs.

HS-13-08 surfaces the briefing on the runtime dashboard.

HS-13-09 ships the second consumer surface. The /history
Projects-tab gains a "Project briefing timeline" card under
the project metadata: each row is the project's
meeting_context annotation, newest first, expand-toggled
inline (no modal). "Run briefing now" POSTs the same
pipeline-run endpoint the dashboard uses; success refreshes
the timeline. The pack now keeps a content-hash-deduped
history — re-running with no upstream changes still produces
no duplicate, but a real upstream change appends a new
snapshot. New `GET /api/projects/{id}/briefings` endpoint
returns the rows scoped to one project. Markdown renderer
extracted to `web/src/scripts/briefing-markdown.js` and
concatenated into both the dashboard and history factories
via the existing `?raw` loader pattern, so there is one
definition.

HS-13-10 closes the phase: `docs/CONNECTOR_DEVELOPMENT.md`
gains a "Phase 13 additions" section covering the pipeline
kind, the runtime permission gates, local-user pack
discovery, and the `connector_runs` history surface; the
parent README is bumped; the regression sweep
(`uv run pytest -q --ignore=tests/e2e/test_metal.py`) is
green at 1406 passed / 13 skipped after the time-bomb
fixture in `test_run_pipeline_endpoint_executes_meeting_context`
was switched off a hardcoded `2026-05-02 11:00:00` and onto
`datetime.now()`. Designer-handoff screenshots are deferred
to a manual user pass against the running web app — see
`evidence-story-10.md` for that handoff. Phase 13 is closed;
phase 14 picks up the deferred connectors-panel run-history
view and per-project pipeline-run args.

## Source Design

- `holdspeak/connector_packs/` — phase-11 first-party packs.
- `holdspeak/connector_sdk.py` — manifest contract.
- `holdspeak/connector_fixtures.py` — phase-11 fixture harness.
- `holdspeak/activity_connectors.py` — the registry phase 13 will
  rewrite as pack-derived.
- `docs/CONNECTOR_DEVELOPMENT.md` — phase-11 developer guide;
  phase 13 will extend the "Lifecycle" + "Permission model"
  sections as the runtime gates land.
