# HS-26-04 — Extract Activity / Connector / Plugin-Job Routes

- **Project:** holdspeak
- **Phase:** 26
- **Status:** backlog
- **Depends on:** HS-26-01
- **Unblocks:** HS-26-07
- **Owner:** unassigned

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

- [ ] Listed routes are served from the new module; none remain inline.
- [ ] Existing activity/connector/plugin-job web tests pass unchanged.
- [ ] Route-inventory diff shows identical paths/methods for the moved set.

## Test plan

- Unit: `uv run pytest -q tests/ -k "web and (activity or connector or plugin)"`.
- Integration: activity refresh + connector toggle via the runtime.
- Manual: n/a.

## Notes / open questions

- Connector enable/disable mutates config; confirm it reads the same shared
  context path the other mutation routes use.
