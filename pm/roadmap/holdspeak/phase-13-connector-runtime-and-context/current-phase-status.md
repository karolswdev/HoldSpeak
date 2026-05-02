# Phase 13 - Connector Runtime + Pipelines + Meeting Context

**Last updated:** 2026-05-01 (HS-13-03 done — pack-declared settings + defaults).

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
| HS-13-04 | Local-user pack discovery | backlog | [story-04-user-pack-discovery.md](./story-04-user-pack-discovery.md) | pending |
| HS-13-05 | Pack run history table + UI | backlog | [story-05-run-history.md](./story-05-run-history.md) | pending |
| HS-13-06 | Pipeline manifest + dependency-graph runner | backlog | [story-06-pipeline-runner.md](./story-06-pipeline-runner.md) | pending |
| HS-13-07 | Meeting-context pipeline pack | backlog | [story-07-meeting-context-pack.md](./story-07-meeting-context-pack.md) | pending |
| HS-13-08 | Pre-meeting briefing surface on / | backlog | [story-08-prebriefing-surface.md](./story-08-prebriefing-surface.md) | pending |
| HS-13-09 | Cross-meeting summary on /history | backlog | [story-09-history-project-summary.md](./story-09-history-project-summary.md) | pending |
| HS-13-10 | Phase exit + DoD | backlog | [story-10-dod.md](./story-10-dod.md) | pending |

## Where We Are

A-arc opening story (HS-13-01) is closed: `connector_packs/`
ships a fourth pack (`calendar_activity`), and
`activity_connectors.KNOWN_CONNECTORS` is now derived from
`connector_packs.ALL_PACKS` instead of a hand-written tuple.

HS-13-02 ships `holdspeak/connector_runtime.py` with a
`PermissionGate` enforcing the manifest's declared permissions
at the runtime gates.

HS-13-03 extends the manifest with a `settings_schema`
(`SettingDescriptor(key, type, default, label, help)` per
tunable) and adds `resolve_setting(manifest, settings, key)`
to the SDK. gh / jira packs declare timeout / max_bytes /
limit; calendar declares limit; firefox_ext declares an empty
schema. The web run endpoints + the PUT settings endpoint are
wired through the schema — any `settings` key not on the
pack's schema is rejected with a 400 naming the offending
keys + the allowed set.

Next: HS-13-04 (local-user pack discovery), HS-13-05 (run
history). -06 unblocks the B-arc; -07 unblocks the C-arc.

## Source Design

- `holdspeak/connector_packs/` — phase-11 first-party packs.
- `holdspeak/connector_sdk.py` — manifest contract.
- `holdspeak/connector_fixtures.py` — phase-11 fixture harness.
- `holdspeak/activity_connectors.py` — the registry phase 13 will
  rewrite as pack-derived.
- `docs/CONNECTOR_DEVELOPMENT.md` — phase-11 developer guide;
  phase 13 will extend the "Lifecycle" + "Permission model"
  sections as the runtime gates land.
