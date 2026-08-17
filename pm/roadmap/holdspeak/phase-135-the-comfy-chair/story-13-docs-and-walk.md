# HS-135-13 — Docs and the walk

- **Project:** holdspeak
- **Phase:** 135
- **Status:** backlog
- **Depends on:** HS-135-01..12
- **Unblocks:** —
- **Owner:** unassigned

## Problem

The Chair's worth is a measured claim: the five-jobs numbers must
move, the laws must hold on glass, and the docs must teach the new
front door.

## Scope

### In

- Docs entry points: README's usage surface introduces the Chair
  (home, the floor button, the hero); any onboarding/docs page the
  repo's conventions dictate; drift guards green.
- The walk (committed harness, extending the house lineage):
  - Screenshot walk at 1440 AND 960 (the new desktop floor width):
    the Chair (seeded, all four lanes populated), each lane's
    open-in-window, the floor swap both ways, the hero recording
    state, sparse surfaces, the L6/L7 fixes on settings-models and
    Intelligence tabs. FRESH BUNDLE FIRST (the Phase-134 rule);
    zero console errors unfiltered.
  - The five-jobs stopwatch RE-RUN with the same method as the
    baseline (assets/five-jobs-baseline.md): record, 1:1 note, TODO
    (still a note — honest), ask, check agents — from the CHAIR as
    landing. The report shows before/after actions+seconds per job.
  - Sound proof: the sfx triggers fire in the walk (assertion on the
    mocked/instrumented layer, or captured audio events).
  - The migration proof from HS-135-01 referenced (real-backup copy
    migrates; hub boots).
  - Full suite gate (quiet tree, isolated HOME, -n auto, metal
    excluded), zero regressions vs baseline.
- All through `dw evidence capture`; the walk cannot be closed by
  unit tests alone and cannot be waived.

### Out

- 393w walking (Phase 136 owns the narrow shell and its walk).

## Acceptance criteria

- [ ] Both-width shots of every Chair surface + the swap + the fixes;
  zero console errors.
- [ ] Five-jobs table: before vs after, with at least Ask and Record
  paths improved or held at 1 action, and every regression (if any)
  named honestly.
- [ ] Suite zero regressions; docs guards green.

## Test plan

- `.githooks/dw evidence capture holdspeak 135 13 -- <walk + suite commands>`;
  stopwatch table in evidence.
