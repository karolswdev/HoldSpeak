# HS-8-02 - Activity ledger persistence

- **Project:** holdspeak
- **Phase:** 8
- **Status:** done
- **Depends on:** HS-8-01
- **Unblocks:** importing browser activity records
- **Owner:** unassigned

## Problem

HoldSpeak needs a normalized local store for activity records before
browser history readers can import data. The store must avoid raw-history
sprawl and support deduplication, retention, and deletion.

HS-8-01 confirmed that the ledger should store normalized datetimes while
preserving a source-specific raw timestamp field for audit/debugging.
Safari and Firefox readers also need per-source/profile checkpoints.

## Scope

- **In:**
  - Local DB tables for activity records and source import checkpoints.
  - Fields for browser/source, URL, title, domain, entity type/id, first
    seen, last seen, raw source timestamp, visit count, and optional
    project link.
  - Deduplication by normalized URL/entity.
  - Unit tests for persistence and retention primitives.
- **Out:**
  - UI.
  - Browser-specific readers.
  - Network enrichment.

## Acceptance Criteria

- [x] Activity records persist locally.
- [x] Duplicate visits merge into one normalized record.
- [x] Import checkpoints are stored per source/profile.
- [x] Raw source timestamps can be retained without becoming the primary user-facing time.
- [x] Deletion/retention primitives exist.
- [x] Focused and full tests pass.

## Test Plan

- `uv run pytest -q tests/unit/test_db.py`
- `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py`

## Evidence

- [evidence-story-02.md](./evidence-story-02.md)
