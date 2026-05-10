# HS-14-06 evidence — Meeting path accepts device streams

## What shipped

- `holdspeak/device_audio.py` — added
  `RemoteAudioRecorder.drain()`. Returns the currently-buffered
  audio (mono float32 at the target rate) without stopping the
  recording; clears the internal frame deque. Returns an empty
  array when not recording. `_frames_to_audio` factored out so
  ``stop_recording`` and ``drain`` share the resample fallback.
- `holdspeak/meeting_session.py` data model:
  - `TranscriptSegment.device_id: Optional[str] = None` (last
    field; default `None`). Round-trips through `to_dict`. The
    legacy mic + system code paths leave it `None`.
  - `MeetingState.devices: list[DeviceDescriptor]` (default
    empty). `to_dict()` serializes each descriptor through a
    new module-level `_device_descriptor_to_dict` shim so
    datetime fields go through `.isoformat()` and the
    `device_audio` module stays free of meeting-side concerns.
- `holdspeak/meeting.py` — `MeetingRecorder` gained:
  - `_device_sources` / `_device_labels` / `_device_last_drain`
    state, populated by `register_device_stream(device_id,
    source, *, label)` and torn down by
    `unregister_device_stream`.
  - `device_label(device_id)`, `registered_device_ids()`,
    `get_pending_device_chunks() -> dict[str, list[AudioChunk]]`.
    The recorder doesn't capture device audio itself — the WS
    route pushes PCM via ``RemoteAudioRecorder.push`` and the
    meeting drains on the same 10-second cadence as the mic +
    system buffers. Each drain produces at most one
    ``AudioChunk`` per device, timestamped at the previous
    drain boundary.
- `holdspeak/meeting_session.py` — `MeetingSession` gained:
  - `attach_device(descriptor, source)` — appends the
    descriptor to ``state.devices``, calls
    ``source.start_recording()``, registers it on the recorder
    with the descriptor's label. Rolls the descriptor append
    back if ``start_recording`` raises.
  - `detach_device(device_id)` — best-effort stop +
    unregister; the descriptor stays on ``state.devices`` so
    the saved meeting still records who participated.
  - `is_device_attached(device_id)` — convenience for the
    web-runtime voice handlers.
  - `_transcribe_chunks(...)` accepts a new
    `device_chunks: Optional[dict[str, list[AudioChunk]]]`
    kwarg. Each device's chunks transcribe to a
    `TranscriptSegment` with `device_id=device_id` and
    `speaker` resolved to the device's registered label.
  - The transcription loop and the final-flush path
    (`recorder.stop()`) both call
    `recorder.get_pending_device_chunks()` so audio captured
    between the last poll and meeting stop still surfaces in
    the transcript.
- `holdspeak/web_server.py` — added
  - ``_MeetingStartRequest`` Pydantic model (``devices:
    Optional[list[str]] = None``) accepted as the
    ``POST /api/meeting/start`` body.
  - ``_UnknownDeviceError`` (subclass of ``LookupError``) so
    ``on_start`` callers can raise an exception that the route
    maps to a 404 with the offending ``device_id`` surfaced in
    the JSON body.
  - The route invokes ``on_start(devices=...)`` only when a
    non-empty list arrives, so the legacy no-arg signature
    keeps working.
- `holdspeak/web_runtime.py` — `_start_meeting` accepts a
  ``devices`` kwarg. Each id is validated against
  ``device_registry.get(...)`` *before* spinning up the
  session; an unknown id raises ``_UnknownDeviceError``. After
  ``session.start()`` returns, the descriptor / source pairs
  are attached via ``session.attach_device``. The voice
  handlers were extended to respect attachment: an attached
  device's ``start`` is a no-op (the meeting owns the
  recorder), a non-attached device's ``start`` during a
  meeting is rejected with ``session_busy``.

## Out (per story scope)

- Meeting-time UI showing N device streams — phase 16.
- > 2 simultaneous devices in one meeting — works
  architecturally; UX/UI polish defers.
- Speaker diarization within a single device's stream — out;
  one device = one speaker by convention.

## Test runs

`uv run --extra test pytest tests/integration/test_device_meeting_session.py`

```
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.0.2, pluggy-1.6.0
rootdir: /home/karol/dev/HoldSpeak
configfile: pyproject.toml
plugins: timeout-2.4.0, cov-7.0.0, anyio-4.12.1, asyncio-1.3.0, mock-3.15.1
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=function, asyncio_default_test_loop_scope=function
collected 7 items

tests/integration/test_device_meeting_session.py .......                 [100%]

============================== 7 passed in 0.59s ===============================
```

The 7 integration cases:

- `test_attach_device_records_descriptor_and_starts_source`
  — attach appends to `state.devices`, starts the source, and
  flips `is_device_attached` to True.
- `test_device_chunks_become_labeled_segments` — feed 1.5 s of
  audio through a `_FakeRemoteSource`, drain via the stub
  recorder, run `_transcribe_chunks` → produces a single
  `TranscriptSegment` with `device_id == "aipi-1"`,
  `speaker == "Karol"`, and the fake transcriber's text.
- `test_local_mic_segment_keeps_device_id_none` — locks the
  legacy contract: a mic chunk with no `device_chunks`
  argument still yields `device_id=None`, `speaker=mic_label`.
- `test_detach_device_stops_source_and_unregisters` — stop
  side effects without leaking ownership.
- `test_meeting_start_passes_devices_to_on_start` — drives
  the FastAPI route with `{"devices": ["aipi-1"]}` and checks
  that `on_start` receives the list.
- `test_meeting_start_unknown_device_returns_404` — raises
  `_UnknownDeviceError` from `on_start`; route returns 404
  with `device_id` echoed in the body.
- `test_meeting_start_legacy_no_body_works` — pinned-down
  contract: callers without a body still get a 200, with the
  no-arg `on_start` signature.

Plus 4 new unit cases on `RemoteAudioRecorder.drain`
(`test_drain_returns_buffered_audio_and_clears`,
`test_drain_when_not_recording_returns_empty`,
`test_drain_does_not_lose_recording_state`,
`test_drain_resamples_when_wire_rate_differs`) and 2 round-trip
cases on `MeetingState.devices` plus a `device_id` field check
on `TranscriptSegment.to_dict`.

Two existing tests required parallel updates:
- `tests/unit/test_meeting_state.py::TestTranscriptSegment::test_to_dict`
  — its literal expected dict gained `"device_id": None`.
- `tests/unit/test_meeting_session.py::test_stop_completes_without_deadlock_during_final_transcription_and_intel`'s
  `_FakeRecorder` gained a `get_pending_device_chunks` method
  returning `{}` so the new final-flush call doesn't blow up.

Full regression sweep:

`uv run --extra test pytest -q tests/integration/test_device_meeting_session.py
tests/integration/test_voice_typing_via_device.py
tests/integration/test_device_audio_ingest.py
tests/integration/test_intel_streaming.py
tests/unit/test_voice_typing_session.py
tests/unit/test_remote_audio_recorder.py
tests/unit/test_audio_source_contract.py
tests/unit/test_device_registry.py
tests/unit/test_device_handshake.py
tests/unit/test_meeting_session.py
tests/unit/test_meeting_state.py
tests/unit/test_meeting_chunks.py
tests/unit/test_meeting_exports.py
tests/unit/test_web_runtime.py
tests/unit/test_controller.py
tests/unit/test_config.py
tests/unit/test_audio_resample.py
tests/unit/test_audio_devices_pulse.py`

```
........................................................................ [ 22%]
........................................................................ [ 45%]
........................................................................ [ 67%]
........................................................................ [ 90%]
...............................                                          [100%]
319 passed in 2.26s
```

## Notes

- **Why `MeetingState.devices: list` (not `list[DeviceDescriptor]`).**
  Importing `DeviceDescriptor` at module import time would
  introduce a meeting → device_audio dependency where today
  the arrow goes the other way (device_audio is the lower
  layer). The annotation in the dataclass is the unparametrized
  `list`; the docstring and `TYPE_CHECKING` import keep the
  intended type visible without the runtime coupling.
- **Drain timestamps are approximate.** A `get_pending_device_chunks`
  call stamps the produced chunk with the previous drain's
  timestamp, not the exact arrival time of each pushed frame.
  The transcript orders segments by `start_time`, which is
  precise to the drain interval (usually 10 s). Sub-drain-window
  ordering between mic, system, and device streams is not
  guaranteed; refining that needs per-frame timestamps from
  the bridge and isn't in HS-14-06's scope.
- **Why the meeting drains rather than stops + restarts.**
  ``stop_recording`` returns audio and ends the session;
  starting again loses any frames that arrived during the
  short turnaround. ``drain`` keeps the recorder open so the
  WS push path is never blocked.
- **Meeting attachment + voice handlers.** A device that's
  attached to a meeting bypasses the voice session entirely —
  the recorder is started by ``attach_device``, the WS pushes
  PCM into it, and the meeting polls. The device's ``start``/
  ``stop`` JSON frames are no-ops in this mode (the WS still
  acks ``start`` so the client UI reflects "we heard you").
  Once HS-14-07 lands, the server can also push state hints
  back to the device's LCD on the same channel.
