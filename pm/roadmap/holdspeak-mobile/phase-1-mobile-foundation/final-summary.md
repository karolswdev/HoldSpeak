# Phase 1 — Final Summary

- **Phase opened:** 2026-06-18
- **Phase closed:** 2026-06-18
- **Chunks shipped:** 4 stories (2 commits + 1 close commit on `main`, pushed)

## Goal — was it met?

> Establish the HoldSpeak Mobile Xcode workspace, the four-layer Swift Package
> layout (Contracts / Runtime Core / Providers / Hosts), a CI pipeline, and a test
> harness — and prove the app launches on both an iPhone and an iPad.

**Yes.** The `apple/` package exists with the four-layer graph, the `Contracts`
types round-trip the Phase-0 fixtures, CI is green on a hosted run, and the shell
launched on both device-class simulators (Gate 1).

## Exit criteria — final state

- [x] Four-layer SPM package; core layers UI-free — [evidence-01](./evidence-story-01.md)
  (grep-guard + `swift build`).
- [x] `Contracts` types round-trip every Phase-0 fixture — [evidence-02](./evidence-story-02.md)
  (`swift test` 5/5).
- [x] CI builds + tests green on a real run — [evidence-03](./evidence-story-03.md)
  (Actions run 27801601150, both jobs ✓).
- [x] **Gate 1 — the app launches on iPhone and iPad** —
  [evidence-04](./evidence-story-04.md) (iPhone 17 Pro Max + iPad Pro M5
  simulators, screenshots committed).

## Stories shipped

| ID | Title | Commit | Date |
|---|---|---|---|
| HSM-1-01 | Xcode workspace + four-layer SPM layout | 913cfb7 | 2026-06-18 |
| HSM-1-02 | Contracts Swift Codable types | 913cfb7 | 2026-06-18 |
| HSM-1-04 | Test harness + Gate-1 launch closeout | a4e0722 | 2026-06-18 |
| HSM-1-03 | CI pipeline | (close bundle) | 2026-06-18 |

## Stories cut or deferred

| ID | Title | Reason | Re-targeted to |
|---|---|---|---|
| — | full SwiftUI `Hosts` app + Xcode project | Gate 1 only needs a launchable shell | Phases 8 (iPad) / 9 (iPhone) |
| — | `xcodebuild` sim-destination test runs | host `swift test` is a valid proxy for platform-agnostic round-trips | optional CI enhancement |

## Surprises and lessons

- **No Xcode project needed for Gate 1.** Compiling the Contracts sources + a
  minimal SwiftUI `@main` app straight against the simulator SDK (`-parse-as-library`)
  and launching via `simctl` is a clean, scriptable Gate-1 proof — no `.xcodeproj`
  or xcodegen. (`scripts/gate1-launch.sh`.)
- **Workspace shape resolved SPM-first** — the SPM package is the source of truth;
  no standalone `.xcworkspace`.
- **One fixture set, two runtimes.** The Swift tests read the same
  `contracts/fixtures/*.json` the Python validator checks — interop is proven, not
  asserted.
- The toolchain (Swift 6.3 / Xcode 26.5 / iOS 26.5 sims) is available locally, so
  Swift phases are fully verifiable here.

## Handoff to phase 2

- **Now available:** a building, tested, CI-green four-layer package; `Providers`
  carries the `IAudioCapture` protocol stub Phase 2 implements.
- **Provisional iOS floor:** 17 (revisit at Phase 5 — Core ML `MLState` → 18,
  PROGRAM-RISKS P6).
- **Read first:** `apple/README.md`, then the Phase-2 status doc.

## Final asset / test posture

- `apple/` package: 4 targets, `swift test` 5/5 green, CI green (run 27801601150).
- Gate 1 launch screenshots committed (iPhone + iPad).
- Provider protocols stubbed for Phases 2–10.
