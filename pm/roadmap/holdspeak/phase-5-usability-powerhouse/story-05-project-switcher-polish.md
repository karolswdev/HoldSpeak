# HS-5-05 — Browser project switcher polish

- **Project:** holdspeak
- **Phase:** 5
- **Status:** done
- **Depends on:** HS-5-01
- **Unblocks:** faster browser switching across dogfood projects
- **Owner:** codex

## Problem

The `/dictation` project-root override works, but it saved whatever
text the user typed without validating the path first. Repeatedly
switching between projects also required retyping full paths. That is
unnecessary friction for a browser-first dictation cockpit.

## Scope

- **In:**
  - Add a browser-facing project-context validation endpoint.
  - Return resolved project identity and expected blocks/KB paths.
  - Validate project roots before saving them to localStorage.
  - Keep recent project roots in browser localStorage.
  - Let users switch to a recent root without retyping.
- **Out:**
  - Server-side recent-project persistence.
  - File picker integration.
  - Multi-project comparison views.

## Acceptance Criteria

- [x] API validates a manual project root and returns project metadata.
- [x] API rejects missing manual roots with an actionable error.
- [x] Browser Apply validates the root before persisting it.
- [x] Browser keeps a small recent-root list and can switch from it.
- [x] Existing project-root override behavior still works for blocks, KB, readiness, and dry-run.
- [x] Focused and full tests pass.

## Test Plan

- `uv run pytest -q tests/integration/test_web_dictation_blocks_api.py tests/integration/test_web_dictation_readiness_api.py tests/integration/test_web_dry_run_api.py`
- Full regression: `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py`

## Notes

- Recent roots stay browser-local by design. This keeps the server
  stateless while still removing repeated path typing.
