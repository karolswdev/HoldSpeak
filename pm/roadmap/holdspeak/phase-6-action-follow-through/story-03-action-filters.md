# HS-6-03 - Action item filters and open-work view

- **Project:** holdspeak
- **Phase:** 6
- **Status:** done
- **Depends on:** HS-6-02
- **Unblocks:** quickly finding outstanding meeting work
- **Owner:** unassigned

## Problem

As meetings accumulate, action items need a focused open-work view or
filters. Otherwise useful extracted tasks disappear into history.

HS-6-03 makes the Actions tab default to pending items that still need
review, and adds explicit status/review filters plus an Open Work reset.

## Scope

- **In:**
  - Filters for open/unreviewed/completed action items.
  - Browser view or panel that makes outstanding work scan-friendly.
  - Tests for API and UI wiring.
- **Out:**
  - External task sync.
  - Multi-user dashboards.

## Acceptance Criteria

- [x] A user can filter action items by useful follow-through states.
- [x] Open/unreviewed work is visible without opening every meeting.
- [x] Focused and full tests pass.

## Test Plan

- `uv run pytest -q tests/integration/test_web_server.py -k "HistoryUiSmoke or GlobalActionItems"`
- `uv run pytest -q tests/integration/test_web_server.py tests/integration/test_intel_streaming.py`
- `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py`

## Evidence

- [evidence-story-03.md](./evidence-story-03.md)
