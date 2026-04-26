# HS-5-14 — Runtime guidance copy bundle

- **Project:** holdspeak
- **Phase:** 5
- **Status:** done
- **Depends on:** HS-5-13
- **Unblocks:** copying multi-step runtime setup commands from one browser action
- **Owner:** codex

## Problem

Runtime readiness guidance can show multiple commands for a setup step,
especially missing model guidance where directory creation and model
download are separate snippets. Users had to copy each snippet
individually.

## Scope

- **In:**
  - Add a `command_bundle` field to shared runtime guidance payloads.
  - Render a browser **Copy all setup commands** button when guidance
    has multiple commands.
  - Keep individual per-command copy buttons.
  - Cover bundle shape and page wiring in tests.
- **Out:**
  - Running setup commands automatically.
  - Shell-specific script generation beyond newline-joined commands.

## Acceptance Criteria

- [x] Shared guidance exposes a newline-joined command bundle.
- [x] Missing-model readiness guidance includes the model download command in the bundle.
- [x] `/dictation` renders a copy-all setup button for multi-command guidance.
- [x] Existing individual copy buttons remain.
- [x] Focused and full tests pass.

## Test Plan

- `uv run pytest -q tests/unit/test_dictation_runtime_guidance.py tests/integration/test_web_dictation_readiness_api.py`
- `uv run pytest -q tests/unit/test_dictation_runtime_guidance.py tests/unit/test_doctor_command.py tests/integration/test_web_dictation_readiness_api.py tests/integration/test_web_dictation_blocks_api.py tests/integration/test_web_dictation_settings_api.py tests/integration/test_web_project_kb_api.py tests/integration/test_web_dry_run_api.py`
- Full regression: `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py`

## Notes

- The copy bundle is a clipboard helper only. It does not execute
  commands.
