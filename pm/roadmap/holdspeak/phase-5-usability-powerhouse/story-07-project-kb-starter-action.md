# HS-5-07 — Project KB starter action

- **Project:** holdspeak
- **Phase:** 5
- **Status:** done
- **Depends on:** HS-5-06
- **Unblocks:** fixing a missing Project KB readiness warning without hand-authoring YAML
- **Owner:** codex

## Problem

The readiness panel can flag a missing Project KB, but the user still
has to know which keys are useful and save a valid
`.holdspeak/project.yaml` by hand or through an empty editor. This is
setup friction in the exact place the cockpit is supposed to remove it.

## Scope

- **In:**
  - Add a starter Project KB endpoint that writes canonical
    `kb: {...}` YAML through the existing validated writer.
  - Include useful starter keys for block placeholders:
    `stack`, `task_focus`, and `constraints`.
  - Refuse to overwrite an existing Project KB file.
  - Add a Project KB editor button for the starter file.
  - Add a readiness action for missing Project KB warnings.
- **Out:**
  - User-authored KB templates.
  - Server-side project registry or setup wizard.
  - Guessing project stack from source files.

## Acceptance Criteria

- [x] A user can create a starter Project KB from the browser.
- [x] The endpoint writes canonical `kb` YAML and validates through the existing Project KB writer.
- [x] Existing Project KB files are not overwritten by the starter action.
- [x] Project-root override is honored.
- [x] Readiness missing-KB warnings expose a one-click starter action.
- [x] Focused and full tests pass.

## Test Plan

- `uv run pytest -q tests/integration/test_web_project_kb_api.py tests/integration/test_web_dictation_readiness_api.py tests/integration/test_web_dictation_blocks_api.py tests/integration/test_web_dry_run_api.py`
- Full regression: `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py`

## Notes

- Starter values are intentionally `null`; the user gets valid
  placeholders immediately and can fill values from the same browser
  editor.
