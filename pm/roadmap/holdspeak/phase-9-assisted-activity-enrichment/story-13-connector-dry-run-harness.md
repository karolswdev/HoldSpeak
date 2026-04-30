# HS-9-13 - Connector dry-run harness

- **Project:** holdspeak
- **Phase:** 9
- **Status:** done
- **Depends on:** HS-9-12
- **Unblocks:** safe connector previews before mutation
- **Owner:** unassigned

## Problem

Assisted connectors need a repeatable way to show what they would do
before they write annotations or candidates. Without a shared dry-run
harness, each connector will invent its own preview shape and safety
rules.

## Scope

- **In:**
  - Shared connector preview result model.
  - Dry-run API that returns proposed records, annotations, candidates,
    command plans, and safety notes.
  - No mutation during dry-run.
  - Output size caps and structured error reporting.
  - Tests proving dry-run does not change DB state.
- **Out:**
  - Actual `gh`/`jira` execution beyond command-plan preview.
  - Browser extension implementation.

## Acceptance Criteria

- [x] Dry-run API returns structured preview results.
- [x] Dry-run results include warnings and permission notes.
- [x] Dry-run never writes records, annotations, or candidates.
- [x] Connectors can reuse the same preview response shape.
- [x] Tests prove DB state is unchanged after dry-run.

## Test Plan

- Unit tests for preview result serialization.
- Integration test for dry-run no-mutation behavior.
- Focused assisted-enrichment API sweep.
