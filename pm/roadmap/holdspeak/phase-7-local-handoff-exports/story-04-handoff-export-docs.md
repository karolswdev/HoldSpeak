# HS-7-04 - Handoff export docs

- **Project:** holdspeak
- **Phase:** 7
- **Status:** done
- **Depends on:** HS-7-03
- **Unblocks:** discoverable local export workflow
- **Owner:** unassigned

## Problem

Handoff exports need brief public documentation so users understand what
is included, where the workflow lives, and that it does not publish to
external systems.

## Scope

- **In:**
  - README and/or Meeting Mode Guide updates.
  - Mention exported action provenance, review state, and artifacts.
  - Clarify local-only/no external sync behavior.
- **Out:**
  - Long-form tutorial.

## Acceptance Criteria

- [x] Public docs describe the handoff export workflow.
- [x] Docs state that exports are local files/downloads only.
- [x] Focused docs/UI tests pass where relevant.

## Test Plan

- `uv run pytest -q tests/integration/test_web_server.py -k "HistoryUiSmoke or meeting_export_endpoint"`
- `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py`

## Evidence

- [evidence-story-04.md](./evidence-story-04.md)
