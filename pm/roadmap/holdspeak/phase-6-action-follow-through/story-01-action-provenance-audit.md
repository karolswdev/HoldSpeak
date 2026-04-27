# HS-6-01 - Action item provenance audit

- **Project:** holdspeak
- **Phase:** 6
- **Status:** done
- **Depends on:** HS-5-16
- **Unblocks:** safe action follow-through UI/API work
- **Owner:** unassigned

## Problem

HoldSpeak can synthesize meeting action items and artifacts, but the
current web experience needed a precise audit before adding review
controls. We needed to know what the data model already exposed, what
the history/detail UI already rendered, which API contracts existed, and
where tests were missing.

The audit found that action items already persisted a `source_timestamp`,
but cross-meeting/project summary APIs and the history action-item
surfaces did not expose it. HS-6-01 shipped that provenance field through
the relevant summary APIs and rendered it in the browser.

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

- [x] Existing action item/artifact API surfaces are mapped with file references.
- [x] Existing history/detail UI surfaces are mapped with file references.
- [x] Current behavior has focused regression coverage where practical.
- [x] Gaps are listed in the story evidence.
- [x] HS-6-02 scope is confirmed or adjusted based on audit findings.

## Test Plan

- `uv run pytest -q tests/integration/test_web_server.py -k "HistoryUiSmoke or GlobalActionItems"`
- `uv run pytest -q tests/integration/test_web_server.py tests/integration/test_intel_streaming.py`
- `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py`

## Evidence

- [evidence-story-01.md](./evidence-story-01.md)

## Notes

- Treat this as an implementation-enabling audit, not a paper exercise.
  If a small missing regression test is obvious, add it in this story.
