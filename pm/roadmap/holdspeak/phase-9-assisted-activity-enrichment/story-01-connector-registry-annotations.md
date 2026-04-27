# HS-9-01 - Connector registry and annotation persistence

- **Project:** holdspeak
- **Phase:** 9
- **Status:** done
- **Depends on:** HS-8-08
- **Unblocks:** Calendar, extension, and CLI enrichment connectors
- **Owner:** unassigned

## Problem

Phase 8 designed assisted activity enrichment, but implementation needs a
local substrate before any connector can safely ship. Connectors need
visible persisted state, and enrichment output needs a local annotation
table that can be inspected and deleted without touching external
systems.

## Scope

- **In:**
  - DB schema for activity enrichment connector state.
  - DB schema for local activity annotations.
  - Dataclasses for connector state and annotations.
  - DB CRUD/list helpers for connector state.
  - DB create/list/delete helpers for annotations.
  - Unit tests.
- **Out:**
  - Calendar candidate extraction.
  - Firefox extension endpoint.
  - Running `gh` or `jira`.
  - Web UI controls.
  - External network calls or writes.

## Acceptance Criteria

- [x] Connector state can be created, updated, listed, and marked with latest run results.
- [x] Connector settings are stored as local JSON.
- [x] Activity annotations can attach to activity records.
- [x] Annotation confidence is bounded.
- [x] Annotations can be listed and deleted by connector or record.
- [x] Missing activity-record references are rejected.
- [x] Focused DB tests pass.

## Test Plan

- `uv run pytest -q tests/unit/test_db.py -k "activity_enrichment or activity_annotations"`
- `git diff --check`

## Evidence

- [evidence-story-01.md](./evidence-story-01.md)
