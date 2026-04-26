# HS-5-15 — Runtime docs backend deep links

- **Project:** holdspeak
- **Phase:** 5
- **Status:** done
- **Depends on:** HS-5-14
- **Unblocks:** jumping directly to the relevant runtime setup section from readiness guidance
- **Owner:** codex

## Problem

HS-5-13 added a served runtime setup docs route, but all guidance
linked to the top of that page. When readiness already knows the
backend, the link should land on the matching setup section.

## Scope

- **In:**
  - Add backend anchors to the local runtime setup page.
  - Add a shared helper for backend-specific docs targets.
  - Point MLX guidance at `#mlx`.
  - Point `llama_cpp` guidance at `#llama-cpp`.
  - Keep `auto` guidance pointed at the top-level docs route.
- **Out:**
  - Splitting setup docs into multiple pages.
  - Changing setup commands.

## Acceptance Criteria

- [x] The runtime setup page has stable `mlx` and `llama-cpp` anchors.
- [x] Shared guidance targets backend-specific anchors when the backend is known.
- [x] `auto` guidance continues to target the top-level setup page.
- [x] Readiness payload tests cover the `llama_cpp` anchor.
- [x] Focused and full tests pass.

## Test Plan

- `uv run pytest -q tests/unit/test_dictation_runtime_guidance.py tests/integration/test_web_dictation_readiness_api.py`
- `uv run pytest -q tests/unit/test_dictation_runtime_guidance.py tests/unit/test_doctor_command.py tests/integration/test_web_dictation_readiness_api.py tests/integration/test_web_dictation_blocks_api.py tests/integration/test_web_dictation_settings_api.py tests/integration/test_web_project_kb_api.py tests/integration/test_web_dry_run_api.py`
- Full regression: `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py`

## Notes

- This is a navigation improvement only. Runtime behavior and commands
  are unchanged.
