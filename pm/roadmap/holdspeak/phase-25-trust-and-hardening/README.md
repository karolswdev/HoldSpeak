# Phase 25 — Trust & Hardening

**Status:** in-progress (opened 2026-05-31; prioritized ahead of Phase 24; all stories backlog).

Phase 25 closes the trust gaps a full-system analysis surfaced: silent
local→cloud transcript egress, an unauthenticated web runtime, implicit LLM
concurrency safety, an unbounded transcription call, undocumented data-at-rest
posture, and a couple of no-op-prone config knobs. The phase exists so HoldSpeak
can be safely operated by someone other than its author and so Phase 15
(cross-network reach) has a defensible runtime to build on.

## Where to look first

- `current-phase-status.md` — goal, scope, exit criteria, story table, risks, pickup order.
- `story-01-loud-cloud-consent.md` — the highest-trust item (no silent egress).
- `story-02-web-runtime-auth.md` — the Phase 15 unblocker.
- `../../../holdspeak/intel.py`, `../../../holdspeak/intel_queue.py`, `../../../holdspeak/config.py` — intel + deferred-queue + config fields.
- `../../../holdspeak/web_server.py`, `../../../holdspeak/device_audio.py` — web runtime + the `verify_psk` pattern to mirror.
- `../../../holdspeak/transcribe.py`, `../../../holdspeak/controller.py`, `../../../holdspeak/plugins/dictation/runtime*.py` — transcription, the serialization lock, and the LLM runtimes.

## Phase boundaries

This phase owns trust/correctness hardening of the existing local product. It
does **not** own the `web_server.py` decomposition (Phase 26), cross-network
transport (Phase 15), product positioning, or any new feature surface.
