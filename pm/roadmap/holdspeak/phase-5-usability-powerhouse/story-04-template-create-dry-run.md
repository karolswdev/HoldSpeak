# HS-5-04 — Template create + dry-run loop

- **Project:** holdspeak
- **Phase:** 5
- **Status:** done
- **Depends on:** HS-5-03
- **Unblocks:** one browser path from starter workflow idea to tested output
- **Owner:** codex

## Problem

Starter templates can create useful first blocks, and dry-run can test
typed utterances safely. The missing usability link is a single browser
flow that creates a starter block and immediately proves what it does
with that template's sample utterance.

## Scope

- **In:**
  - Use each starter template's `sample_utterance` as dry-run input.
  - Add an API path for `POST /api/dictation/blocks/from-template` to
    create a block and return dry-run output in one request.
  - Preserve duplicate-safe block IDs while reporting the actual
    created block ID in dry-run output.
  - Honor global/project scope and the active `project_root` override.
  - Add `/dictation` UI controls for "Create + dry-run".
  - Show created block ID, sample input, pipeline stages, and final
    output in the browser dry-run result.
- **Out:**
  - User-authored template management.
  - Template import/export.
  - Live microphone capture from the browser.

## Acceptance Criteria

- [x] Each block template exposes a sample utterance suitable for dry-run.
- [x] The Blocks panel can create a starter block and immediately run a dry-run using that sample.
- [x] The flow respects global/project scope and active `project_root` override.
- [x] The UI shows the created block ID, dry-run input, pipeline stages, and final output.
- [x] Duplicate-safe IDs continue to work.
- [x] Errors are actionable for invalid template input, invalid scope/project root, and disabled or unavailable pipeline states.
- [x] Focused and full tests pass.

## Test Plan

- `uv run pytest -q tests/integration/test_web_dictation_blocks_api.py tests/integration/test_web_dry_run_api.py`
- `uv run pytest -q tests/integration/test_web_dictation_readiness_api.py`
- Full regression: `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py`

## Notes

- The API keeps the existing create-only behavior by default. Clients opt
  into the combined flow with `{"dry_run": true}`.
