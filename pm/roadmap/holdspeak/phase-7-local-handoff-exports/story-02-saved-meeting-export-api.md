# HS-7-02 - Saved meeting export API

- **Project:** holdspeak
- **Phase:** 7
- **Status:** done
- **Depends on:** HS-7-01
- **Unblocks:** browser handoff export actions
- **Owner:** unassigned

## Problem

The browser can inspect saved meetings and artifacts, but there is no
saved-meeting export API that returns the shared handoff renderer output.

## Scope

- **In:**
  - Saved meeting export endpoint for Markdown and JSON.
  - Include synthesized artifacts where available.
  - Tests for status codes, content type, and payload content.
- **Out:**
  - Writing files to arbitrary user paths from the browser.
  - External publishing.

## Acceptance Criteria

- [x] A saved meeting can be exported through a local API.
- [x] Markdown and JSON outputs use the shared handoff renderer.
- [x] Invalid formats fail clearly.
- [x] Focused and full tests pass.

## Test Plan

- `uv run pytest -q tests/integration/test_web_server.py -k "meeting_export_endpoint or meeting_artifacts"`
- `uv run pytest -q tests/integration/test_web_server.py tests/unit/test_meeting_exports.py`
- `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py`

## Evidence

- [evidence-story-02.md](./evidence-story-02.md)
