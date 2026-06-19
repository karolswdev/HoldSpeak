# HSM-3-01 — WhisperKit transcriber behind ITranscriber

- **Project:** holdspeak-mobile
- **Phase:** 3
- **Status:** in-progress
- **Depends on:** HSM-1-01, HSM-2-03
- **Unblocks:** HSM-3-02, HSM-3-04
- **Owner:** unassigned

## Progress (2026-06-18)

The seam around WhisperKit is built + host-tested: `TranscriberConfig` (language
"auto" default + `normalizedLanguage()`), `WhisperModelPolicy.defaultModel(for:)`
(iPhone→Base / iPad→Small, charter local-model strategy), and the transcription→
`Segment` mapping (HSM-3-04). The **WhisperKit dependency + the WhisperKit-backed
`ITranscriber` implementation are deferred**: pulling WhisperKit + a model into
this headless env buys only a compile (real transcription needs a model + audio on
a device), so it lands as device work to keep the package + CI lean. Stays
in-progress until the WhisperKit impl + an on-device transcription run.

## Problem

The mobile runtime needs a real transcription provider, but Layer 3 only defines
the `ITranscriber` abstraction — there is no implementation. WhisperKit is the
charter's chosen technology (Track D). Without a transcriber wired behind the
abstraction and loading the right per-device model, nothing downstream (realtime,
chunk, segmentation) has anything to run on.

## Scope

- **In:** a `WhisperKitTranscriber` type conforming to the `ITranscriber`
  abstraction (the protocol from Layer 3 / Phase 1); WhisperKit model loading with
  the per-device default from the local-model strategy — Whisper Base on iPhone,
  Whisper Small on iPad; a load/ready lifecycle (cold load, ready signal,
  teardown) the host can drive; a smoke transcription of a known fixture clip to
  prove the model decodes.
- **Out:** the realtime streaming and chunk entry points (HSM-3-02 — this story
  proves the provider loads and decodes, but those two operating modes are their
  own story). Language selection (HSM-3-03). Segment emission (HSM-3-04). Any
  plugged-in larger-variant upgrade (deferred in the phase status).

## Acceptance criteria

Checklist. Merge gate. Each item must be verifiable by reading code or running a
command:

- [ ] A `WhisperKitTranscriber` exists and conforms to the `ITranscriber`
      abstraction (compiles against the protocol; no provider-specific types leak
      into the abstraction).
- [ ] On an iPhone target the loaded model is Whisper Base; on an iPad target it
      is Whisper Small — selection is by device tier, not hard-coded to one.
- [ ] The provider exposes a load/ready/teardown lifecycle and surfaces load
      failure as a typed error, not a crash.
- [ ] A known fixture audio clip transcribes to expected text in a test
      (proves the WhisperKit pipeline decodes end-to-end behind the abstraction).
- [ ] No business-logic type depends on WhisperKit — the dependency stops at the
      provider (charter architecture principle).

## Test plan

- Unit: provider conformance + per-device model selection logic (Base vs Small by
  tier) — run via the Phase-1 test harness (`swift test` / the workspace scheme).
- Integration: load the model on a Tier-1 device and transcribe a committed
  fixture clip; assert the text matches the expected transcript.
- Manual / device: cold-load on a Tier-2 iPhone 17 Pro Max and confirm the Base
  model loads without OOM; note load time.

## Notes / open questions

- The `ITranscriber` protocol shape comes from Phase 1 (HSM-1-01). If it lacks a
  load/ready/teardown surface this story needs, raise it against Phase 1 — the
  abstraction wins; record the gap here, don't fork it.
- Memory rule: bank on WhisperKit per the charter; no pre-measurement spike
  comparing transcription engines — just build it.
- The plugged-in larger-iPad-variant question is parked in the phase status
  ("Decisions deferred"); ship Base/Small only here.
