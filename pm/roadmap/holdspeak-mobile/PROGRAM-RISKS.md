# HoldSpeak Mobile — Program Risk Register (HSM-0-05)

**Status:** the cross-phase risks that span the program (per-phase risks live in
each phase's `current-phase-status.md`). Every risk names a **stop signal** — the
concrete observation that triggers "halt this approach and regroup."

**Last updated:** 2026-06-18 (seeded at Phase-0 close).

| # | Risk | Phase(s) | Likelihood | Mitigation | Stop signal |
|---|---|---|---|---|---|
| P1 | **Contract drift** — desktop and mobile serializations diverge and sync corrupts on the wire | 0, 1, 10 | medium | One schema set (`contracts/schemas/`) + the validator on both ends; sync payloads ARE the Phase-0 contracts; UTC-`Z` normalization at the desktop boundary | A synced object fails Phase-0 schema validation on arrival — reconcile the contract before shipping sync |
| P2 | **12B / thermal infeasibility** — a 30-min meeting can't process locally at the per-device default without thermal kill or OOM | 5, 11 | high | Conservative defaults (4B iPhone / 8B iPad), 12B plugged-in-only, windowed processing, sustained (not burst) measurement in HSM-5-01 | 4B can't hold a 30-min local meeting on Tier-1 — escalate the gate / Mode-B default to the owner |
| P3 | **Sync data loss** — a concurrent edit on two devices silently overwrites one side | 10 | high | Non-destructive conflict policy (keep-both/merge), idempotent round-trip, divergent-edit tests first | A test shows a concurrent edit lost — halt; sync that loses data is worse than no sync |
| P4 | **Desktop-receiver dependency** — mobile sync has no peer because the desktop product can't receive | 10 | medium | Flag desktop-side receiver work as a `holdspeak` roadmap item early (HSM-10-02) | The continuity gate (HSM-10-04) blocks on a missing desktop receiver — file it cross-roadmap, don't fake the round-trip |
| P5 | **Hardware-gated closeouts** — gates 2/3/4/6/7 need real Tier-1/Tier-2 devices; only simulators available | 2, 3, 5, 10, 11 | medium | Treat device gates as hardware-only by nature; secure the devices before the closeout stories | A gate is closed on simulator-only evidence — reject; it does not meet the charter gate |
| P6 | **iOS deployment-floor coupling** — if Core ML wins (HSM-5-01), `MLState` KV cache forces an iOS-18+ floor set after Phase 1 chose a target | 1, 5 | low | Carry the dependency explicitly from HSM-5-01 back to Phase 1's minimum-deployment-target decision | Phase 1 ships a floor below iOS 18 and Core ML wins — re-baseline the floor |
| P7 | **Charter scope is large** (~26 weeks, 12 phases) and a late phase surfaces an early-phase design flaw | all | medium | Phase gates are evidence-bound; hardening (Phase 11) findings route back to the owning phase, not patched in place | A Phase-11 scenario fails for a reason rooted in an earlier phase — file it back to that phase, don't hack the hardening layer |

## Retired

- ~~Truncated charter Quality Gate list~~ — RETIRED 2026-06-18: owner confirmed
  Gates 3–7 as-reconstructed; `CHARTER.md` is the gate list of record.
