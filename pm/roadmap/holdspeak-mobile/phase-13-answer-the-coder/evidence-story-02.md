# Evidence — HSM-13-02 (Native voice-note capture → dictation)

**Date:** 2026-06-20 · **Status:** done

The iPad's native voice-note answer path, as a Runtime-Core view-model:
record → transcribe on-device → review/edit → deliver via the HSM-13-01 inject path.
The owner's hard line holds structurally — **nothing is delivered before an explicit
`send()`**.

## What shipped

- `apple/Sources/RuntimeCore/Companion/VoiceNoteComposer.swift` — a state machine
  (`VoiceNoteState`: idle → recording → transcribing → review → delivering →
  delivered / failed) over three seams it does **not** own:
  - **capture:** the Phase-2 `IAudioCapture` (press-to-talk; chunks accumulate
    on-device under a lock).
  - **transcribe:** a `@Sendable ([AudioChunk]) -> ITranscriber` **factory** — built
    over the captured audio because `ITranscriber.transcribe()` reads the audio it was
    constructed with. No second transcription path is introduced; the MLX
    single-executor-thread discipline stays inside the transcriber.
  - **deliver:** the HSM-13-01 `IDesktopClient.sendRemoteDictation(text:)`.
- `editText(_:)` allows a quick review/edit; `send()` is deliver-on-command and a
  no-op outside `.review`; an empty note is guarded and never reaches the coder.
- `egressLabel` mirrors the client's honest `local + LAN → <host>` (capture stays
  local; only the payload travels).

## Tests (ran)

`swift test` → **117 passed / 6 skipped / 0 failed** (+10). New
`VoiceNoteComposerTests` (fake capture / transcriber / desktop seams):

- `testHappyPath_captureTranscribeReviewDeliver` — full flow; the captured chunks
  reach the transcriber; the reviewed text is what ships.
- `testTranscriptionNeverAutoSends` — recognition lands in `.review` and delivers
  nothing on its own (`remoteSent` empty).
- `testEditChangesTheDeliveredPayload` — the edited text is what ships, not the raw
  recognition.
- `testTranscribeFailure_*` / `testCaptureStartFailure_*` /
  `testDeliveryFailure_unreachableDesktop_*` — each leg fails to its own stage and
  delivers nothing.
- `testEmptyRecognition_guardsTheSend`, `testSendFromIdleIsNoOp`,
  `testEditOutsideReviewIsNoOp`, `testEgressLabelMirrorsTheClient`.

## Deferred (by design)

The **live on-device walkthrough** — speak a real voice note on the iPad, confirm
on-device Whisper recognition, review, and deliver into a live coder session — folds
into **HSM-13-04** (the Track N gate), exactly as this story's test plan states. The
view-model + seam wiring are ready for it; the SwiftUI surface lands with the
Companion shell (HSM-12-03) / the gate.
