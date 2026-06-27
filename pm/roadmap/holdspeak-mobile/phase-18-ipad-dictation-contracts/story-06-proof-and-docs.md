# HSM-18-06 — The real-metal proof + entry-point docs

- **Project:** holdspeak-mobile
- **Phase:** 18
- **Status:** todo — the phase gate.
- **Depends on:** 18-01 … 18-05.
- **Unblocks:** closing Phase 18.
- **Owner:** unassigned

## Problem

The audit's standing rule: iPad work is proven on real metal, not seeded Simulator
screenshots ([[feedback_verify_on_device_not_seeded]]). The dictation contracts touch a live
paired hub (the relay, the macro dispatch, the readiness/dry-run routes), so they cannot be
proven offline or in the Simulator. And the entry-point docs (README, ARCHITECTURE,
GETTING_STARTED) must learn that the iPad is now a dictation client, not a stub.

## The design

1. **The metal walk.** On the cabled iPad against a live LAN hub: dictate a phrase and see
   the dry-run preview (18-01); speak a macro keyword over the relay and confirm it **fires**
   on the Mac (18-02) — the control-vs-treatment proof [[feedback_prefer_real_metal_proof]];
   dictate in a non-English language and confirm the language code took (18-03); speak a
   symbol and see it rendered (18-04); pick a nudge and confirm the following dictation is
   grounded in it (18-05). Capture the evidence under `phase-18-…/screenshots/` with a written
   trace (device walk, not a seed).
2. **The docs.** Update the entry points so a reader learns the iPad dictation client exists:
   README two-modes tour, `docs/ARCHITECTURE.md` device path, GETTING_STARTED. Keep HS-IDs
   out of `docs/*.md` (the voice guard rejects them).

## Scope

- **In:** the on-device proof of all five preceding stories against a live hub; the written
  trace + evidence; the entry-point doc updates.
- **Out:** new features (this is the gate, not a build story).
