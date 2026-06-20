# HSM-8-05 — The air-gapped notetaker (fully-local, zero-connectivity)

- **Project:** holdspeak-mobile
- **Phase:** 8
- **Status:** backlog
- **Depends on:** HSM-8-01, HSM-8-02, HSM-8-03, HSM-8-04, HSM-5-02 (Mode A on-device), HSM-6-02 (intelligence), HSM-7-03 (MIR seam)
- **Unblocks:** HSM-8-06
- **Owner:** unassigned

## Problem

This is the paradigm the whole on-device runtime exists for, and it had no
first-class home (owner steer, 2026-06-20): **you bring the iPad to a meeting with
zero connectivity** — airplane mode, no desktop, no LAN, no endpoint — and it does
the full notetaker job entirely on-device. Record → local Whisper transcription →
local (Mode A) meeting intelligence → handwritten notebook → linked moments →
artifact review, all offline, and it has to be *rich*, not a degraded fallback.
Phase 8 named the workflow but never named the air-gapped condition or proved the
experience under it; Phase 5 carries the engine's airplane-mode checkbox, not the
experience. This story makes the air-gapped notetaker an explicit, first-class
scenario with its own gate.

## Scope

- **In:** the fully-local notetaker experience and its proof — the Phase-8 workflow
  (capture → live transcript → notebook → linked moments → artifact review) running
  end to end with **Mode A** (on-device GGUF, HSM-5-02) and the on-device Whisper
  (Phase 3), under **real airplane mode** (no desktop / LAN / endpoint reachable);
  an honest "fully on-device" egress state (the egress badge reads local / nothing
  leaves); graceful behavior when no model is resident (clear guidance, never a
  dead end); and the air-gapped gate walkthrough on a physical iPad.
- **Out:** the companion/server features (Phases 12–13 — explicitly *not* needed
  here; their absence must not degrade this). Ink-into-intelligence (HSM-8-06 —
  this story proves the offline loop; 8-06 deepens the pencil's role on top).
  Engine performance tuning (Phase 5 / Phase 11). Sync (Phase 10).

## Acceptance criteria

- [ ] In real airplane mode on a physical iPad (no desktop, no LAN, no endpoint),
      the full notetaker loop runs: record → on-device transcript → **Mode A**
      on-device intelligence → notebook + linked moments → artifact review — with no
      network access at any step (proven, e.g., with the radios off).
- [ ] The experience is rich, not a degraded fallback: the artifacts are real and
      profile-shaped (MIR via HSM-7-03), the notebook is the full HSM-8-02 surface,
      and the UI is Signal-grade — the offline meeting feels first-class.
- [ ] The egress state is honest and calm — "on-device · nothing leaves" — with no
      privacy-novel prose (positioning canon).
- [ ] No-model-resident is handled gracefully: clear, actionable guidance to get a
      model on-device (HSM-5-03 paths), never a crash or a silent dead end.
- [ ] **Air-gapped gate:** the offline walkthrough is evidenced by a device
      recording/screens with the network provably off; `evidence-story-05.md`
      written.

## Test plan

- Device: the airplane-mode walkthrough above on the unlocked iPad with a resident
  Mode-A model — record a short real meeting offline, get real local artifacts,
  take pencil notes, review; capture the radios-off proof. A no-LLM plumbing pass
  is not sufficient — the local model must actually produce the artifacts
  (real-metal posture).
- Unit: the runtime composes capture + Mode-A inference + store with every
  network/companion seam absent → the loop still completes (no hidden dependency on
  a reachable peer).

## Notes / open questions

- This is the counterpart to the companion track's P8 ("not a dumb terminal"): there
  the iPad must not lose its server face; here it must not lose its **standalone**
  face. The device is first-class in both directions.
- Device-gated (iPad unlock + a resident Mode-A model). If blocked, host-prove the
  no-network composition and stage the airplane-mode device run with a ready script
  (mirror HSM-5-02's pending airplane-mode run) — but the gate is not "done" until
  a real offline meeting yields real local artifacts on device.
- Reuses HSM-5-02 (Mode A) + the HSM-5-05 30-min local gate; this story is the
  *experience* gate over that engine, not a re-proof of the engine.
