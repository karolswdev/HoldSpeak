# Evidence — HSM-1-01 — Xcode workspace + four-layer SPM layout

- **Shipped:** 2026-06-18
- **Commit:** Phase-1 foundation bundle on `main` (see commit message)
- **Owner:** unassigned

## Files touched

- `apple/Package.swift` — four targets: `Contracts`, `RuntimeCore` (→ Contracts),
  `Providers` (→ Contracts), `Hosts` (→ RuntimeCore + Providers + Contracts), plus
  a `ContractsTests` test target. Provisional platforms `.macOS(.v14) / .iOS(.v17)`.
- `apple/Sources/RuntimeCore/RuntimeCore.swift`,
  `apple/Sources/Providers/Providers.swift` (the five provider protocols),
  `apple/Sources/Hosts/Hosts.swift` — layer placeholders establishing the graph.
- `apple/README.md` — layout + build/test + the layer rule.

## Verification artifacts

`cd apple && swift build` (Swift 6.3 / Xcode 26.5):

```
Compiling Contracts (Models/JSONValue/Enums/Coding) ... Emitting module Contracts
Compiling Providers ... Emitting module RuntimeCore ... Compiling RuntimeCore
Emitting module Hosts ... Compiling Hosts
Build complete! (3.50s)
```

Layer rule — no UI imports in the core layers:

```
$ grep -rn -E "import (SwiftUI|UIKit|WebKit)" Sources/Contracts Sources/RuntimeCore Sources/Providers
(none — Contracts/RuntimeCore/Providers are UI-free)
```

## Acceptance criteria — re-checked

- [x] `Package.swift` declares the four targets; the package resolves and builds.
- [x] Dependency graph is RuntimeCore→Contracts, Providers→Contracts,
  Hosts→(RuntimeCore, Providers, Contracts); Contracts depends on nothing
  platform-specific.
- [x] Contracts/RuntimeCore/Providers import no SwiftUI/UIKit/WebKit — grep guard
  above (the build also links them with no UI framework).
- [x] `swift build` succeeds (green log).
- [x] Deployment floor + the package shape recorded (Package.swift comments +
  `apple/README.md`).

## Deviations from plan

- `Hosts` is a Swift **library** placeholder (not yet an iOS app target) so the
  package builds + tests on the macOS host; the real SwiftUI app + Xcode project
  arrive with Phases 8–9. A standalone `.xcworkspace` was not created — the SPM
  package IS the source of truth (the deferred "workspace shape" decision, resolved
  toward SPM-first).
- The build-fails-if-core-imports-SwiftUI guard is currently a grep (durable CI
  form is HSM-1-03).

## Follow-ups

HSM-1-03 (CI) makes the grep guard a CI step; HSM-1-04 adds the iOS app target +
the Gate-1 simulator launch.
