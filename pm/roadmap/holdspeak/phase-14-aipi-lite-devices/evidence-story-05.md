# HS-14-05 evidence — Voice-typing path consumes remote audio

## What shipped

- `holdspeak/voice_typing.py` — new module owning a single
  ``VoiceTypingSession`` class. Methods:
  - ``begin(source: AudioSource, *, owner: str) -> bool`` —
    locks the session under a ``threading.Lock``; returns
    ``False`` (info-log, no exception) when an active session
    already exists. Calls ``source.start_recording()`` only
    after the ownership claim succeeds; rolls the claim back if
    ``start_recording`` raises so a failed begin doesn't strand
    the session.
  - ``end(owner: str) -> Optional[np.ndarray]`` — returns the
    audio when ``owner`` matches; returns ``None`` (no
    exception) on owner mismatch or when no session is active.
  - ``cancel(owner: str) -> None`` — disconnect-cleanup path;
    drops the session, calls ``stop_recording`` on the source,
    and swallows any error since the audio is being discarded.
  - ``is_active`` / ``active_owner`` properties for diagnostics.

- `holdspeak/device_audio_ws.py` — three new optional handlers
  threaded through ``register_device_audio_routes``:
  ``on_voice_start`` / ``on_voice_stop`` / ``on_voice_cancel``.
  ``_handle_control`` is now an ``async`` function so it can
  send back a ``{"type": "error", "code": "session_busy",
  "reason": "..."}`` frame when ``on_voice_start`` returns
  ``False`` without closing the WebSocket. When voice handlers
  are wired (production), they own the audio — ``on_chunk`` is
  not invoked from the stop path. When they are absent (the
  HS-14-04 tests), the legacy direct
  ``recorder.start/stop_recording`` + ``on_chunk`` path is
  unchanged. ``_teardown`` calls ``on_voice_cancel`` first so a
  device that disconnected mid-session releases the session
  before the recorder is torn down.

- `holdspeak/web_server.py` — ``MeetingWebServer.__init__``
  forwards the three new kwargs (``on_device_voice_start``,
  ``on_device_voice_stop``, ``on_device_voice_cancel``) into
  ``register_device_audio_routes``. Existing tests that
  construct ``MeetingWebServer`` without those kwargs continue
  to use the HS-14-04 path.

- `holdspeak/web_runtime.py` — voice typing now flows through a
  single shared ``VoiceTypingSession``:
  - The hotkey path: ``_on_hotkey_press`` calls
    ``voice_session.begin(recorder, owner="hotkey")``;
    ``_on_hotkey_release`` calls ``voice_session.end("hotkey")``.
    A press received while a device session is active returns
    ``False`` and is silently logged — the hotkey listener
    cannot drown the device.
  - The device path: ``_on_device_voice_start`` /
    ``_on_device_voice_stop`` / ``_on_device_voice_cancel``
    plug into the WS handlers using
    ``owner=f"device:{device_id}"``. A meeting in progress
    automatically rejects the device start (no parallel modes).
  - Transcribe + type extracted into ``_transcribe_and_type``
    and ``_kick_off_transcribe`` so both paths land in the same
    Whisper / ``text_processor`` / ``TextTyper`` pipeline; voice
    state ("recording" / "transcribing" / "idle") is set
    consistently from either entry point.
  - ``_active_meeting_session() is not None`` short-circuits
    both hotkey press and device voice-start so the device
    can't trample a meeting recorder.

## Out (per story scope)

- Multiple concurrent voice-typing sessions across devices —
  one-at-a-time is the v1 rule; second device's start while
  another session is active receives ``session_busy``.
- Meeting path device wiring — HS-14-06.
- Server → device status push messages — HS-14-07.

## Test runs

`uv run --extra test pytest tests/unit/test_voice_typing_session.py
tests/integration/test_voice_typing_via_device.py`

```
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.0.2, pluggy-1.6.0
rootdir: /home/karol/dev/HoldSpeak
configfile: pyproject.toml
plugins: timeout-2.4.0, cov-7.0.0, anyio-4.12.1, asyncio-1.3.0, mock-3.15.1
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=function, asyncio_default_test_loop_scope=function
collected 14 items

tests/unit/test_voice_typing_session.py ..........                       [ 71%]
tests/integration/test_voice_typing_via_device.py ....                   [100%]

============================== 14 passed in 0.61s ==============================
```

`tests/unit/test_voice_typing_session.py` covers begin /
second-begin-rejected / matching-owner end / mismatched-owner
end / no-session end / begin failure releases the lock /
cancel / cancel-with-wrong-owner / blank-owner rejection / 10
concurrent begins serialize to exactly one winner.

`tests/integration/test_voice_typing_via_device.py` (4 cases)
exercises the FastAPI route end-to-end: full pipeline
handshake → start → PCM → stop ⇒ fake STT receives the audio,
mock typer receives the transcript; a second device's start
while another session is active receives the
``session_busy`` JSON frame; mid-session disconnect cancels
without leaking session ownership and without spuriously
running transcribe; the legacy ``on_chunk`` path still works
when voice handlers are absent.

Regression sweep on audio + device + voice + controller +
web_runtime + config + intel_streaming:

`uv run --extra test pytest -q tests/unit/test_voice_typing_session.py
tests/integration/test_voice_typing_via_device.py
tests/integration/test_device_audio_ingest.py
tests/unit/test_device_handshake.py
tests/unit/test_device_registry.py
tests/unit/test_remote_audio_recorder.py
tests/unit/test_audio_source_contract.py
tests/unit/test_audio_resample.py
tests/unit/test_audio_devices_pulse.py
tests/unit/test_controller.py
tests/unit/test_web_runtime.py
tests/unit/test_config.py
tests/integration/test_intel_streaming.py`

```
........................................................................ [ 31%]
........................................................................ [ 62%]
........................................................................ [ 93%]
................                                                         [100%]
232 passed in 2.12s
```

## Notes

- **TUI controller.py left alone.** The story's "controller"
  language is conceptual — in web flagship mode the orchestrator
  is ``run_web_runtime``, which is what now consumes
  ``VoiceTypingSession``. The legacy ``HoldSpeakController``
  (used only by ``holdspeak tui``) keeps its direct
  ``AudioRecorder`` ownership; it has no WebSocket and no
  device path, so wiring the session there would be churn for
  no behavior change.
- **Why a separate ``on_voice_cancel`` instead of "stop with
  discard".** ``on_voice_stop`` runs the full transcribe+type
  side effect, which is the wrong thing on a mid-session
  disconnect. The cancel handler runs ``voice_session.cancel``
  only — no STT, no typer.
- **Why the busy reply is a JSON error frame, not a close.**
  Closing the socket on busy would force the device's bridge
  to reconnect / re-handshake just to retry. An in-band error
  frame lets the bridge wait, retry on the next hotkey press,
  and keep the connection live.
- **Test isolation: voice handlers wired in the test, not via
  ``run_web_runtime``.** Driving ``run_web_runtime`` end-to-end
  in a unit test would require mocking the real Whisper model
  and the global hotkey listener; the integration test instead
  pins down the contract (handler signatures + busy reply) by
  wiring the same ``VoiceTypingSession`` shape directly into
  ``MeetingWebServer``. The web-runtime gluing is small enough
  to inspect by reading ``_on_device_voice_*`` once.
