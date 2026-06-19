# HSM-5-05 — 30-minute meeting closeout (Gate 4)

- **Project:** holdspeak-mobile
- **Phase:** 5
- **Status:** backlog
- **Depends on:** HSM-5-01, HSM-5-02, HSM-5-03, HSM-5-04
- **Owner:** unassigned

## Problem

The charter's Track F gate (program Gate 4) is "a 30-minute meeting processed
locally." This is the proof that Mode A is real on real hardware — that the
chosen engine, the per-device model, and the structured-output path can carry a
realistic meeting end to end without thermal kill, OOM, or network.

## Scope

- **In:** processing a ~30-minute meeting fully locally on a Tier-1 device,
  network disabled — transcript (from Phase 3) → local LLM → contract-shaped
  artifacts — with timing, thermal state, and memory recorded; the artifacts
  validated against the Phase-0 schemas.
- **Out:** desktop-parity quality (Phase 6 / Gate 5 — this gate proves it
  *processes*, not that it matches desktop quality). MIR profiles (Phase 7). UI.
  The 4-hour endurance run (Phase 11).

## Acceptance criteria

- [ ] A ~30-minute meeting is processed **fully locally** (airplane mode / network
      off) on a real Tier-1 device, end to end, producing artifacts.
- [ ] The emitted artifacts validate against the Phase-0 schemas with zero errors.
- [ ] Wall-clock processing time, peak memory, and thermal state during the run
      are recorded; the run completes without OOM or thermal termination.
- [ ] The device, model tier, and engine are stated in evidence (so Gate 4 is
      reproducible against a known configuration).

## Test plan

- Manual / device: the 30-minute local run on a Tier-1 device with network off,
  instrumented for time/memory/thermal; validate the artifacts against the
  schemas.
- Unit: n/a (the gate is an on-device end-to-end run; the unit guards live in the
  upstream stories).

## Notes / open questions

- If a 30-minute meeting can't complete at the per-device default, drop the
  default tier and re-baseline (a phase risk); if even 4B can't hold, escalate the
  gate to the owner — don't quietly redefine "processed."
- This closes Phase 5; on pass write `evidence-story-05.md` + `final-summary.md`.
- Pairs forward with Phase 11's airplane-mode and thermal scenarios — this is the
  first real local-load proof those will stress further.
