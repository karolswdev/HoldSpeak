# HS-54-06 — Closeout: dogfood + final-summary + PR

- **Project:** holdspeak
- **Phase:** 54
- **Status:** backlog
- **Depends on:** HS-54-01, HS-54-02, HS-54-03, HS-54-04, HS-54-05
- **Unblocks:** none (phase exit)
- **Owner:** unassigned

## Problem
A behavior-preserving refactor is only proven by the product behaving: a green suite
plus a real click-through of every surface the carve touched. The phase also has to
land its tracking obligations (final summary, backlog flip, PR merged on green) or the
roadmap lies.

## Scope
- **In:**
  - **Dogfood:** against a live local runtime, click through all nine cockpit tabs and
    exercise the moved behavior — blocks CRUD + template dry-run, readiness cards,
    KB save, `.hs/` guided setup + doc suggestion, runtime save + depth knobs,
    corrections add/delete + learning digest, journal filter + replay, dry-run +
    moment-of-truth ritual, agent hooks render + context banner, project-root
    override + recent roots, discovery nudge, activity pre-briefing nudge + pin.
    Record the transcript + screenshots as evidence.
  - Full suite green (`uv run pytest -q --ignore=tests/e2e/test_metal.py`); `npm run
    build` clean; 0 `_built/` tracked.
  - `final-summary.md` with the before/after metrics (6,101 lines / 2 files → the
    shipped shape) and lessons.
  - Tracking: phase CLOSED in this folder + the project README (Last updated, Current
    phase, phase index row); BACKLOG candidate **D** flipped to shipped.
  - Push branch `phase-54-dictation-frontend`, open PR to `main`, merge on green CI.
- **Out:** any new carve work (if the dogfood finds a behavior change, fix it under
  the story that introduced it before closing).

## Acceptance criteria
- [ ] Dogfood transcript + screenshots committed; every exercised behavior identical.
- [ ] Full suite green; `npm run build` clean; 0 `_built/` tracked.
- [ ] `final-summary.md` ships in the same commit as this story's done-flip, with
      before/after metrics.
- [ ] README (Last updated + Current phase + phase index) and BACKLOG candidate D
      updated in the same commit.
- [ ] PR to `main` merged on green CI (Unit, Integration macOS, E2E macOS, Linux
      Smoke, Route screenshots).

## Test plan
- The full suite + the live dogfood above; CI green on the PR.

## Notes / open questions
- Per the Phase-26 lesson: run the **full** suite, not a narrow `-k` filter — narrow
  filters have hidden real regressions before.
