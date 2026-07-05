# Evidence — HSM-25-03 — Sessions and events ride the belt

**Status:** done (2026-07-04).

## The move

HSM-25-02 already built the poll loop, the session pins, and the
off-belt buckets in `MissionControlModel`/`MissionControlView` — the
two stories shared one natural implementation surface (a single
conveyor screen). What HSM-25-03 lands as its own, distinct addition
is the piece that story left honestly incomplete: the event ticker
rendered `ts / event / story` but silently dropped `detail`, so a
`gate_refusal`'s rule id never actually reached the screen — the one
acceptance criterion this story exists to satisfy.

`Sources/Contracts/MissionControl.swift` gains `formatMCEvent(_:)`
— a pure formatter mirroring the web workbench's `mcEvents` renderer
(WLA-15-02): time, event name, story, and every non-null detail key
sorted for stable output. `MissionControlView`'s ticker now calls it,
so `gate_refusal` carries its rule id verbatim — the rails' words,
not the app's.

## Proof

`cd apple && swift test`:

```text
MissionControlEventFormattingTests — Executed 4 tests, 0 failures:
  testGateRefusalCarriesTheRuleIdVerbatim
  testEventWithNoDetailOmitsTheTrailingSection
  testEventWithNoStoryOmitsIt
  testMultipleDetailKeysAreSortedForStableOutput

Full package suite — Executed 484 tests, with 9 skipped, 0 failures
(480 prior + 4 new; no regression)
```

The same honest scope note as HSM-25-02 applies: the SwiftUI wiring
is unverifiable headlessly in this environment; the on-device leg
(HSM-25-04) is where it gets proven for real.
