# HS-172-06 — The suggested source

- **Project:** holdspeak
- **Phase:** 172
- **Status:** in-progress
- **Depends on:** HS-172-02
- **Unblocks:** HS-172-07
- **Owner:** unassigned

## Problem

When a meeting discusses a GitHub repo or Jira issue, that mention is
buried in the transcript. The arc says: "a meeting's mention of a
repo/issue becomes a SUGGESTED source row in the Room (offered, never
applied)." Today the Room's sources are manually configured. The
ProjectDetectorPlugin (plugins/project_detector.py:52) exists but does
not produce source suggestions for the Room.

## Scope

- In:
  - After intel completes for a Room-linked meeting, if the transcript
    or plugin artifacts mention a recognizable repo (owner/repo
    pattern) or issue (e.g., #123, PROJ-456), produce a SUGGESTED
    source entry on the Room.
  - The suggested source is offered (a row with an Accept / Dismiss
    verb), never auto-applied.
  - Accept creates a new Watch source on the Room using the existing
    Door's add-source flow (project_door_service.py if it exists, or
    the project setup machinery).
  - Dismiss hides the suggestion (persisted as dismissed so it does
    not recur).
  - The face for the suggested source row follows the HS-172-01
    artboard.
- Out:
  - Automatic source application (Accept is the chokepoint).
  - Detecting mentions of tools beyond GitHub repos and Jira issues.
  - Running a new intelligence plugin; reuse
    ProjectDetectorPlugin or the existing transcript scan.

## Acceptance criteria

- [ ] A completed intel job whose transcript mentions a GitHub repo
      (owner/repo) produces a SUGGESTED source row on the Room;
      verified by a unit test with a seeded transcript.
- [ ] A completed intel job whose transcript mentions a Jira issue
      (PROJ-123) produces a SUGGESTED source row on the Room.
- [ ] Accept creates a Watch source using the existing add-source
      flow; Dismiss hides the suggestion.
- [ ] A dismissed suggestion does not recur on subsequent intel jobs
      for the same meeting.
- [ ] No auto-application of sources (Article V).

## Test plan

- Unit: `HOME=$(mktemp -d) uv run pytest -q tests/ -k suggested_source`
  - Transcript with "owner/repo" produces a source suggestion.
  - Transcript with "PROJ-123" produces a source suggestion.
  - Accept creates a Watch source.
  - Dismiss persists and prevents recurrence.
  - Transcript with no recognizable mentions produces no suggestion.
- Integration: n/a.
- Manual: the owner sees a SUGGESTED source in the Room after a test
  meeting that mentions a repo.

## Notes / open questions

- The regex for repo detection: GitHub owner/repo patterns are
  relatively unambiguous. Jira issue keys (PROJ-123) require knowing
  which Jira projects are connected. The connected Jira sites
  (watch_sources.py's JiraWatchSource) provide the project keys.
