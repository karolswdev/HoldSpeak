# HS-6-01 - Action item provenance audit

- **Project:** holdspeak
- **Phase:** 6
- **Status:** ready
- **Depends on:** HS-5-16
- **Unblocks:** safe action follow-through UI/API work
- **Owner:** unassigned

## Problem

HoldSpeak can synthesize meeting action items and artifacts, but the
current web experience needs a precise audit before adding review
controls. We need to know what the data model already exposes, what the
history/detail UI already renders, which API contracts exist, and where
tests are missing.

## Scope

- **In:**
  - Inspect action item and artifact persistence/API surfaces.
  - Inspect history/detail UI rendering for action item provenance and
    review state.
  - Add or update tests that pin current action item API/UI contracts.
  - Produce a short audit summary that selects the smallest next
    implementation story.
- **Out:**
  - New review-state mutation behavior.
  - External task sync.
  - Large UI redesign.

## Acceptance Criteria

- [ ] Existing action item/artifact API surfaces are mapped with file references.
- [ ] Existing history/detail UI surfaces are mapped with file references.
- [ ] Current behavior has focused regression coverage where practical.
- [ ] Gaps are listed in the story evidence.
- [ ] HS-6-02 scope is confirmed or adjusted based on audit findings.

## Test Plan

- Focused tests selected during audit, likely around `tests/integration/test_web_server.py`, history UI smoke coverage, and persistence/action item APIs.
- Full regression: `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py`

## Notes

- Treat this as an implementation-enabling audit, not a paper exercise.
  If a small missing regression test is obvious, add it in this story.
