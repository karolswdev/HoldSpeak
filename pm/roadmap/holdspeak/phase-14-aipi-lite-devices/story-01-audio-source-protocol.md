# HS-14-01 - AudioSource Protocol + RemoteAudioRecorder

- **Project:** holdspeak
- **Phase:** 14
- **Status:** done
- **Depends on:** HS-13-10
- **Unblocks:** HS-14-02, HS-14-04, HS-14-05, HS-14-06
- **Owner:** unassigned

## Problem

`holdspeak/audio.py:AudioRecorder` is currently the only audio-source
abstraction. It opens a `sounddevice.InputStream` and pushes float32
mono frames into an internal list, returning a 16k mono ndarray on
`stop_recording()`. The voice-typing path (`controller.py`) and the
meeting path (`MeetingRecorder`) both expect this concrete class.

Phase 14 needs to plug a different source — frames pushed over a
WebSocket from a remote device — into the same downstream pipeline.
The cleanest move is to extract the implicit interface into an
explicit `AudioSource` Protocol (or ABC), keep `AudioRecorder` as the
local-mic implementation, and add a sibling `RemoteAudioRecorder`
that consumes pushed PCM frames instead of opening a stream.

This is the riskiest substrate story for the phase: the Protocol
shape constrains every downstream story.

## Scope

- **In:**
  - Define `AudioSource` Protocol in `holdspeak/audio.py`. Minimal:
    `start_recording()`, `stop_recording() -> np.ndarray` (16k mono
    float32). Optional: `is_recording` property.
  - Make `AudioRecorder` declare conformance (either by Protocol
    structural typing or `class AudioRecorder(AudioSource)` if we
    pick ABC).
  - Add `RemoteAudioRecorder(AudioSource)` in a new module
    `holdspeak/device_audio.py`. It exposes `push(pcm_bytes: bytes)`
    that decodes int16 little-endian → float32, accumulates in a
    bounded internal buffer, and on `stop_recording()` returns the
    concatenated 16k mono ndarray (resamples if needed for symmetry
    with `AudioRecorder`'s fallback, even though the on-the-wire
    contract is 16k by spec).
  - Add `tests/unit/test_remote_audio_recorder.py` with the cases
    listed in the phase exit criteria.
  - Add a shared shape contract test (`tests/unit/test_audio_source_contract.py`)
    that runs the same scenarios against any `AudioSource`
    implementation passed in.

- **Out:**
  - `DeviceRegistry`, lifecycle, descriptor — HS-14-02.
  - WebSocket route, auth, handshake — HS-14-03 / HS-14-04.
  - Backpressure policy beyond a basic bounded buffer (the policy
    proper, with logging + observability, lives in HS-14-04).
  - Wiring this into `controller.py` or `MeetingRecorder` — HS-14-05 / 06.

## Acceptance Criteria

- [x] `holdspeak/audio.py` defines `AudioSource` Protocol with
  `start_recording()` and `stop_recording() -> np.ndarray`.
- [x] `AudioRecorder` continues to pass all existing tests
  unchanged.
- [x] `holdspeak/device_audio.py:RemoteAudioRecorder` implements
  `AudioSource` and accepts pushed PCM via `push(bytes)`.
- [x] `tests/unit/test_remote_audio_recorder.py` ≥ 6 cases green:
  start/stop round-trip; push-then-stop returns concatenation;
  buffer overflow drops oldest with logged warning; stop without
  start raises; bytes after stop are ignored; resample path
  produces 16k float32 when on-wire rate differs.
- [x] `tests/unit/test_audio_source_contract.py` runs the shape
  contract against both implementations.
- [x] No regression in existing audio tests:
  `uv run pytest tests/unit/test_audio_*.py` green.

## Test Plan

- Unit: `uv run pytest tests/unit/test_remote_audio_recorder.py`,
  `tests/unit/test_audio_source_contract.py`,
  existing `tests/unit/test_audio_recorder.py`.
- Integration: n/a (pure unit story; integration lands in HS-14-04).
- Manual: n/a.

## Notes

- **Protocol vs ABC.** Recommend Protocol (structural typing) over
  ABC — keeps `AudioRecorder` unchanged and lets future test
  doubles satisfy the type without inheritance ceremony.
- **Why decode int16 → float32 inside `RemoteAudioRecorder`.** The
  rest of the pipeline (Whisper, the `_linear_resample_mono` helper,
  pydub-equivalents) all expect float32. Doing the conversion at
  the source boundary keeps downstream code identical.
- **Cross-repo coordination.** AIPI-Lite-side bridge will need to
  produce 16k mono int16 frames. `aipi.yaml` already configures the
  i2s mic at 16k mono 16-bit. No firmware changes required for
  this story.
