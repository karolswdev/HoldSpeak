# HS-14-05 - Voice-Typing Path Consumes Remote Audio

- **Project:** holdspeak
- **Phase:** 14
- **Status:** done
- **Depends on:** HS-14-04
- **Unblocks:** HS-14-08
- **Owner:** unassigned

## Problem

`controller.py` orchestrates the hold-to-record gesture for voice
typing: hotkey-down opens the recorder, hotkey-up stops it, the
captured ndarray flows into `Transcriber` and then `text_processor`.
Today the recorder is hard-wired to `AudioRecorder` (local mic).

Phase 14 needs the same flow to fire when a registered device
sends `{type: "start"}` / `{type: "stop"}` over the WebSocket
without a hotkey involved at all. The simplest mental model: the
device acts like a remote hotkey + remote mic combined, and the
existing controller stays mostly unchanged.

## Scope

- **In:**
  - Refactor the controller's recorder ownership: instead of
    instantiating `AudioRecorder` directly, accept an
    `AudioSource` from a small factory hook (e.g.,
    `controller.set_audio_source(source)`) that web_server can
    set per-press for device-driven sessions.
  - In `device_audio_ws.py`, the dispatch loop's `start` /
    `stop` JSON messages call into the controller's
    voice-typing entry points using the device's
    `RemoteAudioRecorder` as the source.
  - Resulting transcript is typed via the same `text_processor`
    pipeline as a hotkey-driven session — no new typing path.
  - `tests/integration/test_voice_typing_via_device.py`: end-to-
    end through the WS, fake STT, asserts the transcript flows
    through `text_processor` (mock the actual keyboard typer).

- **Out:**
  - Multiple concurrent voice-typing sessions across devices —
    one device at a time for now; second device's start arrives
    while another session is active gets rejected with a
    typed error code.
  - Meeting path — HS-14-06.
  - Status push-back to the device's LCD ("Listening...",
    "Thinking...") — HS-14-07.

## Acceptance Criteria

- [x] Controller no longer instantiates `AudioRecorder`
  directly; accepts an `AudioSource` via factory.
- [x] `AudioRecorder` continues to be the default for
  hotkey-driven sessions; behavior unchanged.
- [x] Device-initiated `start` → recorder starts;
  device-initiated `stop` → recorder stops, transcript flows
  through the same downstream pipeline.
- [x] Concurrent device session attempt while a hotkey or
  device session is active is rejected (typed error to the
  device; no impact on the active session).
- [x] `tests/integration/test_voice_typing_via_device.py`
  green; existing voice-typing tests stay green.

## Test Plan

- Unit: covered indirectly via integration; no new pure-unit
  cases needed beyond mock setups.
- Integration:
  `uv run pytest tests/integration/test_voice_typing_via_device.py`,
  existing
  `uv run pytest tests/integration/test_voice_typing.py`.
- Manual: AIPI-Lite bridge connected; press the device button,
  speak a sentence, release — text appears in the focused window.

## Notes

- Why a factory hook vs inheriting / subclassing the
  controller: minimal blast radius. The controller's logic
  about "press → start, release → stop, then transcribe" is
  shared; the source of the audio is the only delta.
- One-active-session-at-a-time is a deliberate v1 simplification.
  When/if multiple devices need to dictate concurrently, we
  surface that as a future story.
- Cross-repo: this is the moment the AIPI-Lite bridge stops
  doing its own STT/LLM/TTS. Coordinated story in the
  AIPI-Lite roadmap (AIPI-2).
