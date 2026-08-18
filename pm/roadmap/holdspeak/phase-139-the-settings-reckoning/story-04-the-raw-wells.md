# HS-139-04 — The RAW wells

- **Project:** holdspeak
- **Phase:** 139
- **Status:** ready
- **Depends on:** 139-01
- **Unblocks:** 139-05
- **Owner:** delegated Opus worker; orchestrator adjudicates

## Problem

Thirty-one controls are operator wiring — retry curves, hysteresis
windows, score thresholds, poll intervals, stage lists, allowlists
(census FOLD-TO-RAW rows). They must keep working and stop being the
room's face. Standing rule: debug hides behind one folded RAW well.

## Scope

- **In:** each remaining module gains at most ONE folded `RAW` section,
  closed by default, containing that module's operator knobs (the
  census's FOLD-TO-RAW rows, including the wake-word model/threshold/
  window, the entire deferred-queue and routing knob sets, cadence
  tuning, device walker, rails tuning, actuator allowlists,
  fold-to-RAW secrets). Unfold state is not persisted — RAW starts
  closed every open. Knobs keep their exact config paths and write
  behavior.
- **Out:** changing any knob's semantics; a global RAW room (wells are
  per-module); removing anything (that was 01/02).

## Acceptance criteria

- [ ] No operator knob is visible without explicitly unfolding a RAW
  well; every well renders closed on open.
- [ ] Every folded knob still reads/writes its config path (spot-proof
  via route tests + one on-glass write in the walk).
- [ ] The module faces above the wells contain only KEEP-disposition
  controls.

## Test plan

- **Web:** vitest per module proving fold state + face content.
- **Unit:** settings route tests green (no schema change).
