# HS-9-09 - Meeting candidate dedupe and time hints

- **Project:** holdspeak
- **Phase:** 9
- **Status:** backlog
- **Depends on:** HS-9-08
- **Unblocks:** usable meeting-candidate lists instead of noisy repeated previews
- **Owner:** unassigned

## Problem

The current meeting-candidate flow is testable, but it is still rough:
the same calendar URL can be saved multiple times, and previews do not
surface even simple start/end hints from titles or URLs. This makes the
candidate panel useful as proof, but not yet pleasant for daily use.

## Scope

- **In:**
  - Deterministic duplicate key for meeting candidates.
  - Prevent saving duplicate candidates from the same source record and
    connector.
  - Merge repeated preview/save attempts into the existing candidate.
  - Extract simple time hints from local title/URL metadata when present.
  - Show candidate source and confidence clearly in API and UI payloads.
  - Tests for duplicate prevention, merge behavior, and time hint parsing.
- **Out:**
  - Calendar database reads.
  - Microsoft Graph.
  - Natural-language scheduling intelligence beyond deterministic local
    parsing.

## Acceptance Criteria

- [ ] Saving the same preview twice does not create duplicate rows.
- [ ] Candidate list remains stable after repeated preview/save cycles.
- [ ] Basic time hints are extracted when visible in local metadata.
- [ ] Time parsing failures are silent and do not block candidate creation.
- [ ] Focused DB/API/UI tests pass.

## Test Plan

- Unit tests for candidate dedupe key and merge behavior.
- Unit tests for simple time-hint extraction.
- Integration test for repeated save via `/api/activity/meeting-candidates`.
- Focused activity API sweep.
