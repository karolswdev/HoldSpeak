# HSM-1-01 — Xcode workspace + four-layer SPM layout

- **Project:** holdspeak-mobile
- **Phase:** 1
- **Status:** backlog
- **Depends on:** HSM-0-03
- **Unblocks:** HSM-1-02, HSM-1-03, HSM-1-04
- **Owner:** unassigned

## Problem

There is no Apple-platform home for the mobile runtime yet, and the charter's
architecture is load-bearing: business logic must not depend on SwiftUI, UIKit, or
WebView. If the project starts as one big target with folders, that rule survives
only as a comment and rots on the first convenience import. The four layers
(Contracts / Runtime Core / Providers / Platform Hosts) have to be real,
separately-buildable boundaries from day one.

## Scope

- **In:** an Xcode workspace + a Swift Package (`Package.swift`) under the mobile
  source root (path settled with HSM-0-03's package-home decision) exposing four
  SPM targets — `Contracts`, `RuntimeCore`, `Providers`, `Hosts` — with a
  dependency graph where `RuntimeCore` and `Providers` depend on `Contracts`,
  `Hosts` depends on the lower layers, and none of `Contracts`/`RuntimeCore`/
  `Providers` link SwiftUI/UIKit/WebView. A minimal placeholder per target so each
  compiles. The deployment-target floor and workspace shape (per the deferred
  decisions) recorded in the package/README.
- **Out:** the actual Codable types (HSM-1-02 fills `Contracts`). Any audio,
  Whisper, persistence, inference, MIR, or UI feature code. The CI wiring
  (HSM-1-03) and the launch closeout (HSM-1-04). Authoring or changing the
  contract schemas themselves (Phase 0).

## Acceptance criteria

- [ ] `Package.swift` declares four targets — `Contracts`, `RuntimeCore`,
      `Providers`, `Hosts` — and the workspace opens and resolves in Xcode.
- [ ] The dependency graph is: `RuntimeCore` → `Contracts`; `Providers` →
      `Contracts`; `Hosts` → (`RuntimeCore`, `Providers`, `Contracts`); and
      `Contracts` depends on nothing platform-specific.
- [ ] `Contracts`, `RuntimeCore`, and `Providers` import no SwiftUI, UIKit, or
      WebView — demonstrable from the target's linked frameworks / a guard, not
      just from the source reading clean.
- [ ] `swift build` succeeds for the whole package (green log in evidence).
- [ ] The deployment-target floor and the workspace shape are recorded in the
      package README or `Package.swift` comments.

## Test plan

- Unit: `swift build` over the package → succeeds (green log). A minimal `swift
  test` target exists and runs (the substantive tests land in HSM-1-02/04).
- Integration: attempt to import `SwiftUI` from the `RuntimeCore` target → build
  fails (proves the layer boundary is enforced, not conventional); record the
  failure as evidence the guard works.
- Manual / device: open the workspace in Xcode, confirm it resolves and the four
  schemes/targets are present.

## Notes / open questions

- Package home: do not start until HSM-0-03 records where `holdspeak-contracts`
  lives — the `Contracts` target either vendors that package or references it.
- Workspace shape and iOS floor are deferred decisions on the phase status doc;
  this story is where they get settled and recorded.
- Charter wins on the dependency rule: if Xcode/SPM ergonomics tempt a shortcut
  that puts UI types in the core, take the more verbose split and note it here.
