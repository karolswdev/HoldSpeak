# HSM-3-05 — Latency gate closeout (< 2s)

- **Project:** holdspeak-mobile
- **Phase:** 3
- **Status:** backlog
- **Depends on:** HSM-3-01, HSM-3-02, HSM-3-03, HSM-3-04
- **Owner:** unassigned

## Problem

The charter's Track D gate (program Gate 3) is realtime transcription latency
below 2 seconds. Latency is the make-or-break property of the live transcript and
only means something measured on real hardware with a stated method — not
asserted from a fast simulator run.

## Scope

- **In:** a defined latency metric (e.g. time from end-of-utterance to text
  available) and a measurement method; runs on Tier-1 hardware (and the Tier-2
  iPhone, the worst case) at the per-device default model; the recorded raw
  numbers + the pass/fail against the < 2s bar.
- **Out:** tuning the model/window beyond what the gate needs (HSM-3-02 owns the
  realtime path). Cross-device sync. Any artifact/intelligence latency (that's a
  Phase-5/6 concern).

## Acceptance criteria

- [ ] The latency metric and measurement method are written down before measuring
      (no post-hoc redefinition to pass).
- [ ] Measured realtime latency is **below 2 seconds** on the worst-case Tier-1
      device at the per-device default model, with raw numbers in evidence.
- [ ] The iPhone (Tier-2) number is recorded alongside even if the gate bar is set
      on Tier-1 — so the per-tier latency decision (deferred on the phase status)
      has data.
- [ ] The run is on real hardware; a simulator number is explicitly not accepted
      as the gate.

## Test plan

- Manual / device: scripted realtime runs on a Tier-1 device + the Tier-2 iPhone,
  capturing the latency distribution (not just a best case); record median + tail.
- Unit: a CI-side timing smoke test on the host as a regression tripwire (not the
  gate).

## Notes / open questions

- If iPhone can't hold < 2s after HSM-3-02's tuning, this feeds the deferred
  per-tier latency decision and HSM-0-05's owner Gate confirmation — surface it
  with data, don't quietly pass on Tier-1 only.
- This closes Phase 3; on pass write `evidence-story-05.md` + `final-summary.md`.
