# HSM-27-02 — The terminal surface on the diorama

- **Status:** backlog
- **Owner-gated:** device work — the hold-to-arm gesture, the key palette,
  the composer, and the spawn/kill controls are motion-felt; a sim
  screenshot is not the proof (the owner's bar). Proven on the cabled iPad.
- **Depends on:** HSM-27-01

## Problem

The iPad can decode the whole terminal wire now, but there is no way to
DO it on glass. This is the interactive surface, mirroring the web desk's
SessionPullout.

## Scope

- In: on the diorama's session surface — the live peek, a hold-to-arm
  chip → countdown, a KEY PALETTE (`^C`/arrows/`Escape`, armed-only), the
  voice-first composer, a PANE PICKER (attach to any `pane:%N`), a NODE
  chip, and the FACTORY controls (spawn in the picker; rename + a
  confirm-gated kill in the armed surface).
- Out: a PTY emulator; cross-machine factory; agent orchestration.

## Acceptance criteria

- [ ] The surface decodes and drives through HSM-27-01's client; the
      consent spine holds on glass (watch free, manipulate armed, the
      countdown visible, kill confirmed).
- [ ] The couch walk: attach a pane → arm → `C-c` → steer → spawn →
      rename → kill, live from the iPad; the audit reads it back.
- [ ] `swift test` green; the layer rule holds (no SwiftUI in
      Contracts/RuntimeCore/Providers).

## Implementation direction

- Mirror `web/src/desk/components/SessionPullout.tsx`: the key palette in
  the armed footer, the pane picker as a launcher, the factory controls
  as a SESSION row. Reuse the Phase-26 DioStage session grammar.
- Device-felt: build on the cabled iPad, not a sim screenshot.
