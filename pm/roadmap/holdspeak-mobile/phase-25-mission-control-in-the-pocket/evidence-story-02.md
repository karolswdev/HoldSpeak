# Evidence — HSM-25-02 — The conveyor renders

**Status:** done (2026-07-04).

## The move

- `Sources/Contracts/MissionControl.swift` gains
  `pinMissionControlSessions(_:)` — the belt's live-layer decision,
  pure and testable: `on_story` pins to its story id(s), ambiguous
  never guesses (unknown beats guessed), everything else stays
  off-belt. Mirrors the web workbench's server-side kernel
  (`mission_control_live_layer`, WLA-15-02) so both clients make the
  same call from the same correlation document.
- `App/MeetingCapture/MissionControlView.swift` — the conveyor
  screen: `MissionControlModel` (an `ObservableObject`, the
  `DictateModel`/`CompanionBoardState` idiom) polls the client every
  4s (the coder-poll cadence), renders unreachable/unauthorized as
  first-class `MCReach` states rather than throwing, and a
  `#if targetEnvironment(simulator)` seed for offline screenshots.
  `MissionControlView` renders belts with `Sig.*` tokens and
  `.signalCard`, matching the Agent Desk's visual language exactly —
  phases as segments, the current phase's stories as chips with the
  next-actionable in the ember accent, sessions pinned onto their
  story chips, an off-belt section, and a refusal-first event
  ticker. A small dependency-free `FlowLayout` wraps the chips.

## Honest scope note on verification

`App/MeetingCapture/` is a separate Xcode app target (not part of
the `HoldSpeakMobile` SwiftPM package `swift build`/`swift test`
cover) and this environment has no `xcodegen`/generated
`.xcodeproj` to drive `xcodebuild` headlessly. The **pinning
kernel — the story's testable logic — was extracted into
`Sources/Contracts` precisely so it could be proven here**; the
SwiftUI view code follows the codebase's established idioms
(`AgentDeskView`/`DictateModel`/`CompanionMesh` patterns, read
directly from the source) as closely as I could verify by reading,
but its actual compilation and the Simulator screenshot remain
open — the on-device leg (HSM-25-04) is where that gets proven for
real, same as this phase's dashboard already names.

## Proof

`cd apple && swift test`:

```text
MissionControlPinningTests — Executed 7 tests, 0 failures:
  testOnStoryPinsToItsStory
  testOnStoryWithMultipleStoriesPinsToEach
  testAmbiguousNeverGuessesAPin
  testOtherCorrelationsStayOffBelt
  testMultipleSessionsCanPinToTheSameStory
  testStaleAndAwaitingFlagsSurviveThePin
  testOnStoryWithNoStoriesFallsOffBelt

Full package suite — Executed 480 tests, with 9 skipped, 0 failures
(473 prior + 7 new; no regression)
```

`swift build` — clean (the package, including the new
`pinMissionControlSessions` export, compiles).
