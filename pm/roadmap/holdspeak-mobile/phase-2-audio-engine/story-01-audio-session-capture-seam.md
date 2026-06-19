# HSM-2-01 — Audio session + capture seam

- **Project:** holdspeak-mobile
- **Phase:** 2
- **Status:** in-progress
- **Depends on:** HSM-1-01 (the Xcode workspace + SPM layout + the `IAudioCapture`
  provider contract from Phase 1)

## Progress (2026-06-18)

`AudioCaptureService` (iOS) authored in `apple/Sources/Providers/Audio/`: an
`AVAudioEngine` input tap converting the hardware format to 16 kHz mono PCM16 via
`AVAudioConverter`, streaming `AudioChunk`s through the enriched `IAudioCapture`
seam, with `AVAudioSession` `.record` config and interruption + route-change
handlers (pause/resume + restart). **iOS-type-checked** against the iphonesimulator
SDK (exit 0, no warnings); the streaming seam is exercised host-side by a
`FakeAudioCapture` pipeline test. Stays in-progress until **live mic + real
interruption/route-change behavior is verified on a device** (defers with the
Track-C hardware gate, HSM-2-04).
- **Unblocks:** HSM-2-02, HSM-2-03
- **Owner:** unassigned

## Problem

The mobile runtime cannot record anything until there is a live capture path. It
must run through `AVAudioEngine` and a correctly configured `AVAudioSession`, and
it must survive the things that happen on a phone during a meeting: an incoming
call, Siri, headphones unplugged, a Bluetooth headset connecting. If the capture
seam is wired directly to the engine, the rest of the runtime couples to UIKit
audio types and the charter's Layer-3 abstraction (`IAudioCapture`) is violated.

## Scope

- **In:** the `AudioSession` type that configures and activates an
  `AVAudioSession` for recording; the `AudioCaptureService` that drives an
  `AVAudioEngine` input tap and exposes capture *only* through the `IAudioCapture`
  provider protocol defined upstream; explicit handling of `AVAudioSession`
  interruption notifications (began/ended + resume) and route-change
  notifications (e.g. old-device-unavailable on headphone unplug); mic
  permission request + denied state surfaced through the provider.
- **Out:** the `AudioChunk` model and buffering (HSM-2-02). WAV/file writing
  (HSM-2-03). The 1-hour endurance run (HSM-2-04). Any recording UI. Defining the
  `IAudioCapture` protocol shape (it is consumed here, owned upstream).

## Acceptance criteria

- [ ] `AudioCaptureService` conforms to the `IAudioCapture` provider protocol; no
      caller of the service references `AVAudioEngine`/`AVFoundation` types
      directly.
- [ ] `AudioSession` configures an `AVAudioSession` record category and activates
      it; mic-permission-denied is surfaced as a defined provider error, not a
      crash.
- [ ] Starting capture installs an input tap on the engine and begins delivering
      audio; stopping cleanly removes the tap and deactivates the session.
- [ ] An `AVAudioSession` interruption (simulated call / Siri) is handled: capture
      pauses on `began` and resumes on `ended` with the `.shouldResume` option,
      without crashing or leaving a dead engine.
- [ ] A route change (headphones unplugged, Bluetooth connect/disconnect) is
      handled without crashing and without silently dropping into a stopped state
      unnoticed — the provider reports the state.
- [ ] The background-audio posture (foreground-only vs background mode) is decided
      and recorded in Notes, and the configuration matches that decision.

## Test plan

- **Device:** on a Tier-1 device, start capture and confirm audio is flowing
  (level/sample callback fires); trigger Siri or place a call to fire an
  interruption and confirm resume; unplug/replug wired headphones and toggle a
  Bluetooth headset to fire route changes; deny mic permission and confirm the
  provider error path.
- **Simulator:** start/stop lifecycle and tap install/remove; permission-denied
  state. (Interruptions/route changes are device-only — they do not prove on the
  simulator.)
- **Unit:** the `IAudioCapture` conformance and state machine (idle → capturing →
  interrupted → capturing → stopped) with the engine/session behind a seam so the
  transitions are testable without hardware.

## Notes / open questions

- Background-audio is a charter-level open question (the iPhone pocket workflow,
  Phase 9, may need screen-off recording). Default here: foreground capture;
  record the decision so HSM-2-04's gate run states which posture it proves.
- The input tap delivers float32 at the hardware sample rate (often 48 kHz). This
  story exposes raw capture; the conversion to the canonical 16 kHz mono format
  is HSM-2-02's call — flag the chosen format boundary so the two stories agree.
- `IAudioCapture`'s exact signatures come from Phase 1's contract package; if it
  is not yet defined when this story starts, that is a hard block — record it and
  do not invent a private protocol that later forks the contract.
