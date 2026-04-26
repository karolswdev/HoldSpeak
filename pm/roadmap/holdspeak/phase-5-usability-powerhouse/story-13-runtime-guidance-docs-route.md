# HS-5-13 — Runtime guidance docs route

- **Project:** holdspeak
- **Phase:** 5
- **Status:** done
- **Depends on:** HS-5-12
- **Unblocks:** opening useful runtime setup docs from browser readiness guidance
- **Owner:** codex

## Problem

Runtime setup guidance in `/dictation` included a docs link, but that
link targeted a repo-relative README anchor. From the browser cockpit,
that is weaker than a local route served by the web runtime itself.

## Scope

- **In:**
  - Add a local `/docs/dictation-runtime` route.
  - Serve a compact runtime setup page for the MLX and `llama_cpp`
    dictation backends.
  - Point shared runtime guidance links at the local route.
  - Cover the route and payload link target in tests.
- **Out:**
  - Full documentation site generator.
  - Automatic setup actions.
  - Changing runtime install/model commands.

## Acceptance Criteria

- [x] Browser runtime guidance links to a served local route.
- [x] The docs route includes MLX and `llama_cpp` setup commands.
- [x] The route preserves the macOS arm64 Metal `llama_cpp` guidance.
- [x] Readiness payload tests cover the new link target.
- [x] Focused and full tests pass.

## Test Plan

- `uv run pytest -q tests/unit/test_dictation_runtime_guidance.py tests/integration/test_web_dictation_readiness_api.py`
- `uv run pytest -q tests/unit/test_dictation_runtime_guidance.py tests/unit/test_doctor_command.py tests/integration/test_web_dictation_readiness_api.py tests/integration/test_web_dictation_blocks_api.py tests/integration/test_web_dictation_settings_api.py tests/integration/test_web_project_kb_api.py tests/integration/test_web_dry_run_api.py`
- Full regression: `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py`

## Notes

- This keeps guidance local and read-only. The page documents commands;
  it does not execute them.
