# HS-150-04 — The web-inherited baseline (the debt rider)

- **Project:** holdspeak
- **Phase:** 150
- **Status:** ready
- **Depends on:** —
- **Unblocks:** HS-150-06
- **Owner:** unassigned

## Problem

Two arcs have carried six verified-inherited web-unit failures
(chat / containerQueryLaw / writeReceiptGuard / InlineEditor /
MicButton / workbenchAutomations — all byte-identical to main)
invisible to the pytest baseline vocabulary. The blind spot ends
here.

## Scope

### In (settled-design D5)

- `tests/web-inherited-baseline.txt` (or the house-consistent
  home): the six names, each annotated with provenance (the
  anchoring commit/phase); a checker (script or vitest reporter
  consumer) that diffs a web run's failures against it and speaks
  the house vocabulary ("baseline-subset, zero branch-new").
- Wire it into the close-sweep protocol note (the walk/close story
  consumes it).
- Fixing any of the six is WELCOME (each fix removes its line with
  attribution) but not required.

### Out

- Chasing the six roots (unless trivially fixed in-scope).

## Acceptance criteria

1. The checker, run against the current suite, reports exactly the
   six as baseline and zero branch-new.
2. An artificially broken web test is reported as BRANCH-NEW
   (prove, revert).
3. The protocol documented where sweeps are documented.

## Test plan

The checker run both directions; the doc touch.
