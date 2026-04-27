# HS-8-09 - DoD sweep + phase exit

- **Project:** holdspeak
- **Phase:** 8
- **Status:** backlog
- **Depends on:** HS-8-01 through HS-8-08
- **Unblocks:** Phase 8 closure
- **Owner:** unassigned

## Problem

Close Phase 8 with evidence, traceability, regression results, and a
summary of shipped local activity intelligence workflows.

## Scope

- **In:**
  - Phase evidence bundle.
  - Focused local activity intelligence test sweep.
  - Full non-Metal regression.
  - Roadmap status updates.
- **Out:**
  - New product code.

## Acceptance Criteria

- [ ] Phase evidence bundle exists.
- [ ] Focused activity-intelligence sweep passes.
- [ ] Full regression passes.
- [ ] Phase 8 status is updated.

## Test Plan

- Focused activity-intelligence sweep:
  `uv run pytest -q tests/unit/test_activity_context.py tests/unit/test_activity_entities.py tests/unit/test_activity_history.py tests/unit/test_activity_mapping.py tests/unit/test_db.py tests/integration/test_web_activity_api.py`
- Full non-Metal regression:
  `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py`
- Whitespace check:
  `git diff --check`
