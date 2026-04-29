# HS-11-02 - Connector fixture and dry-run test harness

- **Project:** holdspeak
- **Phase:** 10
- **Status:** backlog
- **Depends on:** HS-11-01
- **Unblocks:** connector pack regression testing
- **Owner:** unassigned

## Problem

Connectors will touch local browser events and developer CLIs. Each
connector needs fixture-driven tests so behavior can be proven without
real browser profiles, real Jira/GitHub accounts, or live network calls.

## Scope

- **In:**
  - Fixture format for activity records, connector command output, and
    expected annotations/candidates.
  - Dry-run runner for connector fixtures.
  - Golden-output tests for first-party connectors.
  - No-mutation assertions.
- **Out:**
  - Live connector execution.
  - External service test accounts.

## Acceptance Criteria

- [ ] Fixtures can drive connector preview behavior.
- [ ] Dry-run tests assert no database mutation.
- [ ] First-party connectors can share the same harness.
- [ ] Fixture failures show readable diffs.
