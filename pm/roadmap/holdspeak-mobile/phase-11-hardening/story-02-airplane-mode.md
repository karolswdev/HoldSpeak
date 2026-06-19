# HSM-11-02 — Airplane mode / offline

- **Project:** holdspeak-mobile
- **Phase:** 11
- **Status:** backlog
- **Depends on:** HSM-5-05
- **Owner:** unassigned

## Problem

"Fully local" (Mode A) is a headline charter promise. Airplane mode is the test
that proves it true: with no network at all, capture → transcribe → local LLM →
artifacts must work end to end, and nothing should degrade silently or fail with
an opaque error that implies a missing connection.

## Scope

- **In:** the full Mode A pipeline under airplane mode / all-network-off on real
  hardware — capture, transcription, local inference, artifacts, persistence —
  with explicit checks that no code path silently waits on or assumes a network;
  sync correctly queues (Phase 10) rather than erroring.
- **Out:** Mode B/C (those require network by definition; this scenario is Mode A).
  The 30-minute local proof itself (Phase 5 / HSM-5-05 — this reuses it under
  enforced offline). New features.

## Acceptance criteria

- [ ] With airplane mode on (no network), a meeting goes capture → transcribe →
      local LLM → artifacts → persisted, end to end, on real hardware.
- [ ] No feature degrades silently or fails with a misleading network error in
      Mode A; anything network-dependent (sync) is clearly queued, not broken.
- [ ] Re-enabling the network triggers no data loss and resumes any queued sync.
- [ ] The run records the device, model tier, and that the network was genuinely
      off (not just unused).

## Test plan

- Manual / device: airplane-mode end-to-end meeting on a Tier-1 device; verify
  artifacts + persistence + that sync queued rather than errored.
- Unit: a network-guard test asserting the Mode A path makes no network calls
  (a stubbed network that fails the test if hit).

## Notes / open questions

- The real failure mode to hunt is a hidden network assumption (a telemetry ping,
  a model-availability check) that only bites offline — the no-network-calls guard
  is the tripwire.
- This is also the privacy proof Mode A implies; surface egress honestly (Mode A =
  local-only badge) per positioning canon.
