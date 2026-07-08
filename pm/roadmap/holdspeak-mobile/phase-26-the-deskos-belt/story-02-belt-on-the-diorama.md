# HSM-26-02 — The belt on the diorama

- **Status:** done
- **Shipped:** 2026-07-08 — sim-proven. Decode layer `swift test` 503/0; the belt renders on the iPad diorama from the `BeltState` contract (sim BUILD SUCCEEDED + screenshot). Evidence: [evidence-story-02.md](./evidence-story-02.md), [screenshots/belt-pullout.png](./screenshots/belt-pullout.png).
- **Depends on:** HSM-26-01 (the contracts)
- **Owner-gated:** the craft/acceptance proof is the couch walk (HSM-26-05); sim is the working proof.

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
- **Render (done, sim-proven):** `apple/App/MeetingCapture/DeskBelt.swift`
  — `BeltPrimitive`, a `DeskPrimitive` conformer whose whole UI (glyph,
  card, pull-out sections) is derived from the one declaration. Wired
  into `DioStage`: a `beltState` poll (`GET /api/missioncontrol/state`,
  15 s, read-only, `desktopClient`), the belt appended to `toolMembers`
  when the paired desktop names rails, and an `HS_DESK_BELT` sim-seed.
  The screenshot (`screenshots/belt-pullout.png`) shows both live rails
  with their current phase + stories (status marks ●/◐/◔, evidence +
  next tags), the ⚠ warnings lane, the honest `✕ unavailable` lane, and
  the "Local + your desktop" egress badge — the web conveyor's
  information in the diorama's pull-out grammar, from the contract.
- **Couch refinements (HSM-26-05):** the pull-out header truncates
  ("Mission Control" → "…ontrol"); stories render through the generic
  `.actions` body so each inherits a route-arrow that is not meaningful
  for a belt story. Both are polish for the device walk, not blockers.

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
