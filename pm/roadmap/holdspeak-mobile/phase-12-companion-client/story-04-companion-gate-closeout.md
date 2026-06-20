# HSM-12-04 — Track M gate closeout

- **Project:** holdspeak-mobile
- **Phase:** 12
- **Status:** backlog
- **Depends on:** HSM-12-01, HSM-12-02, HSM-12-03
- **Unblocks:** Phase 13 (Answer the Coder) runs on this proven foundation
- **Owner:** unassigned

## Problem

The companion is only real when it is proven on the metal the owner described: an
iPad in hand, pointed at the same server a coding session runs against. This story
is the Track M gate — the end-to-end device walkthrough — and it carries the
non-negotiable counter-proof that the iPad was **not** neutered in the process.

## Scope

- **In:** a real-hardware walkthrough on the physical iPad Air M4 against a real
  desktop/homelab server over the LAN/Tailscale: point the iPad at the server,
  list the server's meetings, start and stop a meeting from the iPad, and watch
  live state track it — then confirm the iPad's on-device runtime still fully works
  (start a local capture / local intelligence) to prove it stands its own ground.
  Evidence captured (screenshots/log) and the `final-summary.md` written.
- **Out:** answering the coder / voice notes / the companion board (Phase 13). Any
  new feature work (this is the closeout of 12-01..03). Hardening scenarios (Phase
  11).

## Acceptance criteria

- [ ] On a physical iPad against a real desktop: point-at-server → list meetings →
      **start and stop a meeting on the desktop from the iPad** → live state tracks
      it, evidenced by a device walkthrough (screenshots/log committed).
- [ ] **Not-a-dumb-terminal counter-proof:** with the iPad paired, an on-device
      action (local capture or local meeting intelligence) still runs fully — the
      device is enriched, not reduced — and this is shown in the same walkthrough.
- [ ] The server-unreachable path is exercised once on device (kill/restore the
      server) and the app keeps working locally without stalling.
- [ ] `final-summary.md` records the gate result, evidence, and any deferrals;
      `current-phase-status.md`, this README's phase index, and the program README
      "Last updated" line are updated per the operating cadence.

## Test plan

- Device: the full walkthrough above on the unlocked iPad + a reachable desktop;
  capture screenshots and a short log as evidence (a build/type-check is not
  validation — behavior on device is).
- Regression: `swift test` green (the host slice + seam tests from 12-01..03).

## Notes / open questions

- Device-gated like the other on-device gates — needs the iPad unlock (tracked
  across Phase 5/6 device follow-ups) and a desktop reachable on the LAN.
- If the live device run is blocked, host-prove every seam against a fake desktop
  and stage the device walkthrough with a ready script (mirror how HSM-5-06 / the
  Phase-56 macOS click were handled) — but the gate is not "done" until the real
  walkthrough lands.
