# Phase 15 — Out-and-about: cross-network reach for AIPI-Lite

**Status:** not-started. This folder is a placeholder created when
phase 14 closed (HS-14-08, 2026-05-07). The phase has **not** been
planned yet — there is no `current-phase-status.md` here on
purpose. Per `pm/roadmap/roadmap-builder.md`, the phase scaffold is
written at phase open, not at the prior phase's close.

## What this phase will own (placeholder)

The cross-network reach for AIPI-Lite-class devices that phase 14
explicitly deferred. Specifically:

- Tunnel / TLS termination: candidate evaluation across Tailscale,
  Cloudflare Tunnel, WireGuard, or a custom relay.
- Per-device PSKs (today phase 14 ships a single shared secret).
- Coordination with the AIPI-Lite firmware's portable WiFi work:
  multi-SSID, captive-portal flow, Improv-WiFi.
- Re-examining the four open questions in
  [`docs/DEVICE_PROTOCOL.md`](../../../../docs/DEVICE_PROTOCOL.md)
  §8 ("What phase 15 will need to revisit").

## Where to look first when phase 15 opens

- `pm/roadmap/holdspeak/phase-14-aipi-lite-devices/final-summary.md`
  §"Handoff to phase 15" + §"Cross-network deferral — explicit
  trigger".
- `docs/DEVICE_PROTOCOL.md` §8.
- The AIPI-Lite-side companion repo:
  `/home/karol/dev/esp32/AIPI-Lite-Voice-Bridge` (branch `mine`).
