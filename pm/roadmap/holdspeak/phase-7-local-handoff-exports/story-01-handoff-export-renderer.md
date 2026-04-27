# HS-7-01 - Handoff export renderer

- **Project:** holdspeak
- **Phase:** 7
- **Status:** done
- **Depends on:** HS-6-05
- **Unblocks:** saved-meeting export API and browser export actions
- **Owner:** unassigned

## Problem

The shared meeting export renderer includes transcript, summary, topics,
and basic action items, but Phase 6 made richer follow-through metadata
available: action review state, source timestamps, and synthesized
artifacts. Handoff exports should preserve that context before any UI/API
export action is added.

## Scope

- **In:**
  - Add action item review/provenance details to Markdown exports.
  - Add optional synthesized artifacts to Markdown exports.
  - Add optional synthesized artifacts to JSON exports without breaking
    existing meeting-state payload shape.
  - Unit tests for handoff export content.
- **Out:**
  - New web endpoint.
  - Browser export buttons.
  - External task-system publishing.

## Acceptance Criteria

- [x] Markdown action items include review state and source timestamp when present.
- [x] Markdown exports can include synthesized artifact titles/body/source counts.
- [x] JSON exports can include artifact payloads.
- [x] Existing export callers remain compatible.
- [x] Focused tests pass.

## Test Plan

- `uv run pytest -q tests/unit/test_meeting_exports.py`
- `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py`

## Evidence

- [evidence-story-01.md](./evidence-story-01.md)
