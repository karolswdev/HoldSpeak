# HSM Phase 27 — The iPad Terminal — final summary

**2/2 on glass, 2026-07-08.** The iPad has caught up to the web desk's
first-class agent manipulation. The one standing item is the LIVE
gesture walk on a real session (the couch acceptance).

## Why

Phases 89 and 90 gave the WEB desk first-class terminal manipulation —
any key, any pane, any machine, plus the session lifecycle — with a full
on-glass surface. The iPad was left behind: its steering client had only
Phase 87's five verbs and no interactive UI. The owner called it. This
phase closed the gap.

## The two stories

- **HSM-27-01 — the steering client parity (merged, PR #311).**
  `HTTPDesktopClient+Steering.swift` now speaks the full Phase-89/90
  wire: `coderKeys` (named + literal, node-routable), `steeringPanes`,
  `steeringNodes`, `killCoder`, `spawnSession`, `renameSession`, and a
  `node` param on arm/steer/keys/peek that routes through the relay (the
  web's `verbEndpoint` mirrored). New loose result types (SteerKey,
  PaneInfo, CoderKillResult, FactoryResult). Every verb pinned over a
  URLProtocol stub (`SteeringClientTests`, 16). `swift test` 519/0.

- **HSM-27-02 — the terminal surface (sim-proven).**
  `apple/App/MeetingCapture/DeskSteer.swift` is `DioSteerSheet`, the
  iPad's counterpart to the web `SessionPullout`: the pane peek, a
  hold-to-arm chip → countdown, the KEY PALETTE (`^C` loud, arrows,
  `Escape`, armed-only), the voice-first composer, a pane picker with
  `+ Spawn`, a confirm-gated ⌫ Kill, and a node chip. Wired into
  `DioStage` (a `steerSheet` state + a peek poll + handlers driving
  HSM-27-01's client, node-routable) with an `HS_DESK_STEER` seed. Sim
  BUILD SUCCEEDED; two screenshots (the armed surface, the pane picker).

## Proof

`swift test` 519/0; the Swift package + the Xcode sim both build; the
surface screenshot-verified on the iPad Pro sim; the layer rule holds
(`DeskSteer.swift` is an App file — no SwiftUI leaked into
Contracts/RuntimeCore/Providers); every commit through the stamped gate.

## The standing item

The **live gesture walk** — attach a pane → hold-to-arm → `C-c` → steer
→ spawn → rename → kill, LIVE from the iPad against a real hub + tmux,
the audit reading it back. That is motion-felt consent craft, so per the
owner's bar it is proven on the cabled iPad, not a sim screenshot. The
surface is built and sim-proven; the walk is the device acceptance.

## Riders

- Cross-machine factory (kill/spawn on a node) stays deferred, matching
  the web (the relay forwards steer verbs, not the factory).
- Rename on glass: the client verb exists (`renameSession`); the iPad
  surface exposes spawn + kill, with rename a small couch addition.
