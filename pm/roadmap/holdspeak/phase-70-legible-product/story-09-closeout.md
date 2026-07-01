# HS-70-09 — Closeout: no dead doors, one clean arrival, proven

- **Status:** todo
- **Priority:** HIGH (the gate)
- **Depends on:** HS-70-01 … HS-70-08
- **Evidence:** _(added at close)_
- **Phase-exit:** ships `evidence-story-09.md` **and** `final-summary.md`.

## Goal

Prove the phase's thesis end to end: a freshly-launched hub is legible, no
route is a dead door, and a brand-new user goes launch → understand → first win
without confusion.

## Scope

- **No 404s:** every retired/moved/renamed route (`/setup`, `/activity`,
  `/history`↔`/meetings`, any others) redirects; the CLI launch nudge, docs
  links, and `tests/e2e/test_route_preflight.py` `PAGE_ROUTES` all point at
  real URLs; the all-routes zero-page-error sweep is green.
- **The arrival play-walk:** fresh clone / empty DB → launch → exactly one
  arrival surface that names the two modes → a first dictation win → lands on
  Home → the nav shows the four primaries with Studio collapsed. Screenshot the
  whole sequence. Reuse/extend the wizard + first-run dogfoods.
- **The legibility read-test:** record (in evidence) the 10-second "what is
  this + name the two modes + take a first action" test against the launched
  hub — the phase's real acceptance bar (AGENT-BRIEF §1).
- Full suite green (`uv run pytest -q --ignore=tests/e2e/test_metal.py`);
  `cd web && npm run build` clean; `_built/` untracked.
- Cadence: story headers, this `current-phase-status.md`, the project
  `README.md` (phase row + Last-updated + Current-phase), POSITIONING.
- `final-summary.md` written; PR to `main` merged on green.

## Proof required

The play-walk screenshot sequence; route pre-flight + zero-page-error sweep
green; the legibility read-test recorded; full suite count; the final summary.

## Done

_(filled at close)_
