# HS-14-04 evidence — `/api/devices/audio` WebSocket + backpressure

## What shipped

- `holdspeak/device_audio_ws.py` — new module, the only new
  network-facing code for the phase. Public API:
  `register_device_audio_routes(app, *, device_registry,
  get_psk, on_chunk=None)`. Everything below it is private.
  - `_serve_device_audio` — accepts the connection, runs the
    handshake, then drives the dispatch loop; cleans up in the
    `finally` (mid-recording stop is swallowed; descriptor is
    unregistered) so a clean *or* abrupt disconnect leaves the
    registry consistent.
  - `_do_handshake` — receives the first frame, requires JSON
    text, parses through `DeviceHandshake`, calls
    `verify_psk(handshake.psk, get_psk())`, registers via the
    shared `DeviceRegistry`, and replies with
    `{type: "hello-ack", device_id, label}`. Maps
    `InvalidHandshakeError` / `PskMismatchError` /
    `DuplicateLabelError` onto `ws.close(code=...)` using the
    typed error's `.code` (no policy duplication).
  - `_dispatch_loop` — reads frames; text → control, bytes →
    `recorder.push`. Each frame ticks `registry.touch` to
    refresh `last_seen`. Disconnect breaks the loop cleanly.
  - `_handle_control` — `start`/`stop`/`heartbeat`. `start` is
    idempotent (no-op when already recording). `stop` invokes
    the optional `on_chunk(device_id, ndarray)` consumer.
    Unknown control types are logged + dropped, not
    error-closed (a misbehaving client doesn't kill its own
    audio session).

- `holdspeak/device_audio.py` — three substrate tweaks:
  - `RemoteAudioRecorder` accepts a new `device_id: Optional[str]`
    kwarg (default `None`, so the existing
    `tests/unit/test_remote_audio_recorder.py` still asserts the
    legacy log message). When `device_id` is set, the overflow
    log key flips to `device.queue.overflow` and includes
    `device_id` + `dropped_bytes` in the structured `extra`.
  - New read-only property `RemoteAudioRecorder.buffered_bytes`
    (current pushed-buffer depth in bytes; int16 LE = 2
    bytes/sample).
  - `DeviceRegistry.register` now constructs the recorder with
    `device_id=device_id`, so the device-aware overflow log
    is automatic. `DeviceRegistry.active()` snapshots
    `queue_depth` from each live recorder's `buffered_bytes`
    so `/api/runtime/status` (HS-14-07) gets a true depth
    without anyone manually ticking the registry.

- `holdspeak/web_server.py` — `MeetingWebServer.__init__` gains
  two new optional kwargs: `device_psk_provider: Optional[Callable[[], str]]`
  (defaults to `lambda: ensure_device_psk(Config.load())`) and
  `on_device_audio_chunk: Optional[Callable[[str, np.ndarray], None]]`
  (defaults to `None`). `_create_app` calls
  `register_device_audio_routes(...)` immediately after the
  `app.state.device_registry` binding, so the WebSocket route
  is mounted on every FastAPI app this class produces.

- `holdspeak/web_runtime.py` — passes the runtime's already-loaded
  `Config` into the psk provider closure (`lambda:
  ensure_device_psk(config)`) so the route doesn't reload
  config from disk on every connection.

## Out (per story scope)

- Voice-typing wiring against `on_chunk` — HS-14-05.
- Meeting wiring against `on_chunk` — HS-14-06.
- Server-to-device status push messages — HS-14-07.
- Cross-network exposure (TLS, public URL) — phase 15.

## Test runs

`uv run --extra test pytest tests/integration/test_device_audio_ingest.py`

```
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.0.2, pluggy-1.6.0
rootdir: /home/karol/dev/HoldSpeak
configfile: pyproject.toml
plugins: timeout-2.4.0, cov-7.0.0, anyio-4.12.1, asyncio-1.3.0, mock-3.15.1
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=function, asyncio_default_test_loop_scope=function
collected 14 items

tests/integration/test_device_audio_ingest.py ..............             [100%]

============================== 14 passed in 1.07s ==============================
```

The 14 cases cover, exactly:
- handshake success → `hello-ack` and registry visibility,
- bad handshake (non-JSON) → 4001,
- handshake missing field → 4001,
- handshake extra field (strict `extra=forbid`) → 4001,
- bad PSK → 4003,
- duplicate label → 4009,
- push-then-stop emits a float32 ndarray of correct shape +
  values via the `on_chunk` consumer,
- heartbeat exercises the registry (clean teardown after),
- clean disconnect unregisters the device,
- mid-recording disconnect drops in-flight audio + unregisters,
- queue overflow drops oldest with a single
  `device.queue.overflow` warning carrying `device_id` +
  `dropped_bytes`,
- `DeviceRegistry.active()` reflects live `queue_depth`,
- handshake calls the psk provider every connection, so a
  rotated PSK takes effect on the next reconnect.

Regression sweep across audio + device + controller +
web_runtime + config + intel_streaming:

`uv run --extra test pytest -q tests/integration/test_device_audio_ingest.py
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
........................................................................ [ 33%]
........................................................................ [ 66%]
........................................................................ [ 99%]
..                                                                       [100%]
218 passed in 1.95s
```

## Notes

- **Why module-level `from fastapi import WebSocket`.** The
  initial pass had the import inside `register_device_audio_routes`,
  but with `from __future__ import annotations` the type hint
  on the inner `_ingest(websocket: WebSocket)` resolves through
  the module's globals — not the enclosing function — so
  FastAPI saw `WebSocket` as unresolved and treated `websocket`
  as a query parameter (close 1008 with a Pydantic
  "Field required" payload). Fix: hoist the imports to the
  top of the module. `fastapi` is already a core HoldSpeak dep
  so the unconditional import is fine.
- **Why typed errors carry `.code`.** The route does
  `await websocket.close(code=exc.code)` rather than mapping
  exception type → code at the call site. That keeps HS-14-03's
  policy (which exception means which code) co-located with
  the exception class definition — no chance of HS-14-04
  drifting from HS-14-03.
- **Why `start` is idempotent.** A racing client that sends
  `start` twice (e.g., the bridge re-emits after a brief
  network blip) shouldn't crash its own session. We guard with
  `if not recorder.is_recording`. Same logic on `stop` —
  no-op when already stopped.
- **Why `recorder.max_buffer_seconds` is mutable.** The
  overflow integration test pins the cap to 0.05 s post-
  registration to force overflow in a few hundred bytes,
  rather than blasting megabytes through the WS test client.
  This is a test-only knob; production never mutates it.
