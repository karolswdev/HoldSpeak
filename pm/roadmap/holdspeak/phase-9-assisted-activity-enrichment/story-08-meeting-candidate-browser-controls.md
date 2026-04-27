# HS-9-08 - Meeting candidate browser controls

- **Project:** holdspeak
- **Phase:** 9
- **Status:** done
- **Depends on:** HS-9-07
- **Unblocks:** non-CLI testing of local meeting candidates
- **Owner:** unassigned

## Problem

HS-9-07 exposed meeting candidates through the local API. To make the
feature immediately tangible in normal dogfooding, `/activity` needs
browser controls for the same workflow.

## Scope

- **In:**
  - Meeting Candidates panel on `/activity`.
  - Preview local calendar/Outlook candidates.
  - Save a preview candidate.
  - Refresh saved candidates.
  - Arm, dismiss, and reset candidate status.
  - Clear dismissed candidates.
  - Integration test that the browser surface references the candidate
    preview endpoint.
- **Out:**
  - Automatic recording.
  - Meeting runtime integration.
  - Microsoft Graph or calendar database reads.

## Acceptance Criteria

- [x] `/activity` exposes meeting candidate controls.
- [x] Candidate previews can be loaded from the browser surface.
- [x] Candidate previews can be saved from the browser surface.
- [x] Saved candidates can be armed, dismissed, or reset.
- [x] Dismissed candidates can be cleared.
- [x] Focused web tests pass.

## Test Plan

- `uv run pytest -q tests/integration/test_web_activity_api.py -k "activity_page or meeting_candidate"`
- `uv run pytest -q tests/unit/test_activity_candidates.py tests/integration/test_web_activity_api.py`
- `git diff --check`

## Evidence

- [evidence-story-08.md](./evidence-story-08.md)
