# HS-96-07 — Closeout: walks, storm, owner rider

- **Project:** holdspeak
- **Phase:** 96
- **Status:** backlog
- **Depends on:** HS-96-06
- **Unblocks:** phase close

## Problem

A styling phase is exactly where regressions hide in plain sight. The
phase closes only against the production bundle: the full walk, the
frame budget, the guards, and the owner's eyes on the polish.

## Scope

- In:
  - the assembled production walk (the Phase 95 chain) green on the
    restyled bundle at 1440 and 393 with zero failed API responses;
  - the frame-budget storm re-run (assembled) with no regression against
    the Phase 95 numbers;
  - the full guard set (no-exit, cores, desk locks, validator, doc
    guards) and both suites green;
  - UAT Campaign 13 extended (or Campaign 14 authored) with the design
    polish beats — focus visibility, one-material reading, keyboard
    operation — for the owner's sitting;
  - final-summary.md with deferrals named; the owner walk preserved per
    the standing close directive if not sat live.
- Out:
  - fixing non-blocking findings beyond the walk (triage to BACKLOG).

## Acceptance criteria

- [ ] The assembled walk and shots pass on the restyled bundle; zero
      failed API responses.
- [ ] Storm: median and p95 within the Phase 95 envelope (≤16.7 / ≤33),
      no regression beyond noise against 8.3/10.2.
- [ ] All guards and suites green; the validator lock live in CI.
- [ ] The owner sitting is staged (campaign beats shipped) and the
      verdict recorded, or preserved per the standing close directive
      with the criterion verbatim in BACKLOG.
- [ ] final-summary.md names every deferral.

## Test plan

- the assembled walk; the storm; the full sweep with the standing metal
  exclusion; the campaign validation suite.

## Evidence required

- walk + storm + sweep outputs; shots; the campaign diff; the verdict or
  its preserved criterion.
