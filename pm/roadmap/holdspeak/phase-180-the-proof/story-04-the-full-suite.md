# HS-180-04 — The full suite and live legs

- **Project:** holdspeak
- **Phase:** 180
- **Status:** backlog
- **Depends on:** Phase 179 merged
- **Unblocks:** HS-180-09
- **Owner:** unassigned

## Problem

The release candidate must have a clean test record: the full Python
suite, the Swift suite, the web baseline, and every live leg (the .43
runner, the companion, the metal walk) green.

## Scope

- In:
  - The full Python suite: `HOME=$(mktemp -d) uv run pytest -q
    --ignore=tests/e2e/test_metal.py -n auto`; zero failures.
  - The Swift test suite: `cd apple && swift test`; zero failures.
  - The web baseline check: `uv run python
    scripts/check_web_baseline.py --run`; zero branch-new.
  - The .43 runner live leg: the .43 box runs a sweep + drafter
    overnight; receipts land on the desk; the transcript is evidence.
  - The companion live leg: the companion discovers, authenticates,
    shows the portfolio, drills into a Room, receives a notification.
  - The metal walk: the owner's real desk, real mic, real model;
    evidence from the measured week (HS-180-01).
  - All results filed as evidence in the phase folder.
- Out:
  - Fixing test failures (filed as observations; not fixed in this
    proof phase unless they are trivially environmental).

## Acceptance criteria

- [ ] The full Python suite passes with zero failures (Article IX.1).
- [ ] The Swift suite passes with zero failures.
- [ ] The web baseline passes with zero branch-new.
- [ ] The .43 runner live leg is green with receipts on the desk.
- [ ] The companion live leg is green (discovery, portfolio, Room,
      notification on the real device).
- [ ] All results filed as evidence.

## Test plan

- Unit: the full Python suite; the Swift suite.
- Integration: CI; the .43 runner; the companion.
- Manual: the metal walk; the companion walk.

## Notes / open questions

- If the .43 box is unreachable at proof time (network issue), the
  live leg is documented as "could not verify" -- not faked.
