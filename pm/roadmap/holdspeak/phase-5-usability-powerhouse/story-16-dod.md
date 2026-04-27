# HS-5-16 - DoD sweep + phase exit

- **Project:** holdspeak
- **Phase:** 5
- **Status:** done
- **Depends on:** HS-5-01 through HS-5-15
- **Unblocks:** Phase 6 planning and execution
- **Owner:** codex

## Problem

Phase 5 accumulated the core usability cockpit improvements. It needs a
formal closeout: capture phase evidence, verify the current full
regression, summarize shipped value, mark Phase 5 done, and open the
next phase around the highest-value remaining product gap.

## Scope

- **In:**
  - Capture focused Phase 5 verification.
  - Capture full non-Metal regression.
  - Write phase-exit evidence bundle under
    `docs/evidence/phase-usability-powerhouse/20260426-1755/`.
  - Mark Phase 5 done in roadmap tracking.
  - Open Phase 6 scaffold for meeting action follow-through.
- **Out:**
  - New product code.
  - Broad frontend redesign.
  - Native file-picker implementation.

## Acceptance Criteria

- [x] Phase evidence bundle exists with environment, git status, focused sweep, full regression, manifest, and phase summary.
- [x] Focused Phase 5 sweep passes.
- [x] Full non-Metal regression passes.
- [x] Phase 5 story table includes this DoD closure story.
- [x] Project roadmap marks Phase 5 done and Phase 6 current.

## Test Plan

- `uv run pytest -q tests/unit/test_dictation_runtime_guidance.py tests/unit/test_doctor_command.py tests/integration/test_web_dictation_readiness_api.py tests/integration/test_web_dictation_blocks_api.py tests/integration/test_web_dictation_settings_api.py tests/integration/test_web_project_kb_api.py tests/integration/test_web_dry_run_api.py`
- `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py`

## Notes

- Phase 6 is intentionally not a continuation of runtime setup polish.
  The next larger product gap is turning meeting intelligence/action
  artifacts into reviewable work.
