# HSM-26-02 — The belt on the diorama

- **Status:** in-progress
- **Depends on:** HSM-26-01 (the contracts)
- **Owner-gated:** device work (the couch walk is the exit; sim is the working proof)

## Problem

The belt renders on glass but the diorama has no mission-control surface.

## Progress

- **Decode layer (done, 2026-07-08, `swift test` 503/0):** the Swift
  contract models (`apple/Sources/Contracts/MissionControl.swift`) for
  the belt state (`BeltState`/`BeltRepo`/`BeltProject`/`BeltPhase`/
  `BeltStory`) AND the presence shapes (peek, grant, steer result,
  audit entry, rails ref, journal entry) — mirroring the HSM-26-01
  schemas 1:1; the client (`HTTPDesktopClient+MissionControl.swift`:
  `missionControlState()`, `railsJournal()`); decode round-trips
  against the SAME fixtures the Python validator checks
  (`MissionControlTests.swift`). Also fixed a real contract bug the
  HSM-26-01 fidelity test missed: the audit `ts` was SQLite-naive
  ("YYYY-MM-DD HH:MM:SS"), not the contract's UTC-Z — `db/steering.py`
  now emits ISO-Z, and the fidelity test builds a REAL db row so it
  catches the drift.
- **Render (pending):** the `BeltPrimitive` + the conveyor surface on
  `DioStage`, sim-built + screenshot. The craft/acceptance proof is the
  couch walk (HSM-26-05).

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
