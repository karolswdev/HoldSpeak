# HS-9-02 - Calendar and Outlook meeting candidates

- **Project:** holdspeak
- **Phase:** 9
- **Status:** done
- **Depends on:** HS-9-01
- **Unblocks:** visible meeting-candidate scheduling from local activity
- **Owner:** unassigned

## Problem

The local activity ledger can see calendar and meeting URLs, but it does
not yet turn those into actionable meeting candidates. HoldSpeak should
surface likely upcoming or active meetings from local metadata and let
the user manually arm or start recording.

## Scope

- **In:**
  - Meeting-candidate persistence.
  - Outlook/Google Calendar candidate extraction from existing activity records.
  - Preview before persistence.
  - Manual candidate status updates.
- **Out:**
  - Microsoft Graph.
  - Email scraping.
  - Automatic meeting join.
  - Automatic recording without visible user action.

## Acceptance Criteria

- [x] Candidate schema exists.
- [x] Calendar/Outlook records can be previewed as candidates.
- [x] Candidates can be stored and dismissed.
- [x] No network calls are introduced.

## Test Plan

- `uv run pytest -q tests/unit/test_activity_candidates.py tests/unit/test_db.py -k "activity_meeting_candidates or activity_candidates"`
- `uv run pytest -q tests/unit/test_activity_candidates.py tests/unit/test_db.py`
- `git diff --check`

## Evidence

- [evidence-story-02.md](./evidence-story-02.md)
