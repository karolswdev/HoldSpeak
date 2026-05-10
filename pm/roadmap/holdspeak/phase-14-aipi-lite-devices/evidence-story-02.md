# HS-14-02 evidence — DeviceRegistry + Device Descriptor Model

## What shipped

- `holdspeak/device_audio.py` — added `DeviceDescriptor`,
  `DeviceRegistryError`, `DuplicateLabelError`, and
  `DeviceRegistry`.
  - `DeviceDescriptor` is a mutable dataclass:
    `id`, `label`, `connected_at`, `last_seen`, `queue_depth=0`.
    `queue_depth` is the placeholder field HS-14-04 will populate
    once the WebSocket route is reporting per-device buffer
    depth.
  - `DeviceRegistry` is thread-safe (single `threading.Lock`
    around `_descriptors` + `_recorders` dicts). Public API:
    `register(id, label) -> DeviceDescriptor`,
    `unregister(id)` (idempotent),
    `get(id) -> Optional[DeviceDescriptor]`,
    `active() -> list[DeviceDescriptor]` (returns *copies* via
    `dataclasses.replace` — caller mutations cannot corrupt
    registry state),
    `touch(id)` (no-op when unknown, logged at debug),
    `recorder_for(id) -> Optional[AudioSource]`.
  - `register()` rejects blank id/label with `ValueError`,
    rejects same-id re-registration with `DeviceRegistryError`
    (loud, not silent), and rejects an active label collision
    with `DuplicateLabelError` (typed for the eventual 409
    Conflict mapping in HS-14-04). A label freed by
    `unregister` is reusable immediately.
  - On `register`, a fresh `RemoteAudioRecorder` is created and
    held privately. On `unregister`, the descriptor and
    recorder are dropped together. Mid-flight callers holding
    `recorder_for` references are unaffected — Python GC
    cleans up once they release.
- `holdspeak/web_server.py` — `MeetingWebServer.__init__`
  accepts an optional `device_registry: Optional[DeviceRegistry]`
  kwarg. When omitted, a fresh registry is constructed so
  every existing test (which builds a server bare) keeps
  working. Stored on `self.device_registry` and bound to
  `app.state.device_registry` inside `_create_app` so future
  FastAPI routes (HS-14-04) can read it from `request.app.state`.
- `holdspeak/web_runtime.py` — `run_web_runtime` constructs a
  `DeviceRegistry()` early and passes it into the
  `MeetingWebServer` call. This is the single shared instance
  for the runtime's lifetime.

## Out (per story scope)

- WebSocket route, auth, handshake — HS-14-03 / HS-14-04.
- Persistence — registry is in-memory only; devices re-register
  on reconnect.
- Per-device queue-depth observability + `/api/runtime/status`
  integration — HS-14-04.

## Test runs

`uv run --extra test pytest tests/unit/test_device_registry.py
tests/unit/test_remote_audio_recorder.py
tests/unit/test_audio_source_contract.py`

```
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.0.2, pluggy-1.6.0
rootdir: /home/karol/dev/HoldSpeak
configfile: pyproject.toml
plugins: timeout-2.4.0, cov-7.0.0, anyio-4.12.1, asyncio-1.3.0, mock-3.15.1
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=function, asyncio_default_test_loop_scope=function
collected 36 items

tests/unit/test_device_registry.py ..............                        [ 38%]
tests/unit/test_remote_audio_recorder.py ............                    [ 72%]
tests/unit/test_audio_source_contract.py ..........                      [100%]

============================== 36 passed in 0.32s ==============================
```

`tests/unit/test_device_registry.py` ships 14 cases (story
required ≥5): register-then-get, get-unknown-returns-none,
double-register-different-label, duplicate-label-fails,
double-register-same-id-raises, unregister-removes-descriptor-
and-recorder, idempotent-unregister, label-freed-after-
unregister-is-reusable, recorder_for-returns-AudioSource,
recorder_for-unknown-returns-none, touch-updates-last-seen,
touch-unknown-id-is-noop, active-returns-copies (mutating a
returned descriptor must not corrupt the registry),
register-rejects-blank-inputs.

Regression sweep on audio + controller + web_runtime:

`uv run --extra test pytest -q tests/unit/test_device_registry.py
tests/unit/test_remote_audio_recorder.py
tests/unit/test_audio_source_contract.py
tests/unit/test_audio_resample.py
tests/unit/test_audio_devices_pulse.py
tests/unit/test_controller.py
tests/unit/test_web_runtime.py`

```
........................................................................ [ 94%]
....                                                                     [100%]
76 passed in 0.62s
```

## Notes

- **Why `DeviceDescriptor` is mutable, not frozen.** `touch()`
  needs to update `last_seen` in place. Returned snapshots are
  always copies (`dataclasses.replace`), so external callers
  cannot mutate live state.
- **Why same-id re-register raises rather than overwriting.**
  An overwrite would silently destroy the previous device's
  recorder while a meeting consumer might still be holding
  the reference. Loud failure → the WebSocket handler can map
  to a 409 / force the device through unregister first.
- **Constructor injection on `MeetingWebServer`.** The story
  Notes called for "a property there [in web_runtime.py] rather
  than module-global state". Constructor injection keeps the
  registry as a per-runtime instance with explicit ownership in
  `run_web_runtime`, while still defaulting to a self-created
  one in tests that don't care.
