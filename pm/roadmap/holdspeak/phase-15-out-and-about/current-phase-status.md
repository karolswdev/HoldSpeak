# Phase 15 — Out-and-About (cross-network AIPI-Lite reach)

**Last updated:** 2026-07-07 (status doc backfilled by HS-86-01; the
phase itself is unchanged and unstarted).

## Goal

Cross-network reach for AIPI-Lite devices: tunneling (Tailscale /
Cloudflare Tunnel / WireGuard candidate evaluation), TLS, and
per-device PSKs — paired with the AIPI-Lite firmware's portable WiFi
work (multi-SSID + captive portal + Improv-WiFi) on the device-side
roadmap.

## Scope

- In: to be scoped when the phase opens (see the roadmap README
  phase-index row and the AIPI-Lite roadmap for the standing intent).
- Out: everything, until the phase opens.

## Exit criteria (evidence required)

- [ ] Defined when the phase opens.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|

## Where we are

Not started. Gated on Phase 25 landing the web-runtime auth + bind
guard (the standing sequencing rule in the roadmap README). This file
existed as a directory without a status doc until 2026-07-07; the
backfill records the gate and the intent, nothing more.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Opening this phase before Phase 25's auth/bind guard lands | low | the gate is recorded here and in the README | any story scaffolded here while Phase 25 is open |

## Decisions made (this phase)

- none yet.

## Decisions deferred

- Tunnel candidate (Tailscale vs Cloudflare Tunnel vs WireGuard) —
  decided when the phase opens — no default.
