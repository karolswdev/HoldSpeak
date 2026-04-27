# HS-6-04 - Artifact/action detail linking

- **Project:** holdspeak
- **Phase:** 6
- **Status:** done
- **Depends on:** HS-6-03
- **Unblocks:** verifying action items against meeting context
- **Owner:** unassigned

## Problem

Action items and artifacts need clear links back to the source meeting
and surrounding context. Without provenance, users cannot confidently
review generated work.

HS-6-04 links action items and project artifacts back to their source
meeting and loads meeting artifacts in the selected meeting detail view.

## Scope

- **In:**
  - Detail links between action items, artifacts, and meetings.
  - Browser affordances for opening source context.
  - Tests for link/API behavior.
- **Out:**
  - Semantic transcript search.
  - Cross-meeting action deduplication.

## Acceptance Criteria

- [x] Action items expose useful source context from browser views.
- [x] Artifacts and action items cross-link where the data model supports it.
- [x] Focused and full tests pass.

## Test Plan

- `uv run pytest -q tests/integration/test_web_server.py -k "HistoryUiSmoke or GlobalActionItems or meeting_artifacts"`
- `uv run pytest -q tests/integration/test_web_server.py tests/integration/test_intel_streaming.py`
- `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py`

## Evidence

- [evidence-story-04.md](./evidence-story-04.md)
