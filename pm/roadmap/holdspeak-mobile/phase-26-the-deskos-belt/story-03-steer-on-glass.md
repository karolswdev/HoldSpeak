# HSM-26-03 — Attach, arm, steer, ground on glass

- **Status:** in-progress
- **Depends on:** HSM-26-01 (the contracts)
- **Owner-gated:** the interactive consent surface (hold-to-arm, countdown, send) is device-felt — its real proof is the couch walk (HSM-26-05).

## Problem

Steering a session must work from the iPad under the ported consent spine.

## Progress

- **Client layer (done, 2026-07-08, `swift test` 510/0):** the consent
  spine on the wire — `HTTPDesktopClient+Steering.swift`:
  `coderPeek(key:)` (watch, read-only), `armCoder(key:)` (the grant OR a
  typed refusal), `disarmCoder(key:)`, `steerCoder(key:text:submit:
  grounding:)` (delivered OR a first-class refusal), `steeringAudit()`.
  The refusals are DATA, not thrown: a 409 arm/steer body decodes into
  the result (`CoderArmResult`, `SteerResult`), so the surface re-offers
  ARM from the shape alone — the recycled-pane crown case
  (`revoked: true`) proven over a stubbed network
  (`SteeringClientTests.swift`, 7/7). Grounding rides the steer body as
  rails refs.
- **Surface (staged for the couch, HSM-26-05):** the steering pull-out
  (the live peek, the hold-to-arm chip → countdown, the voice-first
  composer). This is INTERACTIVE consent — the gesture, the countdown,
  and the send are motion-felt, so unlike the read-only belt a static
  sim shot is not the proof. Built and reviewed live on the cabled iPad.

## Scope

- In: the diorama surface that renders this capability STRICTLY from
  the HSM-26-01 contracts (mirror `apple/Sources/Contracts/Coding.swift`);
  sim-build + screenshot as the working proof.
- Out: any NEW hub capability (the routes exist); a shape with no
  contract row (that is a contract bug, fixed in HSM-26-01, not here).

## Acceptance criteria

- [ ] The surface decodes the documented contract shapes with no
      invented fields (a Swift shape maps 1:1 to a contract row).
- [ ] Sim-built and screenshot-verified; the consent spine
      (watch free, steer armed, everything audited) is preserved where
      it applies.
- [ ] `swift test` green; the guards green.

## Test plan

- Swift unit: the decoders against the HSM-26-01 fixtures.
- Sim: build + screenshot the surface on the diorama.
- Device: the couch walk (HSM-26-05) is the phase's real proof.

## Implementation direction

- Render on `DioStage` as pull-outs / cards, not new screens.
- Poll the documented routes (poll-only-while-open, the web desk's
  posture); the presence shapes are read, not synced.
- Defer the real device proof to HSM-26-05 (the couch walk).
