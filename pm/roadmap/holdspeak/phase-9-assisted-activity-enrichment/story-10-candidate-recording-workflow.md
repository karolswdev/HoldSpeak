# HS-9-10 - Meeting candidate recording workflow

- **Project:** holdspeak
- **Phase:** 9
- **Status:** done
- **Depends on:** HS-9-09
- **Unblocks:** turning a saved candidate into a visible recording action
- **Owner:** unassigned

## Problem

The browser can now save and arm meeting candidates, but `armed` is only
stored state. Users need an explicit, visible path from candidate to
meeting recording without automatic join or hidden recording.

## Scope

- **In:**
  - Candidate detail action in `/activity` or the runtime dashboard.
  - Manual "start meeting from candidate" action.
  - Candidate title/URL carried into meeting state where supported.
  - Candidate status transition to `started` after manual start.
  - Audit metadata linking candidate ID to the started meeting.
  - Tests for status transitions and manual-start API behavior.
- **Out:**
  - Automatic recording.
  - Automatic meeting join.
  - Calendar reminders/notifications.
  - Cloud calendar integration.

## Acceptance Criteria

- [x] User can manually start recording from a candidate.
- [x] Candidate status becomes `started` only after visible user action.
- [x] Started meeting carries candidate title/context when available.
- [x] Candidate-to-meeting linkage is persisted or inspectable.
- [x] No automatic recording is introduced.

## Test Plan

- API test for manual start from candidate.
- Unit test for candidate status transition rules.
- Focused runtime/web activity integration test.
