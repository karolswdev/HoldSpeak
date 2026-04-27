# HS-9-12 - Connector controls and output deletion

- **Project:** holdspeak
- **Phase:** 9
- **Status:** backlog
- **Depends on:** HS-9-01, HS-9-08
- **Unblocks:** safe opt-in connector execution and cleanup
- **Owner:** unassigned

## Problem

Connector state and annotations exist, but users cannot yet manage
connectors from the browser. Before CLI or extension connectors are
enabled, `/activity` needs visible connector status, enablement, preview,
last-run errors, and deletion of connector outputs.

## Scope

- **In:**
  - Connector list API and browser panel.
  - Enable/disable connector state.
  - Show connector source kind, capability list, last run, and last error.
  - Clear annotations and meeting candidates by connector.
  - Confirm destructive clear actions.
  - Tests for connector state APIs and deletion filters.
- **Out:**
  - Running `gh` or `jira`.
  - Firefox extension event ingestion.
  - External OAuth or token storage.

## Acceptance Criteria

- [ ] `/activity` shows known connector states.
- [ ] User can enable or disable a connector.
- [ ] User can clear connector-created annotations.
- [ ] User can clear connector-created meeting candidates.
- [ ] Last-run errors are visible.
- [ ] No connector can run invisibly.

## Test Plan

- Integration tests for connector state APIs.
- Unit tests for deletion by connector.
- Browser surface test for connector panel.
