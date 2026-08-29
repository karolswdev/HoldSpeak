# HoldSpeak for Apple platforms

This directory contains the Swift runtime, native iPhone/iPad application
sources, and device-build tooling for HoldSpeak. The architectural map is
[`ARCHITECTURE.md`](./ARCHITECTURE.md); historical roadmap and contract rationale
live under [`../pm/roadmap/holdspeak-mobile/`](../pm/roadmap/holdspeak-mobile/).

## Layout

```text
Sources/
  Contracts/       language-neutral Codable contracts
  RuntimeCore/     meeting, artifact, routing, persistence, and sync logic
  Providers/       audio, transcription, storage, endpoint, and sync adapters
  InferenceLlama/  llama.cpp-backed on-device inference adapter
  Hosts/           shared host-facing Swift code
App/               native SwiftUI app and harness entry points
Tests/             package tests for all runtime layers
scripts/           generated-Xcode-project and physical-device workflows
```

Only host/application code imports SwiftUI or UIKit. `Contracts`, `RuntimeCore`,
and `Providers` remain UI-independent; the package and layer-guard tests enforce
that boundary.

The supported deployment floors declared by `Package.swift` are macOS 14 and
iOS 17. Swift tools version 6.0 is required.

## Build and test the runtime

```bash
cd apple
swift build
swift test
```

The contract tests read the golden wire fixtures under the mobile roadmap, so
Swift and Python are checked against the same serialized shapes. Tests needing
a real model, endpoint, or device are opt-in; see
[`ARCHITECTURE.md`](./ARCHITECTURE.md#testing).

## Run the native app

The primary physical-device workflow generates a signed Xcode project under the
gitignored `apple/build/` directory, builds it, installs it, and launches it:

```bash
cd apple
scripts/meeting-capture-device.sh [device-udid]
```

One-time prerequisites are an Xcode account with an accepted developer
agreement, a trusted/registered device with Developer Mode enabled, and valid
automatic signing. The script prefers a connected iPad, then an iPhone. Review
the script before running it: as part of signing recovery it clears cached local
provisioning profiles so Xcode can regenerate them for the selected device.

Other scripts are purpose-built harnesses rather than alternate production app
roots:

- `gate1-launch.sh` and `gate1-device.sh`: minimal shell smoke tests.
- `harness-device.sh`: endpoint/inference harness.
- `local-harness-device.sh`: on-device inference harness.
- `speak-harness-device.sh`: speech/dictation harness.
- `push-model-device.sh`: copy a GGUF into an installed app container.

Each device script prints its exact prerequisites and accepted arguments.

## Mesh serving

The native app can serve its active model to the paired HoldSpeak mesh. Enable
**Serve my models to the mesh** in Settings. Serving is off by default and
foreground-only: while enabled, `MeshServeWorker` claims signed work from the
hub and executes it with the device's own model and Keychain-held endpoint key.
The model and key stay on the device. Closing the app makes the node offline and
later runs refuse with the node named.

## Current status

The Swift package and native app are both implemented. `App/MeetingCapture/`
contains the flagship desk, recording/review, models, sync, companion, and mesh
surfaces; the remaining app entry points are focused test and compatibility
harnesses. Treat `pm/` as historical planning/evidence, not as the current
product-status reference.
