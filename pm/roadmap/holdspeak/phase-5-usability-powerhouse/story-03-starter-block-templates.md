# HS-5-03 — Starter block templates

- **Project:** holdspeak
- **Phase:** 5
- **Status:** done
- **Depends on:** HS-5-02
- **Unblocks:** first useful dictation workflow without schema authoring
- **Owner:** codex

## Problem

The readiness panel can now tell a user that no blocks are loaded,
but the next action still required knowing the block schema and
inventing examples/templates from scratch. That is avoidable friction
for the first dogfood loop.

## Scope

- **In:**
  - Server-defined starter templates for common dictation workflows.
  - `GET /api/dictation/block-templates`.
  - `POST /api/dictation/blocks/from-template`.
  - Duplicate-safe block IDs when creating from a template repeatedly.
  - Project-root override support for template creation.
  - `/dictation` UI template picker in the Blocks panel.
- **Out:**
  - User-authored template library.
  - Template marketplace/import/export.
  - One-click dry-run after creation.

## Acceptance Criteria

- [x] User can see starter templates from the browser.
- [x] User can create a block from a starter template in global or project scope.
- [x] Creating the same template twice produces a unique block ID.
- [x] Project-root override is honored for project-scope template creation.
- [x] Focused and full tests pass.

## Test Plan

- `uv run pytest -q tests/integration/test_web_dictation_blocks_api.py tests/integration/test_web_dictation_readiness_api.py tests/integration/test_web_dry_run_api.py`
- Full regression: `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py`

## Notes

- Bundling note: committed together with HS-4-05, HS-4-06, HS-5-01,
  and HS-5-02 because the user asked to commit the accumulated
  significant work from this session. `.tmp/BUNDLE-OK.md` records the
  intentional bundle.
