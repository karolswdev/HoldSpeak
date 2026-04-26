# HS-5-02 — Dictation readiness panel

- **Project:** holdspeak
- **Phase:** 5
- **Status:** done
- **Depends on:** HS-5-01
- **Unblocks:** faster dogfood setup loops from the browser
- **Owner:** codex

## Problem

After phase 4 and HS-5-01, `/dictation` can edit the important
surfaces, but the user still has to mentally join separate panels:
pipeline settings, selected project, block availability, project KB,
runtime backend, model path, and dry-run results. That makes setup
feel like troubleshooting instead of a cockpit.

## Scope

- **In:**
  - `GET /api/dictation/readiness?project_root=...`.
  - Readiness snapshot for project, pipeline config, global/project
    blocks, resolved block source, project KB, runtime backend/model,
    counters/session state, and actionable warnings.
  - `/dictation` Readiness section with status cards and next actions.
  - Tests for ready, disabled/no-project, missing-model, invalid
    project root, and page-surface branches.
- **Out:**
  - Loading the LLM model just to check readiness.
  - Native file picker for project selection.
  - Automatic model download.

## Acceptance Criteria

- [x] API reports ready state and actionable warnings without loading the LLM model.
- [x] API honors `project_root` override from HS-5-01.
- [x] UI renders pipeline, blocks, project KB, and runtime cards.
- [x] UI renders next-action warnings with section navigation.
- [x] Focused and full tests pass.

## Test Plan

- `uv run pytest -q tests/integration/test_web_dictation_readiness_api.py tests/integration/test_web_dictation_blocks_api.py tests/integration/test_web_project_kb_api.py tests/integration/test_web_dry_run_api.py`
- Full regression: `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py`

## Notes

- Bundling note: committed together with HS-4-05, HS-4-06, HS-5-01,
  and HS-5-03 because the user asked to commit the accumulated
  significant work from this session. `.tmp/BUNDLE-OK.md` records the
  intentional bundle.
