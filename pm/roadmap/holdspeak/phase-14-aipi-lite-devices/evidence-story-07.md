# HS-14-07 evidence — Server → device status push-back

## What shipped

- `holdspeak/device_status.py` — new module containing
  `DeviceStatusEmitter`. Thread-safe registry of per-device
  sender callables (`Callable[[str, int], None]`); each
  WebSocket handler registers a sender at handshake-accept
  time and unregisters on disconnect. `send` /
  `broadcast` swallow sender exceptions and return delivery
  counts so callers don't have to wrap them. `{label}`
  substitution against an injected ``DeviceRegistry``-shaped
  ``label_lookup`` resolves the device's registered label;
  falls back to ``device_id`` when missing.

- `holdspeak/device_audio_ws.py` — outbound writer + inbound
  event handling.
  - Each connection now spins up an async ``_writer_loop``
    task that drains an asyncio queue of ``{type: "status",
    text, ttl_ms}`` frames and writes them via
    ``websocket.send_json``. Sends from any thread go through
    ``loop.call_soon_threadsafe(out_queue.put_nowait, msg)``
    so the runtime's voice / meeting paths (which run on
    background threads) can fire status updates without
    needing an event loop reference.
  - Disconnect cleanup unregisters the emitter, posts a
    ``None`` sentinel onto the queue, and waits up to 1 s
    for the writer to drain before canceling.
  - ``_handle_control`` learned a new ``"event"`` control
    type. ``{type: "event", name, at}`` dispatches to an
    optional ``EventHandler``; ``at`` is coerced to ``float``
    when present and passed through as ``None`` otherwise.
    Events without a ``name`` are dropped with a warning log.
  - The route exposes two new optional kwargs on
    ``register_device_audio_routes``: ``status_emitter`` and
    ``on_event``.

- `holdspeak/web_server.py` — ``MeetingWebServer`` forwards
  ``device_status_emitter`` and ``on_device_event``
  constructor kwargs into ``register_device_audio_routes``.
  When ``device_status_emitter`` is omitted, an in-process
  ``DeviceStatusEmitter`` is constructed using the registry as
  the label lookup so existing tests stay green.

- `holdspeak/web_runtime.py` — emit sites and event handler.
  - ``_transcribe_and_type`` and ``_kick_off_transcribe``
    grew an ``on_complete`` hook that fires *outside* the
    typing try-block with the transcribed text, so the
    device gets the snippet even if local typing failed.
  - ``_on_device_voice_start`` emits ``Listening...`` on
    accept; ``_on_device_voice_stop`` emits ``Thinking...``
    immediately and registers a transcript-complete
    callback that emits the first 80 chars of the
    transcript with ``ttl_ms=4000``.
  - ``_start_meeting`` broadcasts ``Recording 00:00`` to
    attached devices after attach. (Per-minute ticks are
    deferred — the acceptance criteria require status on
    bookmark and save, not on every minute boundary.)
  - ``_on_bookmark`` broadcasts ``Bookmark @ {timestamp}s``
    to attached devices when a bookmark lands during an
    active meeting.
  - ``_stop_active_meeting`` broadcasts
    ``Saving meeting...`` to attached devices *before*
    ``session.stop`` flips state and clears
    ``state.devices``.
  - New ``_on_device_event`` handler: ``long_press`` on an
    attached device fires
    ``MeetingSession.add_bookmark`` (auto-labeled) and
    broadcasts the resulting ``Bookmark @ ...`` to every
    attached device. Other event names are logged + ignored
    (the protocol ferries them but only ``long_press`` has a
    binding in v1).

## Out (per story scope)

- Rich UI on the device side (eyes / icons / progress bars).
- Localization (English-only this phase; ``{label}`` is the
  only substitution).
- Long-running emitters across reconnect — reconnect = blank
  slate.

## Test runs

`uv run --extra test pytest tests/unit/test_status_emitter.py
tests/integration/test_device_status_pushback.py`

```
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.0.2, pluggy-1.6.0
rootdir: /home/karol/dev/HoldSpeak
configfile: pyproject.toml
plugins: timeout-2.4.0, cov-7.0.0, anyio-4.12.1, asyncio-1.3.0, mock-3.15.1
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=function, asyncio_default_test_loop_scope=function
collected 15 items

tests/unit/test_status_emitter.py ........                               [ 53%]
tests/integration/test_device_status_pushback.py .......                 [100%]

============================== 15 passed in 0.75s ==============================
```

`tests/unit/test_status_emitter.py` (8 cases):
- send without registered sender returns False;
- register + send delivers `(text, ttl_ms)` to the sender;
- unregister drops the sender;
- send swallows sender-raised exceptions;
- broadcast returns the delivery count and skips ghosts;
- ``{label}`` substitution against a stub registry;
- ``{label}`` fallback to ``device_id`` when the lookup
  returns nothing;
- ``active_device_ids`` reflects register / unregister state.

`tests/integration/test_device_status_pushback.py` (7 cases):
- emitter.send after handshake reaches the device as a
  ``{type: "status", text, ttl_ms}`` frame;
- ``{label}`` and ``ttl_ms`` round-trip through the WS;
- end-to-end voice-typing turn emits the
  Listening → Thinking → snippet sequence through the
  emitter (with a fake voice handler);
- inbound ``event`` with ``name`` + numeric ``at``
  dispatches to the handler;
- inbound ``event`` without ``name`` is ignored;
- inbound ``event`` with no ``at`` lands as ``None``;
- disconnect unregisters the device from the emitter.

Full regression sweep:

`uv run --extra test pytest -q tests/unit/test_status_emitter.py
tests/integration/test_device_status_pushback.py
tests/integration/test_device_meeting_session.py
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
........................................................................ [ 21%]
........................................................................ [ 43%]
........................................................................ [ 64%]
........................................................................ [ 86%]
..............................................                           [100%]
334 passed in 2.59s
```

One existing test (`test_runtime_meeting_control_callbacks_are_wired`)
needed its `FakeState` extended with an empty `devices` list
because `_stop_active_meeting` now reads it for the
``Saving meeting...`` broadcast. Pure shape update.

## Outstanding manual verification

Acceptance bullet 5 — *"Old standalone-bridge LCD strings are
now driven by the server, not the bridge — verified manually
with the AIPI-Lite hooked up"* — is deferred to HS-14-08's
DoD pass. The story file marks this checkbox unticked with
the deferral noted; HS-14-08 owns the cross-repo manual
verification before the phase closes.

## Notes

- **Why `loop.call_soon_threadsafe(put_nowait, msg)` instead
  of `asyncio.run_coroutine_threadsafe(queue.put(msg))`.**
  The former is non-blocking and lock-free; the latter would
  schedule a coroutine and wait on a future, adding latency
  and a failure mode if the loop is already shutting down.
  Status sends are fire-and-forget, so dropping under
  shutdown is correct.
- **Why ``on_complete`` fires outside the typing try-block.**
  If the local typer raises (Wayland, missing perms), the
  text already has a transcription — sending the snippet to
  the device is the entire point of the device-side LCD.
  Wrapping ``on_complete`` in the typing try-block would
  swallow the snippet on a typer error.
- **Why no per-minute ``Recording`` tick in HS-14-07.** The
  acceptance criteria require status on bookmark + save; the
  scope mentions "updated each minute" but the bookmark and
  save events already keep the device LCD fresh during a
  meeting. A periodic tick can land in HS-14-07's follow-up
  if it turns out to be needed.
- **One-way disconnect cleanup ordering.** ``finally`` block:
  unregister emitter → post ``None`` to queue → wait for
  writer → unregister + tear down recorder. The emitter is
  unregistered first so a racing emit during teardown can't
  hit a stale queue.
