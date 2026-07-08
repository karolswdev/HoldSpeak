# HSM-26-04 — Rails grounding + the journal on glass

- **Status:** in-progress
- **Depends on:** HSM-26-01 (the contracts)
- **Owner-gated:** the grounding PICKER lives in the interactive steer composer — device-felt, staged for the couch walk (HSM-26-05).

## Problem

Rails objects and the ambient journal must be first-class on the diorama.

## Progress

- **The journal on glass (done, 2026-07-08, sim-proven):**
  `RailsJournalPrimitive` (`apple/App/MeetingCapture/DeskBelt.swift`) —
  a `DeskPrimitive` reading the ambient observer's journal from
  `GET /api/missioncontrol/rails/journal` (client + poll wired into
  `DioStage`, an `HS_DESK_JOURNAL` seed). The screenshot
  (`screenshots/journal-pullout.png`) shows each entry naming the events
  it saw (story flips, a gate refusal, the `@walk-remote` cross-machine
  origin) plus the local model's summary, with a meaningful "Route this
  to AI" affordance (a journal entry becomes AI-routable material). Sim
  BUILD SUCCEEDED.
- **Rails grounding into a steer (wire done, picker on the couch):** the
  grounding ref already rides `steerCoder(...grounding:)`
  (HSM-26-03 client, `SteeringClientTests` proves it carries the rails
  refs in the body). The grounding PICKER — choosing a rail object to
  attach — lives in the interactive steer composer, device-felt craft
  staged for the couch walk (HSM-26-05).

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
