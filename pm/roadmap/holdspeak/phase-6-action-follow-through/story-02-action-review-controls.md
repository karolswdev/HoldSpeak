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

## Scope

- **In:**
  - Browser controls for action item review state.
  - API mutation path if one does not already exist.
  - Tests for persistence/API/UI wiring.
- **Out:**
  - External task sync.
  - Assignment workflows beyond local review state.

## Acceptance Criteria

- [ ] A user can mark an action item reviewed from the browser.
- [ ] Review state persists.
- [ ] Review state is visible in the relevant history/detail surface.
- [ ] Focused and full tests pass.

## Test Plan

- To be finalized after HS-6-01.
