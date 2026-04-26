# HS-5-08 — Runtime readiness action

- **Project:** holdspeak
- **Phase:** 5
- **Status:** done
- **Depends on:** HS-5-07
- **Unblocks:** fixing disabled dictation pipeline readiness warnings from the cockpit
- **Owner:** codex

## Problem

Readiness can detect that the dictation pipeline is disabled, but the
user still has to open Runtime, understand which checkbox matters, and
save. Blocks and Project KB now have one-click readiness fixes; runtime
should have the same setup-loop ergonomics while still using the
normal settings save path.

## Scope

- **In:**
  - Add an `enable_pipeline` runtime action to the
    `pipeline_disabled` readiness warning.
  - Add a browser readiness button that switches to Runtime, loads the
    current settings into the form, enables the pipeline, and saves.
  - Reuse `PUT /api/settings`; no separate runtime mutation endpoint.
  - Verify partial settings saves preserve existing runtime config.
- **Out:**
  - Installing missing runtime dependencies.
  - Downloading model files.
  - Auto-enabling warm model loading.

## Acceptance Criteria

- [x] Readiness exposes a concrete enable action for disabled pipeline warnings.
- [x] The browser renders an Enable pipeline action from readiness.
- [x] The action previews the current runtime settings in the Runtime panel before saving through the existing settings path.
- [x] Enabling the pipeline preserves the configured backend/model fields.
- [x] Focused and full tests pass.

## Test Plan

- `uv run pytest -q tests/integration/test_web_dictation_readiness_api.py tests/integration/test_web_dictation_settings_api.py tests/integration/test_web_project_kb_api.py tests/integration/test_web_dictation_blocks_api.py tests/integration/test_web_dry_run_api.py`
- Full regression: `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py`

## Notes

- Missing runtime dependency and model-file warnings still route users
  to Runtime; automatic installation/download is deliberately out of
  scope.
