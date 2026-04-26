# HS-5-09 — Model/runtime install guidance

- **Project:** holdspeak
- **Phase:** 5
- **Status:** done
- **Depends on:** HS-5-08
- **Unblocks:** fixing missing runtime dependency and model-file readiness warnings without source-diving
- **Owner:** codex

## Problem

Readiness can already detect `runtime_unavailable` and
`runtime_model_missing`, but those warnings only point users toward the
Runtime section. A user still has to know which optional extra maps to
which backend, where the default models belong, and when macOS arm64
needs the Metal `llama-cpp-python` rebuild command.

## Scope

- **In:**
  - Add structured install guidance to `runtime_unavailable` warnings.
  - Add structured model-path guidance to `runtime_model_missing`
    warnings, including the exact missing path.
  - Render guidance in `/dictation` readiness warnings and the Runtime
    panel.
  - Provide copyable command snippets for useful local install/download
    steps.
- **Out:**
  - Automatic package installs.
  - Automatic network downloads.
  - Runtime mutation from the readiness endpoint.

## Acceptance Criteria

- [x] `runtime_unavailable` readiness warnings include backend-specific install guidance.
- [x] `runtime_model_missing` warnings include the exact missing path and suggested next step.
- [x] `/dictation` renders the guidance in Readiness and Runtime, with copyable commands.
- [x] The guidance does not trigger automatic installs or downloads.
- [x] Focused and full tests pass.

## Test Plan

- `uv run pytest -q tests/integration/test_web_dictation_readiness_api.py tests/integration/test_web_dictation_settings_api.py tests/integration/test_web_project_kb_api.py tests/integration/test_web_dictation_blocks_api.py tests/integration/test_web_dry_run_api.py`
- Full regression: `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py`

## Notes

- This keeps readiness read-only. It only describes commands the user
  may choose to copy and run.
