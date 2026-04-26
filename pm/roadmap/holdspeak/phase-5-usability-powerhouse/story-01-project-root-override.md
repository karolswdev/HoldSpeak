# HS-5-01 — Dictation project-root override

- **Project:** holdspeak
- **Phase:** 5
- **Status:** done
- **Depends on:** HS-4-05
- **Unblocks:** browser-first dictation authoring across multiple local projects
- **Owner:** codex

## Problem

Phase 4 made blocks, project KB, runtime config, and dry-run preview
browser-operable, but project-scoped work still targeted only the
project detected from the `holdspeak` process cwd. That forced users
to relaunch the app from another directory just to edit or test
another project's dictation configuration.

## Scope

- **In:**
  - Optional `project_root` override for project-scope block CRUD.
  - Optional `project_root` override for project-KB GET/PUT/DELETE.
  - Optional `project_root` in dry-run payload.
  - `/dictation` UI control to apply/clear a project root override,
    persisted in localStorage.
  - Integration tests covering block, project-KB, and dry-run override
    paths plus UI anchors.
- **Out:**
  - File-picker/native dialog integration.
  - Multi-project tabs.
  - Remote/project index service.

## Acceptance Criteria

- [x] Project-scope block endpoints accept `project_root` and target that project without changing process cwd.
- [x] Project-KB endpoints accept `project_root`, including creation of `.holdspeak/project.yaml` under the selected root.
- [x] Dry-run accepts `project_root` and runs against that project's blocks + KB.
- [x] `/dictation` exposes apply/clear controls for the override.
- [x] Focused tests pass.

## Test Plan

- `uv run pytest -q tests/integration/test_web_dictation_blocks_api.py tests/integration/test_web_project_kb_api.py tests/integration/test_web_dry_run_api.py`
- Full regression before handoff.

## Notes

- Bundling note: committed together with HS-4-05, HS-4-06, HS-5-02,
  and HS-5-03 because the user asked to commit the accumulated
  significant work from this session. `.tmp/BUNDLE-OK.md` records the
  intentional bundle.
