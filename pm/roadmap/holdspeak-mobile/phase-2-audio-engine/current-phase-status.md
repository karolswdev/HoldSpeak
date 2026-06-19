# Phase 2 — Audio Engine

**Status:** in-progress (HSM-2-02/03 done 2026-06-18; HSM-2-01 authored +
iOS-type-checked, device-pending; HSM-2-04 = the 1-hour hardware gate). Track C of
the Council Implementation Charter. The first Layer-3 provider: the `IAudioCapture`
implementation the mobile runtime records meetings and dictation through, and the
WAV export that feeds the Phase-3 transcriber.

**Last updated:** 2026-06-18 (**HSM-2-02 + HSM-2-03 done** — `AudioChunk` +
bounded `AudioAccumulator` and the 16 kHz-mono-PCM16 `WavWriter`, host-tested
(`swift test` 8/8, header re-parsed + capture→WAV pipeline). **HSM-2-01** capture
service (`AVAudioEngine`/`AVAudioSession`, format conversion, interruption +
route-change handling) authored + **iOS-type-checked** (exit 0); in-progress until
device-verified. **HSM-2-04** is the 1-hour continuous-recording gate — needs real
hardware + a mic, deferred).

## Goal

Build the mobile audio engine behind the `IAudioCapture` provider abstraction:
an `AudioCaptureService` over `AVAudioEngine` + `AVAudioSession` that captures
streaming audio (`AudioChunk`), records to disk, and exports 16 kHz mono PCM WAV
— the format the downstream transcriber (Phase 3, WhisperKit) wants. The phase
passes when the engine survives a 1-hour continuous recording without drop,
glitch, or memory growth (Track C gate / Quality Gate 2 — Audio Stability).

## Scope

- **In:** the `AudioCaptureService` + `AudioSession` capture seam over
  `AVAudioEngine`/`AVAudioSession`, behind the `IAudioCapture` provider contract,
  with interruption and route-change handling (HSM-2-01); the `AudioChunk`
  streaming model + buffering for downstream transcription (HSM-2-02); on-disk
  recording + WAV export at 16 kHz mono PCM (HSM-2-03); the 1-hour continuous
  recording stability closeout (HSM-2-04).
- **Out:** transcription of any kind — WhisperKit, chunk-to-text, latency
  (Phase 3). Persisting recordings as `Meeting`/`Segment` rows (Phase 4). Any
  UI for record/stop/level-metering (Phases 8–9). Speaker diarization. The
  `IAudioCapture` contract *shape* is fixed in the contract package (Phase 0 /
  Phase 1); this phase implements it, it does not redefine it.

## Exit criteria (evidence required)

- [ ] `AudioCaptureService` captures live mic audio via `AVAudioEngine` behind
      the `IAudioCapture` provider abstraction; an `AVAudioSession` is configured
      for record, and interruptions (phone call, Siri) and route changes
      (headphones in/out, Bluetooth) are handled without crashing or
      silently dropping capture (HSM-2-01).
- [ ] Captured audio is delivered as a stream of `AudioChunk` values with stable
      format and ordering, buffered so a downstream consumer that stalls does not
      drop samples or unbound memory (HSM-2-02).
- [ ] A recording writes to disk and exports a valid WAV file at **16 kHz mono
      PCM** — the transcriber contract — verified by re-reading the file's header
      and sample rate (HSM-2-03).
- [ ] **Track C gate / Quality Gate 2:** a **1-hour continuous recording**
      completes on a Tier-1 device with no dropped buffers, no audio glitches in
      the exported WAV, and bounded memory (no leak/unbounded growth over the
      hour) — recorded as a device trace (HSM-2-04).

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HSM-2-01 | Audio session + capture seam | in-progress | [story-01](./story-01-audio-session-capture-seam.md) | — |
| HSM-2-02 | AudioChunk streaming | done | [story-02](./story-02-audio-chunk-streaming.md) | [evidence-02](./evidence-story-02.md) |
| HSM-2-03 | Recording + WAV export (16 kHz mono PCM) | done | [story-03](./story-03-recording-wav-export.md) | [evidence-03](./evidence-story-03.md) |
| HSM-2-04 | 1-hour stability closeout (Gate 2) | backlog | [story-04](./story-04-one-hour-stability-closeout.md) | — |

## Where we are

The testable core of Track C is done. `AudioChunk` + the bounded
`AudioAccumulator` (HSM-2-02) and the 16 kHz-mono-PCM16 `WavWriter` (HSM-2-03) are
host-tested (`swift test` 8/8: the WAV header is re-parsed to assert
PCM/mono/16000/16-bit/length, and a fake-capture → chunks → accumulator → WAV
pipeline runs end to end). The live `AudioCaptureService` (HSM-2-01,
`AVAudioEngine`/`AVAudioSession` + `AVAudioConverter` to the canonical format +
interruption/route-change handling) is authored and **iOS-type-checked** against
the simulator SDK (exit 0), exercised host-side through a `FakeAudioCapture`; it
stays in-progress until live mic + interruption behavior is verified on a device.
**The only remaining Phase-2 work is hardware-gated:** HSM-2-01's device
verification and HSM-2-04 (the 1-hour continuous-recording Gate 2) both need real
Tier-1 hardware + a mic. Next authorable step is Phase 3 (Whisper Runtime), which
consumes this `AudioChunk` stream; the Phase-2 hardware closeouts run when a device
is available.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| `AVAudioEngine` delivers float32 at the hardware rate (44.1/48 kHz), not the 16 kHz mono PCM the transcriber wants | high | Resolve sample-rate + format conversion once in the capture seam (`AVAudioConverter`), not per-consumer; pin the canonical output format in HSM-2-02 | A consumer needs a second output format — fix the converter, don't fork the stream |
| Interruptions/route changes (call, Siri, headphone unplug) silently kill the engine mid-recording | high | HSM-2-01 handles `AVAudioSession` interruption + route-change notifications explicitly with resume; HSM-2-04 forces them during the 1-hour run | The engine cannot resume after an interruption without losing the in-progress recording — escalate the session strategy before the gate |
| 1-hour capture leaks memory or drops buffers under backpressure (the Gate-2 failure mode) | medium | Bounded ring buffer + measured per-chunk allocation in HSM-2-02; the gate run (HSM-2-04) watches memory and dropped-buffer counters | Memory grows unbounded or buffers drop over a sustained run — fix buffering before claiming the gate |
| iOS suspends/throttles the app in background, truncating long recordings | medium | Decide the background-audio posture (background mode vs foreground-only) in HSM-2-01; the 1-hour run states which posture it proves | The gate only passes foreground but the product needs background recording — re-scope with the owner |
| No physical Tier-1 device available for the 1-hour gate | low | Run HSM-2-04 on real hardware (iPad Air/Pro M4 or iPhone 17 Pro Max); simulator audio does not prove the gate | The gate is run only on the simulator — it does not count; park HSM-2-04 until a device is available |

## Decisions made (this phase)

- 2026-06-18 — WAV export targets **16 kHz mono PCM** because that is what the
  Phase-3 transcriber (WhisperKit) consumes; the capture seam owns the
  conversion from the hardware format — owner charter note for Track C.
- 2026-06-18 — The Track C gate ("1-hour continuous recording") gets a dedicated
  closeout story (HSM-2-04) rather than being a footnote on HSM-2-03, so the
  Audio-Stability gate is proven as device evidence — roadmap-builder convention.

## Decisions deferred

- Background-audio posture (background audio mode vs foreground-only recording) —
  trigger: HSM-2-01 — default: configure for foreground capture; revisit if the
  iPhone pocket workflow (Phase 9) needs screen-off recording.
- WAV file location + naming on disk and its handoff to persistence — trigger:
  HSM-2-03 — default: a temp/app-support recordings directory; Phase 4 owns the
  durable `Meeting` association.
- Whether `AudioChunk` carries 16 kHz converted samples or hardware-rate samples
  with conversion deferred to export — trigger: HSM-2-02 — default: the stream
  carries the canonical 16 kHz mono format so the transcriber and the WAV writer
  share one path.
