# HoldSpeak Mobile (Apple)

The Apple runtime of the HoldSpeak ecosystem (iPhone/iPad). Roadmap + canon live
at [`../pm/roadmap/holdspeak-mobile/`](../pm/roadmap/holdspeak-mobile/); this is
the Swift codebase that roadmap builds.

## Layout (charter four-layer architecture)

```
Sources/
  Contracts/    # Layer 1 — language-neutral schema as Swift Codable types (Foundation only)
  RuntimeCore/  # Layer 2 — meeting/artifact/MIR engines, persistence, sync (no UI)
  Providers/    # Layer 3 — ITranscriber / ILLMProvider / IAudioCapture / IStorage / ISyncProvider
  Hosts/        # Layer 4 — iPad/iPhone SwiftUI apps (the only UI layer)
Tests/
  ContractsTests/  # round-trips the Phase-0 golden fixtures
```

**Layer rule (enforced):** `Contracts`, `RuntimeCore`, and `Providers` import no
SwiftUI/UIKit/WebKit — business logic does not depend on UI (charter Architecture
§Principle).

## Build & test

```bash
cd apple
swift build      # compiles all four layers (macOS host)
swift test       # round-trips the Phase-0 fixtures through Swift Codable
```

The `Contracts` types are written against
[`../pm/roadmap/holdspeak-mobile/contracts/`](../pm/roadmap/holdspeak-mobile/contracts/)
(the schemas + serialization contract + golden fixtures). The tests read those
same fixtures, so the Swift and Python runtimes are validated against one source.

## Status

Phase 1 (Mobile Foundation): the SPM package + `Contracts` types are in
(HSM-1-01/02). CI (HSM-1-03) and the on-device launch closeout (HSM-1-04) are the
remaining Phase-1 stories. The SwiftUI app target / Xcode project arrives with the
iPad (Phase 8) and iPhone (Phase 9) experience phases; `Hosts` is a placeholder
until then so the package builds + tests on the macOS host.

Provisional iOS floor: 17 — revisit at Phase 5 (if Core ML wins, `MLState` moves
it to 18; PROGRAM-RISKS P6).
