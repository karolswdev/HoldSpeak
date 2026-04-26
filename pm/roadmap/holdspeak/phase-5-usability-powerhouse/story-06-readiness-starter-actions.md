# HS-5-06 — Readiness starter actions

- **Project:** holdspeak
- **Phase:** 5
- **Status:** done
- **Depends on:** HS-5-04
- **Unblocks:** fixing a missing-block readiness warning without leaving the setup flow
- **Owner:** codex

## Problem

The readiness panel can identify that no dictation blocks are loaded,
but the user still has to interpret that warning, open Blocks, choose a
starter, and run the sample manually. The cockpit should convert that
warning into the next safe action.

## Scope

- **In:**
  - Add starter-template recommendations to the `no_blocks` readiness
    warning.
  - Recommend the correct target scope (`global` when no project is
    selected, `project` when a project root is active).
  - Add a `/dictation` readiness action that creates the recommended
    starter and runs its sample dry-run.
  - Keep the existing Open-section actions for other warnings.
- **Out:**
  - A full rule engine for all readiness warnings.
  - User-configurable readiness recommendations.
  - Server-side mutation from the readiness endpoint itself.

## Acceptance Criteria

- [x] `no_blocks` readiness warnings include a concrete starter template recommendation.
- [x] The recommended scope follows the active project context.
- [x] The browser readiness action can create the recommended starter and run its sample dry-run.
- [x] Existing readiness section navigation still works.
- [x] Focused and full tests pass.

## Test Plan

- `uv run pytest -q tests/integration/test_web_dictation_readiness_api.py tests/integration/test_web_dictation_blocks_api.py tests/integration/test_web_dry_run_api.py`
- Full regression: `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py`

## Notes

- The readiness endpoint remains read-only. The mutation happens only
  when the user clicks the browser action, via the existing
  create-plus-dry-run template API.
