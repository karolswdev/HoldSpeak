# AIPI-3-05 - Phase Exit + DoD + Cross-Network Runbook

- **Project:** aipi-lite
- **Phase:** 3
- **Status:** backlog
- **Depends on:** AIPI-3-01, AIPI-3-02, AIPI-3-03, AIPI-3-04
- **Unblocks:** AIPI-4
- **Owner:** unassigned

## Problem

Close phase 3: ship the cross-network runbook so a user can take
the AIPI-Lite + bridge to a coffee shop, conference, or AirBnB and
do voice typing against their home HoldSpeak install.

## Scope

### In

- **Cross-network runbook section** — either a new
  `docs/CROSS_NETWORK.md` or §9 of `docs/HOLDSPEAK_BRIDGE.md`,
  depending on size. Covers:
  1. **The shape** — what's running where (device on local WiFi;
     bridge on the user's laptop; HoldSpeak on the home host;
     tunnel between bridge and HoldSpeak).
  2. **Tailscale walkthrough (recommended)** — install on both
     ends, magic DNS hostname, bridge.env URL.
  3. **Cloudflare Tunnel walkthrough** — for users who want a real
     public hostname + Let's Encrypt cert.
  4. **WireGuard walkthrough** — for self-hosters.
  5. **Latency expectations** — typical numbers per path; what to
     do if it's slow.
  6. **PSK rotation across networks** — manual procedure.
  7. **Troubleshooting cheatsheet** — TLS-cert errors, NAT issues,
     RTT spikes, mDNS-not-finding-the-host.
- **Top-level `README.md` updated** to mention cross-network
  support exists (one paragraph + link to the runbook).
- **`final-summary.md`** per `roadmap-builder.md` §2.5: goal
  recap, exit criteria final state, story table, surprises +
  lessons, handoff to AIPI-4 (wake-word).
- **All AIPI-3-01..04 stories show `Status: done`** with paired
  `evidence-story-{n}.md` files (or AIPI-3-04 stays `paused` if
  HS-15 hasn't shipped per-device PSKs).
- **`pm/roadmap/aipi-lite/README.md`** reflects phase 3 done +
  phase 4 not-started; `Current phase` pointer moves to phase 4.

### Out

- AIPI-4 work itself (wake-word / on-device VAD).
- New tunnel/VPN choices beyond Tailscale + Cloudflare Tunnel +
  WireGuard.

## Acceptance Criteria

- [ ] Cross-network runbook exists, has been walked through with
  at least one tunnel/VPN end-to-end.
- [ ] All AIPI-3 stories show `Status: done` (or `paused` per
  documented dependency) with paired evidence files.
- [ ] `final-summary.md` records what shipped + what surprised us
  + handoff notes for AIPI-4.
- [ ] `pm/roadmap/aipi-lite/README.md` reflects phase 3 done +
  phase 4 not-started.
- [ ] Top-level `README.md` mentions cross-network support.

## Test Plan

- **Manual fresh-user simulation:**
  1. Stash any local Tailscale / tunnel config.
  2. Read only the cross-network runbook.
  3. Stand up a fresh tunnel (probably Tailscale since it's
     fastest).
  4. Verify voice typing works end-to-end from a separate network.
  5. Note any friction; fix in the runbook or record in
     `final-summary.md` as a known sharp edge.

## Notes

- Reuse the AIPI-1-06 + AIPI-2-06 runbook layouts (TL;DR, numbered
  sections, troubleshooting cheatsheet). The pattern works.
- Handoff to AIPI-4 in `final-summary.md` should call out:
  - What's now possible (cross-network voice typing + meetings)
  - What still hurts (PSK rotation across networks, latency on
    flaky connections)
  - What AIPI-4 inherits as a working baseline (the protocol
    contracts, the runbook patterns, the bridge architecture)
- Per the methodology: `final-summary.md` is created at phase
  exit and immutable. Don't write it before stories 01..04 are
  actually `done`.
