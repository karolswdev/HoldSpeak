# HSM-2-04 — 1-hour stability closeout (Gate 2)

- **Project:** holdspeak-mobile
- **Phase:** 2
- **Status:** backlog
- **Depends on:** HSM-2-01, HSM-2-02, HSM-2-03
- **Owner:** unassigned

## Problem

The charter's Track C gate (and program Quality Gate 2, Audio Stability) is a
1-hour continuous recording. Long-run audio bugs — dropped buffers under
backpressure, slow memory growth, an interruption that kills the engine — only
appear over sustained capture, not in a 30-second test. This story proves the
engine holds for an hour on real hardware.

## Scope

- **In:** a 1-hour continuous recording on a Tier-1 device, instrumented for
  dropped-buffer count, memory over time, and audio integrity of the exported
  WAV; deliberately injecting at least one interruption (call/Siri) and one route
  change (headphone unplug / Bluetooth) during the run to prove resume; the
  recorded device trace as evidence.
- **Out:** transcription of the hour (Phase 3). Background/screen-off recording if
  the phase decided foreground-only (note which posture the run proves). Thermal
  stress as a dedicated scenario (Phase 11 owns the hardening matrix; this is the
  audio-stability gate only).

## Acceptance criteria

- [ ] A 1-hour continuous recording completes on a real Tier-1 device (iPad
      Air/Pro M4 or iPhone 17 Pro Max) with **zero dropped buffers** and no audio
      glitches in the exported WAV.
- [ ] Memory is bounded over the hour (no unbounded growth / leak) — shown as a
      memory-over-time trace, not a single snapshot.
- [ ] At least one interruption and one route change occur mid-run and the engine
      resumes without losing the recording.
- [ ] The run is on hardware, not the simulator; the device + the posture
      (foreground/background) it proves are recorded in evidence.

## Test plan

- Manual / device: the instrumented 1-hour run on a Tier-1 device, with the
  injected interruption + route change; capture the dropped-buffer counter, the
  memory trace, and the WAV integrity check.
- Unit: the per-chunk allocation + bounded-buffer assertions from HSM-2-02 run in
  CI as the fast guard; the hour run is the gate.

## Notes / open questions

- Simulator audio does not prove this gate — if no device is available, park the
  story and say so; do not close Phase 2 on simulator-only evidence.
- This is the phase's closeout; on pass, write `evidence-story-04.md` and
  `final-summary.md`, and flip the phase to done in the README index.
