# HS-8-06 - Privacy controls and retention

- **Project:** holdspeak
- **Phase:** 8
- **Status:** done
- **Depends on:** HS-8-03, HS-8-05
- **Unblocks:** trustworthy local activity intelligence
- **Owner:** unassigned

## Problem

Browser history ingestion is sensitive even for a personal local tool.
The feature should ship enabled by default, but users still need explicit
visibility and control over whether it is running, which domains are
included/excluded, how long records are retained, and how to delete
imported data.

## Scope

- **In:**
  - Default-enabled setting with visible enabled/paused state.
  - First-run/browser-surface copy that names the active local sources.
  - Domain allowlist/denylist.
  - Retention controls.
  - Delete imported activity controls.
  - Tests for privacy settings and deletion.
- **Out:**
  - Hidden background collection.
  - Remote telemetry.

## Acceptance Criteria

- [x] Activity ingestion is enabled by default when local sources are readable.
- [x] UI/API visibly reports that ingestion is enabled.
- [x] User can pause ingestion.
- [x] User can exclude domains.
- [x] User can delete imported activity.
- [x] Focused and full tests pass.

## Test Plan

- `uv run pytest -q tests/unit/test_activity_context.py tests/unit/test_activity_entities.py tests/unit/test_activity_history.py tests/unit/test_db.py tests/integration/test_web_activity_api.py`
- `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py`

## Evidence

- [evidence-story-06.md](./evidence-story-06.md)
