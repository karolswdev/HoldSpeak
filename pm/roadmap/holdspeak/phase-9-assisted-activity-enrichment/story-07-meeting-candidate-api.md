# HS-9-07 - Meeting candidate API surface

- **Project:** holdspeak
- **Phase:** 9
- **Status:** done
- **Depends on:** HS-9-02
- **Unblocks:** immediate local testing of calendar/Outlook candidates
- **Owner:** unassigned

## Problem

HS-9-02 made meeting candidates real in the DB, but the user should not
need to run Python to prove that they work. The first tangible product
surface should be a local web API that can preview candidates from
existing activity, persist them, arm/dismiss them, and clear them.

## Scope

- **In:**
  - Preview meeting candidates from local activity records.
  - List stored meeting candidates.
  - Create a candidate from preview data.
  - Update candidate status.
  - Delete candidates by status or connector.
  - Integration test for the end-to-end API flow.
- **Out:**
  - Browser UI panel.
  - Automatic recording.
  - Microsoft Graph, calendar DB reads, or email scraping.

## Acceptance Criteria

- [x] `GET /api/activity/meeting-candidates/preview` returns candidate previews.
- [x] `POST /api/activity/meeting-candidates` persists a candidate.
- [x] `GET /api/activity/meeting-candidates` lists stored candidates.
- [x] `PUT /api/activity/meeting-candidates/{id}/status` updates status.
- [x] `DELETE /api/activity/meeting-candidates` clears candidates.
- [x] Integration tests cover preview, create, list, status update, and delete.

## Test Plan

- `uv run pytest -q tests/integration/test_web_activity_api.py -k meeting_candidate`
- `uv run pytest -q tests/unit/test_activity_candidates.py tests/integration/test_web_activity_api.py`
- `git diff --check`

## Evidence

- [evidence-story-07.md](./evidence-story-07.md)
