# HS-63-06 — Closeout: the live boot proof + final-summary + PR

- **Project:** holdspeak
- **Phase:** 63
- **Status:** backlog
- **Depends on:** HS-63-01..05
- **Unblocks:** phase exit
- **Owner:** unassigned

## Problem
A refactor's suite can be green while the composed runtime fails to
boot; the phase closes only on a live proof.

## Scope
- **In:** a live dogfood: the real composed runtime boots and serves;
  a meeting starts and stops through the real routes (segments + save);
  a dictation dry-run runs through the real pipeline route; the cockpit
  loads with zero page errors. Full suite; `final-summary.md`; BACKLOG
  E flipped to shipped; README cadence; PR merged on green; memory.
- **Out:** new features.

## Acceptance criteria
- [ ] The live trace ships in evidence (boot, meeting lifecycle,
      dictation dry-run, zero page errors).
- [ ] Full suite green (`--ignore=tests/e2e/test_metal.py`).
- [ ] final-summary; BACKLOG E flipped; README cadence; PR merged on
      green; memory recorded.

## Test plan
- The dogfood script + the full suite as regression.
