# HSM-27-02 — The terminal surface on the diorama

- **Status:** done
- **Shipped:** 2026-07-08 — surface sim-proven; the live gesture walk is the couch acceptance. `DeskSteer.swift` (`DioSteerSheet`) renders the full terminal surface on the diorama (peek + hold-to-arm → countdown + KEY PALETTE + composer + pane picker + spawn + kill + node chip), wired to HSM-27-01's client in `DioStage`; sim BUILD SUCCEEDED + two screenshots; `swift test` 519/0. Evidence: [evidence-story-02.md](./evidence-story-02.md), [screenshots](./screenshots/).
- **Owner-gated:** the hold-to-arm gesture, the key taps, and the send/kill are motion-felt — the surface is sim-proven, but the LIVE walk on a real session (the audit reading it back) is the device acceptance, on the cabled iPad.
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

- [x] The surface renders + drives through HSM-27-01's client; the
      consent spine holds on glass (watch free, key palette + composer +
      kill armed-only, the countdown visible, kill confirmed). Sim
      BUILD SUCCEEDED + screenshots (`screenshots/steer-*.png`).
- [ ] The couch walk: attach a pane → arm → `C-c` → steer → spawn →
      rename → kill, LIVE from the iPad; the audit reads it back. (The
      device acceptance — motion-felt, on the cabled iPad.)
- [x] `swift test` green (519/0); the layer rule holds (`DeskSteer.swift`
      is an App file; no SwiftUI leaked into Contracts/RuntimeCore/
      Providers).

## Implementation direction

- Mirror `web/src/desk/components/SessionPullout.tsx`: the key palette in
  the armed footer, the pane picker as a launcher, the factory controls
  as a SESSION row. Reuse the Phase-26 DioStage session grammar.
- Device-felt: build on the cabled iPad, not a sim screenshot.
