# HS-6-02 - Action item review controls

- **Project:** holdspeak
- **Phase:** 6
- **Status:** backlog
- **Depends on:** HS-6-01
- **Unblocks:** marking action items reviewed from the browser
- **Owner:** unassigned

## Problem

Action items are useful only if the user can review and trust them.
The browser should make review state visible and editable without
database/source inspection.

HS-6-01 confirmed that review-state persistence and API mutation paths
already exist for global/history action items. This story should focus on
browser ergonomics: making the existing review actions easier to reach
from the action follow-through surfaces and keeping source provenance
visible while reviewing.

## Scope

- **In:**
  - Browser controls for action item review state where the history UI
    currently only shows labels or low-context buttons.
  - Reuse existing review mutation APIs unless a specific gap is found.
  - Keep source timestamp/meeting context visible during review.
  - Tests for persistence/API/UI wiring.
- **Out:**
  - External task sync.
  - Assignment workflows beyond local review state.

## Acceptance Criteria

- [ ] A user can mark an action item reviewed from the relevant browser follow-through surface.
- [ ] Review state persists.
- [ ] Review state is visible in the relevant history/detail surface alongside source provenance.
- [ ] Focused and full tests pass.

## Test Plan

- Focused history UI/API tests around action item review state.
- Full regression: `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py`
