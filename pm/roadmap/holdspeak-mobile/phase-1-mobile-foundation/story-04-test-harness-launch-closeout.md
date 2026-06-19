# HSM-1-04 — Test harness + Gate-1 launch closeout

- **Project:** holdspeak-mobile
- **Phase:** 1
- **Status:** backlog
- **Depends on:** HSM-1-01, HSM-1-02, HSM-1-03
- **Owner:** unassigned

## Problem

The charter's Gate 1 is "application launches on iPhone and iPad." A green build
is not a launch, and a passing `swift test` is not proof the host app runs. The
phase needs a test harness the later phases extend, and a recorded launch on both
device classes so Gate 1 is evidenced, not asserted.

## Scope

- **In:** a test harness convention the package carries forward (where unit tests
  live, how the `Hosts` app target is smoke-launched, how device/simulator runs
  are recorded); a minimal launchable `Hosts` app that boots to a placeholder
  screen over the Runtime Core; the Gate-1 closeout — launch on an iPhone and an
  iPad (simulator at minimum, real Tier-1/Tier-2 device if available) with a
  per-device launch artifact (log/screenshot).
- **Out:** any feature UI (Phases 8–9). Audio, transcription, persistence,
  inference. Re-deriving the contract round-trip (HSM-1-02 owns it).

## Acceptance criteria

- [ ] The `Hosts` app launches to a placeholder screen on an iPhone destination
      and an iPad destination, evidenced by a launch log or screenshot per device.
- [ ] The test harness is documented (one place that says how to run the suite
      and how to add a phase's tests) and `swift test` runs green through it.
- [ ] The launch artifacts are committed/linked in `evidence-story-04.md`; a
      build-only log is explicitly rejected as Gate-1 evidence.
- [ ] If only the simulator is available, that is stated plainly in evidence (real
      device launch noted as the stronger proof, deferred to where hardware lands).

## Test plan

- Unit: `swift test` through the harness → green log.
- Manual / device: launch the `Hosts` app on an iPhone sim + an iPad sim (and a
  real device if available); capture a screenshot/log per device.
- Integration: n/a (the substantive integration tests arrive with the feature
  phases).

## Notes / open questions

- This closes Phase 1 and proves Gate 1. Keep the app deliberately empty — its
  only job here is to launch on both device classes over the four-layer package.
- The harness conventions set here are inherited by every later phase; make them
  cheap to extend (a new phase adds a test target/folder, not a new framework).
