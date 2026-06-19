# Evidence — HSM-1-04 — Gate-1 launch (+ test harness)

- **Shipped:** 2026-06-18
- **Commit:** Phase-1 Gate-1 bundle on `main` (see commit message)
- **Owner:** unassigned

## Files touched

- `apple/App/HoldSpeakApp.swift` — a minimal SwiftUI runtime shell (shows the
  real `HoldSpeakContracts.contractVersion`).
- `apple/App/Info.plist` — universal (iPhone + iPad) app bundle metadata.
- `apple/scripts/gate1-launch.sh` — compiles the shell **with the Contracts
  sources**, bundles a `.app`, and boots + installs + launches on an iPhone and an
  iPad simulator, capturing a screenshot each.
- `pm/roadmap/holdspeak-mobile/phase-1-mobile-foundation/gate1-iphone17promax.png`,
  `gate1-ipadpro-m5.png` — the launch screenshots (Gate-1 evidence).

## Verification artifacts

Real on-simulator launch (iOS 26.5 runtime; the charter's Tier-2 + Tier-1
targets), via `apple/scripts/gate1-launch.sh`:

```
== iPhone 17 Pro Max ==   ... bootstatus Finished
dev.holdspeak.mobile: 18791            # launched (PID)
screenshot: build/launch-iPhone_17_Pro_Max.png
== iPad Pro 13-inch (M5) ==  ... bootstatus Finished
dev.holdspeak.mobile: 20110            # launched (PID)
screenshot: build/launch-iPad_Pro_13-inch__M5_.png
== Gate 1: launched on iPhone + iPad ==
```

The screenshots show the shell rendered — title + "Runtime foundation — Phase 1"
+ "contracts v0.1.0" (the last read from the `Contracts` layer compiled into the
app, so the launch exercises real contract code, not a literal).

## Acceptance criteria — re-checked

- [x] The app launches on an iPhone destination AND an iPad destination —
  iPhone 17 Pro Max (PID 18791) + iPad Pro 13-inch M5 (PID 20110), screenshots
  committed. A build-only log is explicitly NOT the evidence; these are running
  processes with rendered UI.
- [x] The test harness runs (`swift test` 5/5, HSM-1-02) and the launch is
  scripted + repeatable (`gate1-launch.sh`).
- [x] Launch artifacts committed (the two PNGs).
- [x] Simulator vs. device stated: this is the iOS 26.5 **simulator** for both
  device classes; a physical-device run is the stronger proof, deferred to where
  hardware lands.

## Deviations from plan

- The launchable shell is a script-built `.app` (compiling Contracts + the app
  sources directly against the simulator SDK), NOT a full Xcode app project /
  `Hosts` SwiftUI app — that proper app target arrives with Phases 8–9. For Gate 1
  ("application launches on iPhone + iPad") a rendered launch on both device
  classes is the bar, and it is met.

## Follow-ups

A physical-device launch when Tier-1/Tier-2 hardware is available; the full
SwiftUI `Hosts` app + Xcode project in Phases 8 (iPad) / 9 (iPhone).
