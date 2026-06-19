# HSM-11-01 — 4-hour meeting endurance

- **Project:** holdspeak-mobile
- **Phase:** 11
- **Status:** backlog
- **Depends on:** HSM-2-04, HSM-3-05, HSM-4-02
- **Owner:** unassigned

## Problem

Phase 2 proved 1 hour of audio; the charter's hardening scenario is a 4-hour
meeting — the full stack (capture + transcription + persistence, and deferred
intel) running four times longer. Long-session bugs (memory creep, segment-table
growth, transcriber drift) only surface at this duration.

## Scope

- **In:** a 4-hour continuous meeting on real hardware — capture → live/streamed
  transcription → persistence — instrumented for memory over time, dropped
  buffers, transcription continuity, and DB growth; intel processing of the result
  (deferred is fine).
- **Out:** the thermal/battery angle (HSM-11-03 — though a 4-hour run will warm the
  device, the dedicated thermal scenario owns that bar). Sync. New features.

## Acceptance criteria

- [ ] A 4-hour continuous meeting completes on a real Tier-1 device with no crash
      and no data loss (the full meeting + all segments persist and reopen intact).
- [ ] Memory is bounded across the 4 hours (trace, not a snapshot); no unbounded
      growth.
- [ ] Transcription stays continuous (no silent stop) and the persisted segment
      stream is complete end to end.
- [ ] The run is on hardware; the device, duration, and posture are recorded.

## Test plan

- Manual / device: the instrumented 4-hour run on a Tier-1 device; capture memory
  trace, buffer/segment counters, DB size, and a reopen-intact check.
- Unit: the bounded-buffer / store guards from Phases 2 & 4 run in CI as the fast
  tripwire.

## Notes / open questions

- Run this early in the phase — it's the riskiest and most likely to surface an
  earlier-phase design issue (phase risk). A failure here routes back to Phase
  2/3/4, not a Phase-11 patch.
- Pair with HSM-11-03: the 4-hour run is also a natural thermal soak; record
  thermal state even though HSM-11-03 owns that gate.
