# HS-133-07 — Plugin jobs over the wire

- **Project:** holdspeak
- **Phase:** 133
- **Status:** done
- **Depends on:** HS-133-01
- **Unblocks:** HS-133-11
- **Owner:** unassigned

## Problem

The deferred plugin-job pipeline is invisible and undriveable from MCP.
`PluginJobService` supports list (:24), summary (:27), retry (:31, which
refuses running jobs at :34), and cancel (:39, refusing running jobs at
:42) — the Plugin RFC's Phase-2 observability promise, unexposed.

## Scope

### In

Per assets/surface-spec.md §1G, verbatim:
`holdspeak/mcp/families/plugin_job.py` implementing `plugin_job.list`,
`plugin_job.summary`, `plugin_job.retry`, `plugin_job.cancel` with the
spec's schemas (status enum, integer `job_id`). The `plugin_job.list`
description names queue *processing* as unavailable from the sidecar
(it requires the live-runtime `ctx.on_process_plugin_jobs` callback).

### Out

- A `plugin_job.process` verb (live-runtime callback; out per spec). Any
  PluginJobService change. Any resource (job state is transient).

## Acceptance criteria

- [ ] All four tools in the catalogue with closed schemas, dispatching
  to the anchored methods.
- [ ] Retry/cancel against a running job surface the service's refusal
  as `isError: true`; retry against an unknown `job_id` likewise.
- [ ] REQUIRED_TOOLS extended with the four names.

## Test plan

- `HOME=$(mktemp -d) uv run pytest -q tests/unit/test_mcp_phase133.py tests/unit/test_mcp_tools.py --tb=short`
