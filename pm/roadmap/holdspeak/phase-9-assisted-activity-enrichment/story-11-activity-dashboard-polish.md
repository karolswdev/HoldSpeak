# HS-9-11 - Activity dashboard polish

- **Project:** holdspeak
- **Phase:** 9
- **Status:** done
- **Depends on:** HS-9-08
- **Unblocks:** comfortable dogfooding of local activity and enrichment
- **Owner:** unassigned

## Problem

`/activity` is functional but utilitarian. As more controls arrive, rough
states become costly: empty panels do not explain what action is useful,
preview vs saved candidates can blur together, and repeated action
feedback is minimal.

## Scope

- **In:**
  - Clear empty states for activity records, rules, candidates, and
    connectors.
  - Distinct preview and saved-candidate affordances.
  - Loading/disabled button states for long actions.
  - Inline error and success messages tied to the panel that generated
    them.
  - Candidate status filtering.
  - UI text pass for local-only/privacy boundaries.
  - Browser smoke test for `/activity` rendering.
- **Out:**
  - Visual redesign.
  - New connector functionality.
  - Notifications.

## Acceptance Criteria

- [x] Empty states tell the user what to do next.
- [x] Preview candidates and saved candidates are visually distinct.
- [x] Buttons do not allow repeated accidental submits while actions run.
- [x] Errors surface near the relevant panel.
- [x] Candidate status can be filtered or scanned quickly.
- [x] Focused web tests pass.

## Test Plan

- Integration test for `/activity` static surface.
- API-backed smoke test for candidate panel operations.
- Manual browser pass at desktop and narrow viewport widths.
