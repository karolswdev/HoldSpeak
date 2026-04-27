# HS-7-03 - Browser handoff export action

- **Project:** holdspeak
- **Phase:** 7
- **Status:** done
- **Depends on:** HS-7-02
- **Unblocks:** one-click local handoff from history
- **Owner:** unassigned

## Problem

After reviewing meeting actions/artifacts in `/history`, the user should
be able to download a local handoff file without switching to another
surface.

## Scope

- **In:**
  - Browser export action from selected meeting detail.
  - Markdown and JSON format options.
  - Clear local-only behavior.
  - Tests for UI wiring.
- **Out:**
  - Cloud upload or external task creation.

## Acceptance Criteria

- [x] Selected meeting detail exposes handoff export controls.
- [x] Export downloads the API output.
- [x] Controls remain local-only and do not auto-publish.
- [x] Focused and full tests pass.

## Test Plan

- `uv run pytest -q tests/integration/test_web_server.py -k "HistoryUiSmoke or meeting_export_endpoint"`
- `uv run pytest -q tests/integration/test_web_server.py tests/unit/test_meeting_exports.py`
- `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py`

## Evidence

- [evidence-story-03.md](./evidence-story-03.md)
