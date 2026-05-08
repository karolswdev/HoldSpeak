# HS-14-01 evidence — AudioSource Protocol + RemoteAudioRecorder

## What shipped

- `holdspeak/audio.py` — added `AudioSource`, a
  `@runtime_checkable` `Protocol` over `start_recording()` and
  `stop_recording() -> np.ndarray`. Structural typing means
  `AudioRecorder` conforms with no inheritance change; existing
  `_FakeAudioRecorder`/`MockAudioRecorder` test doubles satisfy
  the protocol unchanged.
- `holdspeak/device_audio.py` — new module. `RemoteAudioRecorder`
  consumes pushed PCM frames via `push(pcm_bytes)`, decoding
  int16 little-endian → float32 (divide by 32768.0) into a
  bounded ring of frames. `start_recording()` resets the ring;
  `stop_recording()` returns mono float32 audio at the configured
  `sample_rate` (default 16 kHz, with a `_linear_resample_mono`
  fallback for non-16 k wire rates). Frames pushed before
  `start_recording()` or after `stop_recording()` are silently
  dropped — the `/api/devices/audio` WebSocket path (HS-14-04)
  may race the device's stop signal and we don't want to blow up
  the connection over a tail frame.
- Backpressure: bounded internal buffer with drop-oldest on
  overflow plus a `holdspeak.audio.remote` warning log carrying
  `dropped_samples`, `cap_samples`, `buffered_samples`,
  `max_buffer_seconds`, `wire_sample_rate` as `extra` fields.
  Story scope cap: this is the substrate; the per-device queue
  policy + `/api/runtime/status` integration land in HS-14-04.
- `RemoteAudioRecorderError` — symmetric to `AudioRecorderError`;
  raised on stop-without-start and on double-start.
- `tests/unit/test_remote_audio_recorder.py` — 12 cases (story
  required ≥6) covering: start/stop with no push returns empty
  float32; push-then-stop concatenates correctly; overflow drops
  the oldest frame and emits a structured warning; stop-without-
  start raises; double-start raises; bytes pushed during the
  stopped gap are ignored; bytes pushed before start are
  ignored; resample path produces ~16 k float32 from an 8 k
  wire rate; int16 decoding round-trips the −1.0 / 0.0 / +1.0
  edges; an odd trailing byte is dropped; empty push is a
  no-op; invalid constructor args raise `ValueError`.
- `tests/unit/test_audio_source_contract.py` — parametrized
  shape contract that runs against both `AudioRecorder` and
  `RemoteAudioRecorder`: `isinstance(src, AudioSource)`,
  `start_recording`/`stop_recording` are callable, and
  `stop_recording()` without a prior `start_recording()` raises
  the implementation's specific error type.

## Out (per story scope)

- `DeviceRegistry`, lifecycle, descriptor — HS-14-02.
- `/api/devices/audio` WebSocket route, PSK auth, handshake —
  HS-14-03 / HS-14-04.
- Per-device queue depth in `/api/runtime/status` — HS-14-04.
- Voice-typing / meeting wiring against `RemoteAudioRecorder`
  — HS-14-05 / HS-14-06.

## Test runs

`uv run pytest -q tests/unit/test_remote_audio_recorder.py
tests/unit/test_audio_source_contract.py
tests/unit/test_audio_resample.py
tests/unit/test_audio_devices_pulse.py`

```
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.0.2, pluggy-1.6.0
rootdir: /home/karol/dev/HoldSpeak
configfile: pyproject.toml
plugins: timeout-2.4.0, cov-7.0.0, anyio-4.12.1, asyncio-1.3.0, mock-3.15.1
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=function, asyncio_default_test_loop_scope=function
collected 48 items

tests/unit/test_remote_audio_recorder.py ............                    [ 25%]
tests/unit/test_audio_source_contract.py ..........                      [ 45%]
tests/unit/test_audio_resample.py ........................               [ 95%]
tests/unit/test_audio_devices_pulse.py ..                                [100%]

============================== 48 passed in 0.33s ==============================
```

Regression sweep on the audio-adjacent paths (controller,
web_runtime) to confirm the Protocol addition is non-disruptive:

`uv run --extra test pytest -q tests/unit/test_controller.py
tests/unit/test_web_runtime.py
tests/unit/test_audio_resample.py
tests/unit/test_audio_devices_pulse.py
tests/unit/test_remote_audio_recorder.py
tests/unit/test_audio_source_contract.py`

```
..............................................................           [100%]
62 passed in 0.63s
```

## Notes

- **Protocol vs ABC.** Picked `@runtime_checkable` `Protocol`
  per the story recommendation — keeps `AudioRecorder` and the
  many existing `FakeAudioRecorder` test doubles unchanged
  while enabling the contract test to `isinstance`-check
  conformance.
- **Bounded ring vs unbounded queue.** Substrate-level only:
  drop-oldest with a logged warning is the simplest viable
  signal that backpressure is real before HS-14-04 hooks the
  policy into per-device runtime status.
- **`AudioRecorder` byte-stable.** No edits to `AudioRecorder`
  beyond the new `from typing import Protocol, runtime_checkable`
  import and the new `AudioSource` class above the existing
  `AudioRecorderError` definition.
