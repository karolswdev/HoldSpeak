# HS-5-12 — Runtime guidance shared source

- **Project:** holdspeak
- **Phase:** 5
- **Status:** done
- **Depends on:** HS-5-11
- **Unblocks:** keeping browser readiness and doctor setup guidance from drifting
- **Owner:** codex

## Problem

HS-5-09 added browser runtime guidance and HS-5-11 added matching
doctor guidance, but the command construction lived in two places.
That duplication makes it easy for future changes to update one setup
surface and forget the other.

## Scope

- **In:**
  - Move dictation runtime install/model guidance into a shared helper.
  - Reuse that helper from `/api/dictation/readiness`.
  - Reuse that helper from `holdspeak doctor`.
  - Add focused unit tests for the shared command construction.
- **Out:**
  - Changing the user-facing behavior from HS-5-09 or HS-5-11.
  - Automatically running install or download commands.

## Acceptance Criteria

- [x] Browser readiness and doctor use one implementation source for runtime guidance.
- [x] The macOS arm64 `llama_cpp` Metal command remains covered.
- [x] Missing-model guidance still includes `huggingface-cli` commands and target paths.
- [x] Existing readiness and doctor behavior remains covered.
- [x] Focused and full tests pass.

## Test Plan

- `uv run pytest -q tests/unit/test_dictation_runtime_guidance.py tests/unit/test_doctor_command.py tests/integration/test_web_dictation_readiness_api.py`
- `uv run pytest -q tests/unit/test_dictation_runtime_guidance.py tests/unit/test_doctor_command.py tests/integration/test_dictation_cold_start_cap.py tests/integration/test_web_dictation_readiness_api.py tests/integration/test_web_dictation_blocks_api.py tests/integration/test_web_dictation_settings_api.py tests/integration/test_web_project_kb_api.py tests/integration/test_web_dry_run_api.py`
- Full regression: `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py`

## Notes

- This is a maintainability story only. It intentionally preserves the
  read-only behavior of readiness and doctor.
