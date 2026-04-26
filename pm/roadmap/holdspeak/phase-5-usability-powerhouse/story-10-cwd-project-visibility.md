# HS-5-10 — Current cwd project visibility

- **Project:** holdspeak
- **Phase:** 5
- **Status:** done
- **Depends on:** HS-5-09
- **Unblocks:** knowing which project `/dictation` is editing before setting a manual override
- **Owner:** codex

## Problem

The `/dictation` project-root banner lets users set and recall manual
project roots, but initial page load is quiet when no override is set.
That makes it unclear which cwd-derived project the browser will use
for project blocks, Project KB, readiness, and dry-run.

## Scope

- **In:**
  - Load `/api/dictation/project-context` on `/dictation` startup when
    no manual override is active.
  - Show the detected cwd project name, anchor, and root in the project
    banner.
  - Preserve the existing saved-override behavior.
  - Refresh cwd visibility after clearing or applying an empty override.
- **Out:**
  - Native file picker integration.
  - Server-side project registry.
  - Changing how project detection works.

## Acceptance Criteria

- [x] `/api/dictation/project-context` reports the cwd-detected project without a manual root.
- [x] `/dictation` shows the detected cwd project on initial load when no override is set.
- [x] Saved manual overrides still display as selected overrides.
- [x] Clearing the override re-runs cwd project visibility.
- [x] Focused and full tests pass.

## Test Plan

- `uv run pytest -q tests/integration/test_web_dictation_blocks_api.py`
- `uv run pytest -q tests/integration/test_web_dictation_readiness_api.py tests/integration/test_web_dictation_settings_api.py tests/integration/test_web_project_kb_api.py tests/integration/test_web_dictation_blocks_api.py tests/integration/test_web_dry_run_api.py`
- Full regression: `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py`

## Notes

- This story only improves visibility. The same existing project
  detection and project-root override APIs remain the source of truth.
