# HSM-25-02 — The conveyor renders: phases as the belt, stories as the items

- **Status:** backlog
- **Depends on:** HSM-25-01.

## Problem

A decoded feed nobody can see is a JSON blob. The conveyor is a desk primitive beside the Agent Desk (`DioStage`), rendering each rails project as a belt: phases as segments, the current phase's stories as the items, the next actionable story in the Signal ember accent, warnings visible. A repo whose status is not `live` renders its honest compatibility/unavailable state, never an empty belt.

## The design

A `MissionControlModel: ObservableObject` (the DictateModel idiom) fetches via the client and maps failure to a first-class `Reach`-style state (unreachable is rendered, never thrown); a `MissionControlView` renders the belts with `Sig.*` tokens and `.signalCard`; a `#if targetEnvironment(simulator) seedDemo()` injects a live belt for offline screenshots. Mounted as a desk tile opening the view via `.sheet`/`.navigationDestination`.

## Test plan

Pure view-model logic tests (belt assembly from a feed fixture, the compatibility/unavailable states, the next-story highlight) via `swift test`; a simulator screenshot once it renders.
