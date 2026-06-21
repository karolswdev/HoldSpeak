# HSM-13-02 — Native voice-note capture → dictation

- **Project:** holdspeak-mobile
- **Phase:** 13
- **Status:** done (2026-06-20 — the `VoiceNoteComposer` capture→transcribe→review→
  deliver view-model ships, host-tested over fake seams; live on-device run folds
  into HSM-13-04. See [evidence-story-02](./evidence-story-02.md))
- **Depends on:** HSM-13-01, HSM-2-01 (capture), HSM-3-01 (Whisper)
- **Unblocks:** HSM-13-04
- **Owner:** unassigned

## Problem

The owner's words: "use our **native functionality** to send back a voice note."
The answer to the coder should be spoken on the iPad and captured with the device's
own capability — not typed into a box. This story is the native voice-note path:
press to speak, capture on-device, transcribe with Whisper, and hand the text to
the inject path. It is where the iPad "standing its own ground" pays off in the
companion flow — the capture and transcription are the iPad's, the delivery is the
server's.

## Scope

- **In:** a native voice-note capture on the iPad — press-to-talk capture (reuse
  the Phase-2 `IAudioCapture`), on-device Whisper transcription (reuse the Phase-3
  transcriber), a quick review/edit of the recognized text, then deliver via the
  HSM-13-01 client method. The capture is on-device; only the resulting dictation
  payload leaves (honest egress label).
- **Out:** the inject endpoint itself (HSM-13-01). The Companion board / which
  session it targets (HSM-13-03 supplies the target). On-device meeting capture
  (Phase 8 — this is a short voice note, not a meeting). A typed-answer fallback
  (deferred; voice-note first).

## Acceptance criteria

- [x] Press-to-talk captures a voice note on the iPad via the Phase-2 capture seam
      and transcribes it with the Phase-3 Whisper transcriber, fully on-device.
      *(`VoiceNoteComposer` drives `IAudioCapture` → an `ITranscriber` built over the
      captured `AudioChunk`s; host-tested that the captured chunks reach the
      transcriber. The live on-device capture+Whisper run folds into HSM-13-04, per
      this story's test plan.)*
- [x] The recognized text is shown for a quick review/edit before anything is sent
      (never auto-sent from recognition). *(`stopAndTranscribe()` always lands in
      `.review`; `editText(_:)` mutates it; `send()` is separate —
      `testTranscriptionNeverAutoSends` / `testEditChangesTheDeliveredPayload`.)*
- [x] On send, the text is delivered through the HSM-13-01 client method; the
      egress label is honest (capture stays local; the dictation payload goes to the
      paired server). *(`send()` calls `IDesktopClient.sendRemoteDictation`;
      `egressLabel` mirrors the client's `local + LAN → <host>`.)*
- [x] The capture path reuses the on-device seams (no new transcription/capture
      engine); a view-model drives capture → transcribe → review → deliver without
      UIKit. *(Pure RuntimeCore; a transcriber **factory** over the existing
      `ITranscriber` — no second transcription path; the MLX single-executor-thread
      discipline stays inside the transcriber.)*

## Test plan

- Unit: the capture → transcribe → review → deliver view-model over fake
  capture/transcribe/client seams → correct state flow; nothing is delivered before
  an explicit send.
- Device (folded into HSM-13-04): speak a real voice note on the iPad, confirm
  on-device recognition, review, and deliver.

## Notes / open questions

- MLX threading rule still applies on-device: all MLX/Whisper work stays pinned to
  the single executor thread (the standing `_MlxTranscriber` discipline) — do not
  introduce a second transcription path here.
- The rich-pipeline transform happens server-side (HSM-13-01); the iPad sends clean
  recognized text. Keep the client thin — capture + recognize + review + post.
- Voice-note first per the owner's scenario; a typed fallback is cheap to add later
  once the inject path exists (Decisions deferred, phase status).
