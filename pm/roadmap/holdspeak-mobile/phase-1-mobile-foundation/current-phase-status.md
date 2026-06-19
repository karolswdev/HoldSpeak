# Phase 1 — Mobile Foundation

**Status:** CLOSED ✅ (4/4) 2026-06-18 — Gate 1 proven, CI green on a hosted run.
See [`final-summary.md`](./final-summary.md).
**Real-metal addendum (2026-06-19):** the HSM-1-04 follow-up is discharged — the
shell launched on a **physical iPad Air 11" (M4), iPadOS 26.5** (owner-confirmed
"contracts v0.1.0" on-device), via the new headless deploy tooling
(`apple/scripts/gen-device-project.rb` + `gate1-device.sh`). Stronger than the
simulator bar; phase stays CLOSED. Evidence:
[`gate1-ipadair-m4-realmetal.log`](./gate1-ipadair-m4-realmetal.log)
(`** BUILD SUCCEEDED **` → `Launched application with dev.holdspeak.mobile`),
discharging the HSM-1-04 physical-device follow-up.
Track B
of the Council Implementation Charter. The first Swift-bearing phase: it stands up
the four-layer SPM target structure (Contracts / Runtime Core / Providers /
Platform Hosts) and lands the Swift `Codable` types against the Phase-0 contracts,
then proves the shell launches on both device classes.

**Last updated:** 2026-06-18 (**Phase 1 CLOSED ✅ 4/4** — Gate 1 proven on the
iPhone 17 Pro Max + iPad Pro M5 simulators (HSM-1-04, screenshots committed) and
CI green on a hosted run (HSM-1-03, Actions 27801601150). See `final-summary.md`.
Phase 2 next. Earlier: **HSM-1-01 + HSM-1-02 done** — the `apple/` Swift
package exists with the four-layer target graph, the core layers UI-free
(grep-guarded); the `Contracts` `Codable` types + enums + `JSONValue` + the
snake_case/UTC-Z coder round-trip the Phase-0 golden fixtures via `swift test`
(**5/5 green**, the same fixtures the Python validator checks). Remaining: HSM-1-03
(CI) and HSM-1-04 (iOS app target + the Gate-1 on-device launch)).

## Goal

Stand up the Apple-platform foundation for the HoldSpeak Mobile Runtime: an Xcode
workspace, a four-layer Swift Package layout (Contracts / Runtime Core /
Providers / Platform Hosts) with the charter's dependency rule enforced (business
logic must not depend on SwiftUI/UIKit/WebView), the Swift `Codable` types that
mirror the Phase-0 JSON Schemas and round-trip the Phase-0 conformance fixtures, a
CI pipeline that builds and tests for iPhone and iPad simulator destinations, and
a test harness — closed out by the Track B gate: the app launches on iPhone and
iPad.

## Scope

- **In:** the Xcode workspace + the four-layer SPM package layout
  (`Contracts`/`RuntimeCore`/`Providers`/`Hosts` targets) with no UI dependency in
  the core layers (HSM-1-01); the Swift `Codable` types for the canonical entities,
  matching the HSM-0-02 schemas and round-tripping the HSM-0-04 fixtures
  (HSM-1-02); a CI pipeline that builds + runs `swift test` for iPhone and iPad
  simulator destinations (HSM-1-03); the test harness + the Gate-1 launch closeout
  on both device classes (HSM-1-04).
- **Out:** any audio capture (Phase 2), Whisper transcription (Phase 3),
  persistence/SQLite (Phase 4), local inference (Phase 5), intelligence/artifacts
  (Phase 6+), MIR (Phase 7), and the actual iPad/iPhone product UIs (Phases 8–9).
  The Contracts package's *content* (the schemas + fixtures) is owned by Phase 0;
  this phase consumes them, it does not author or redefine them. No on-device
  hardware run (simulator launch is the Gate-1 bar; real-device runs come with the
  features that need hardware).

## Exit criteria (evidence required)

- [ ] The Xcode workspace opens and resolves, and the SPM package exposes four
      targets — `Contracts`, `RuntimeCore`, `Providers`, `Hosts` — with the
      dependency graph proving `Contracts`/`RuntimeCore`/`Providers` import no
      SwiftUI/UIKit/WebView (HSM-1-01).
- [ ] `swift build` succeeds for the package and `swift test` passes, both shown
      as a green log, not a type-check (HSM-1-01, HSM-1-04).
- [ ] The Swift `Codable` types decode every HSM-0-04 golden fixture and
      re-encode to a semantically-equal payload — a passing round-trip test run in
      evidence (HSM-1-02).
- [ ] CI builds and runs `swift test` against an iPhone simulator destination AND
      an iPad simulator destination, green on a real run (HSM-1-03).
- [ ] **Track B gate — the application launches on iPhone and iPad** (simulator
      for each device class), evidenced by a launch log/screenshot per device
      (HSM-1-04).

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HSM-1-01 | Xcode workspace + four-layer SPM layout | done | [story-01](./story-01-xcode-workspace-spm-layout.md) | [evidence-01](./evidence-story-01.md) |
| HSM-1-02 | Contracts Swift Codable types | done | [story-02](./story-02-contracts-swift-types.md) | [evidence-02](./evidence-story-02.md) |
| HSM-1-03 | CI pipeline (iPhone + iPad sim) | done | [story-03](./story-03-ci-pipeline.md) | [evidence-03](./evidence-story-03.md) |
| HSM-1-04 | Test harness + Gate-1 launch closeout | done | [story-04](./story-04-test-harness-launch-closeout.md) | [evidence-04](./evidence-story-04.md) |

## Where we are

Just scaffolded. Phase 0 (Track A) fixes the contracts this phase consumes: the
`holdspeak-contracts` package home + serialization contract (HSM-0-03) and the
golden conformance fixtures (HSM-0-04) are the upstream inputs. The four stories
are stubbed against Track B's four deliverables (Xcode Workspace, Swift Package
Layout, CI Pipeline, Test Harness). **HSM-1-01 and HSM-1-02 are done:** the
`apple/` SPM package builds all four layers (Swift 6.3 / Xcode 26.5), the core
three are UI-free (grep-guarded), and the `Contracts` Codable types round-trip the
Phase-0 golden fixtures (`swift test` 5/5 green — decode, typed encode→decode
equality, UTC-Z encoding, the MIR-profile dimension, the actuator). The SPM
package is the source of truth (the deferred "workspace shape" resolved SPM-first;
no standalone `.xcworkspace`). **Phase 1 is CLOSED ✅ (4/4).** Gate 1 is proven
(HSM-1-04: the shell launched on the iPhone 17 Pro Max AND iPad Pro 13-inch (M5)
iOS-26.5 simulators, screenshots committed, showing "contracts v0.1.0" from the
real contract layer), and CI is green on a **hosted** run (HSM-1-03: Actions run
27801601150, both jobs ✓, after `git push`). See
[`final-summary.md`](./final-summary.md). Phase 2 (Audio Engine) is next.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| The four-layer rule is asserted but not enforced — UI types leak into the core via a convenience import | high | Make the dependency rule a build constraint: separate SPM targets so `Contracts`/`RuntimeCore`/`Providers` *cannot* link SwiftUI/UIKit, and assert it in CI | A core target compiles only because a host framework was on the search path — the layers are not actually separated |
| Phase-0 contracts not yet settled when HSM-1-01 wants to start | medium | HSM-1-01 depends on HSM-0-03 (package home + serialization contract); HSM-1-02 depends on HSM-0-04 (fixtures) — do not start the Swift types before the fixtures exist | The Swift types are being written against a guessed schema because Phase 0 hasn't shipped — stop and finish HSM-0-02/04 first |
| CI can't reach an iPad simulator destination (runner image lacks the simulator/SDK) | medium | Pin the simulator destinations explicitly (device + OS) and verify the runner image ships them before relying on it | A green CI run that silently only built one device class — fail the job if either destination is missing |
| "Launches" is read as "compiles" and the Gate-1 evidence is a build log, not a running app | medium | Gate-1 evidence is a launch artifact (screenshot/log of the app process running) on each device class, per HSM-1-04 | The closeout cites a build success in place of a launch — reject, it does not meet the charter gate |
| Codable casing/optionality drift from the Python source (snake_case vs camelCase, dates) | medium | Resolve impedance once via the HSM-0-03 serialization contract; the Swift types use `CodingKeys`/strategy to match the wire format, proven by the HSM-0-04 round-trip | A fixture fails to round-trip and the fix is a per-type hack instead of a contract-level decoding strategy — escalate to the contract |

## Decisions made (this phase)

- 2026-06-18 — Phase 1 establishes the four-layer SPM target structure as real,
  separately-buildable targets (not folders in one target), so the charter's "no
  UI dependency in business logic" rule is enforced by the build graph rather than
  by convention — charter Architecture §"Principle".

## Decisions deferred

- Workspace shape: a single `.xcworkspace` wrapping one SPM package + an app
  target, vs. an app project that depends on a local SPM package — trigger:
  HSM-1-01 — default: a `.xcworkspace` with the SPM package as the source of truth
  and a thin `Hosts` app target.
- Minimum deployment target (iOS version floor) — trigger: HSM-1-01 — default:
  the lowest iOS that supports the charter's Tier-1/Tier-2 devices (iPad Air/Pro
  M4, iPhone 17 Pro Max); confirm against the WhisperKit/inference floors before
  Phase 3/5 rather than guessing high now.
- CI host: GitHub-hosted macOS runner vs. self-hosted (the homelab/.43 path) —
  trigger: HSM-1-03 — default: GitHub-hosted macOS runner for the simulator build,
  revisit if device runs or signing are needed later.
- Test framework: XCTest vs. Swift Testing — trigger: HSM-1-02 — default: whatever
  `swift test` runs by default on the pinned toolchain; do not block the layout on
  this.
