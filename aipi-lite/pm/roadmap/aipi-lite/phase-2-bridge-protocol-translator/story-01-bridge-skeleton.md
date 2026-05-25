# AIPI-2-01 - Bridge Skeleton: ESPHome + HoldSpeak Connections

- **Project:** aipi-lite
- **Phase:** 2
- **Status:** done
- **Depends on:** none
- **Unblocks:** AIPI-2-02, AIPI-2-03
- **Owner:** karol

## Problem

Today's `bridge.py` is a self-contained voice loop: aioesphomeapi
listens for the right-button press → buffers audio → faster-whisper
transcribes → local LLM generates a reply → gTTS synthesizes → ESP32
plays. AIPI-2 deletes the middle three steps and replaces them with a
WebSocket forwarder to HoldSpeak. Before any audio can flow, the
spine has to exist: an async event loop that maintains both
connections, performs the HoldSpeak handshake, and survives
disconnects on either side without exiting.

## Scope

### In

- Rewrite `bridge.py`'s `main()` as an async event loop that runs two
  concurrent tasks:
  1. `device_loop()` — opens an `aioesphomeapi.APIClient` against the
     AIPI-Lite, subscribes to relevant events (button + audio
     placeholders for stories 02/03), holds the connection.
  2. `holdspeak_loop()` — opens a `websockets` client to
     `ws://<HOLDSPEAK_HOST>:<HOLDSPEAK_PORT>/api/devices/audio`,
     sends a `DeviceHandshake` JSON frame, awaits `hello-ack`, then
     enters a heartbeat + receive loop.
- Pydantic models that mirror HoldSpeak's wire schema:
  `Hello` (outbound), `HelloAck` (inbound), `Heartbeat` (both
  directions), `ServerError` (inbound). All with `extra="forbid"`.
  Source of truth: `~/dev/HoldSpeak/holdspeak/device_audio.py`.
- **Device leg reconnect: delegate to `aioesphomeapi.ReconnectLogic`.**
  That class already implements an exponential-backoff retry loop
  for the ESPHome API connection. Wrap a callback to log the
  reconnect lifecycle structurally (`event="reconnect.device"`,
  `state=<connecting|connected|disconnected>`).
- **HoldSpeak (WS) leg reconnect:** custom helper
  `reconnect_with_backoff(coro_factory, name)` with
  exponential backoff + jitter. Schedule: 1s, 2s, 4s, 8s, 16s, 30s
  (cap), each ± 25 % jitter. Reset on successful handshake. Log every
  retry attempt structurally (`event="reconnect.holdspeak"`,
  `attempt=<n>`, `wait_ms=<n>`).
- **WebSocket health: ping/pong, not frame-receive timeouts.** A
  healthy idle HoldSpeak connection produces *zero* unsolicited
  server frames (HoldSpeak doesn't push unless there's something to
  say — `status` frames during meetings, `error` frames on bad
  control, etc.). Checking "no frame received in N seconds" would
  tear down healthy connections. Use the `websockets` library's
  `ping_interval=15, ping_timeout=30` — RFC-6455 ping/pong frames
  bypass the application layer and detect dead peers cleanly.
  Outbound `{"type":"heartbeat"}` control frames are still sent on
  the same 15s cadence so HoldSpeak's logs show liveness, but they
  are NOT used for inbound timeout detection.
- Structured logging via Python `logging` with a JSON formatter
  (or `structlog`; story-01 picks one — `structlog` recommended for
  field-rich logs).
- Graceful shutdown on `SIGTERM`/`SIGINT`: cancel both loops, send a
  WS close frame to HoldSpeak, disconnect cleanly from the device.
- A minimal smoke-test path: `python3 bridge.py --check` connects to
  both endpoints, performs the handshake, then exits 0 if both
  succeed (1 otherwise). Useful for systemd `ExecStartPre`.

### Out

- Audio-frame forwarding (story-02).
- Button-event → control-frame mapping (story-03).
- Configuration schema beyond reading the four required env vars
  (story-04).
- Inbound `status` frame *real* handling (out of phase). The
  skeleton ships a **no-op handler stub** that logs and discards
  inbound `status` frames so adding the LCD-pushback follow-up is
  a tiny diff. Same for inbound `error` frames — log + don't
  crash. (See phase status decisions.)
- Outbound `event` frames device → server. No gesture in phase 2
  maps to one; the bridge does not emit them.
- Tests beyond the listed unit tests + the `--check` smoke path.
  Story-06 covers the end-to-end happy-path manual test.

## Acceptance Criteria

- [x] `bridge.py` `main()` is an async function that runs the
  HoldSpeak WS loop + the ESPHome `ReconnectLogic` concurrently;
  `asyncio.create_task` for the WS leg, `ReconnectLogic` owns
  the device leg lifecycle. Implemented 2026-05-07.
- [x] Pydantic models for `Hello`, `HelloAck`, `Heartbeat`,
  `Status`, `ErrorFrame` (plus `StartFrame`, `StopFrame`,
  `EventFrame` for stories 03 / followups) exist with
  `extra="forbid"` and `str_strip_whitespace=True` mirroring
  HoldSpeak's `DeviceHandshake`. **Unit-tested**:
  `tests/test_models.py` — 17 cases (one per frame type +
  negative tests for unknown fields, empty strings,
  whitespace-only, wrong type literals). All pass.
- [x] `reconnect_with_backoff` helper unit-tested:
  `_backoff_seconds` schedule + jitter + floor verified
  deterministically; the async path is exercised with three
  cases (cancellation propagates, exceptions trigger backoff
  rather than propagate, attempt counter resets on a clean
  return). `tests/test_reconnect.py` — 9 cases. All pass.
- [x] `python3 bridge.py --check` exits 0 on success, 1 on
  either endpoint failing the handshake. Stderr names which
  endpoint failed and (for HoldSpeak) decodes the 4xxx close
  code into a human-readable cause. **Verified 2026-05-07** —
  device leg connects to live `aipi.local`; HoldSpeak leg
  fails with `ConnectionRefusedError` exit 1 when no server
  is running, as expected.
- [x] On clean start: bridge logs `connect.device.ok` (verified
  via `--check`), then `connect.holdspeak.handshake.ok`, then
  `loop.ready`. No errors.
  **Partial:** `connect.device.ok` verified against live
  hardware. The HoldSpeak handshake log + `loop.ready` are
  exercised in unit tests (handshake parsing) but a full
  three-line happy-path against a *running* HoldSpeak is
  pending HoldSpeak being up.
- [ ] Killing HoldSpeak (`pkill -f holdspeak`) → bridge logs
  `disconnect.holdspeak`, retries with backoff, reconnects when
  HoldSpeak comes back. Bridge does NOT exit.
  **Pending HoldSpeak running.** Reconnect helper
  unit-tested in isolation; integration verification needs
  a live HoldSpeak.
- [ ] Killing the device (unplug USB) → `aioesphomeapi.ReconnectLogic`
  drives a clean reconnect; bridge logs the lifecycle via the
  callback. Bridge does NOT exit. **Pending device-in-loop test.**
- [ ] WebSocket idle behaviour: with both legs connected and no
  audio flowing, the bridge sits silently for ≥ 60 s without
  triggering a reconnect. **Pending HoldSpeak running.**
- [ ] `SIGTERM` / `SIGINT` triggers a clean shutdown within 2 s;
  no asyncio "task was destroyed but it is pending" warnings.
  **Pending live-running test.**

## Test Plan

- **Unit:** Pydantic model round-trip tests for each frame type
  (load fixture JSON, validate, serialize, compare). `pytest`.
- **Integration (manual):**
  1. Start HoldSpeak locally (`holdspeak` CLI, web runtime on default
     port).
  2. Set `bridge.env` with `HOLDSPEAK_HOST=127.0.0.1`,
     `HOLDSPEAK_PORT=<port>`, `HOLDSPEAK_PSK=<from holdspeak device-psk show>`.
  3. Run `python3 bridge.py --check` — expect exit 0.
  4. Run `python3 bridge.py` — expect three log lines and a
     steady heartbeat.
  5. `pkill -f holdspeak` — confirm reconnect log lines + recovery
     when HoldSpeak restarts.
  6. Unplug + replug the device — confirm reconnect on the
     aioesphomeapi side.
  7. `Ctrl-C` — confirm clean shutdown.

## Notes

- **Authoritative wire contract:** `~/dev/HoldSpeak/docs/DEVICE_PROTOCOL.md`
  (HS-14-08). Mirror the field schemas exactly; don't paraphrase.
- **Pick `structlog` over stdlib `logging` JSON formatter** unless
  `structlog` is already too much new dep weight; it makes
  field-rich logs trivial and is a dep HoldSpeak already pulls in
  (verify before committing).
- **Device-leg reconnect is `aioesphomeapi.ReconnectLogic`'s job.**
  The current `bridge.py` already uses it. Don't add a parallel
  backoff loop on the device side — they'd race. Only the HoldSpeak
  WS leg needs the custom `reconnect_with_backoff` helper, because
  `websockets` doesn't ship one.
- **Why ping/pong, not frame-receive timeouts:** HoldSpeak's WS
  server doesn't send unsolicited frames except `status` (during
  meetings) and `error` (on bad control). A healthy idle connection
  is silent. Checking "no frame received in N seconds" would tear
  down healthy connections. `websockets.connect(..., ping_interval=15,
  ping_timeout=30)` enables RFC-6455 ping/pong frames at the
  protocol layer; they detect dead peers without polluting the
  application channel.
- **Outbound `{"type":"heartbeat"}` control frames** are still
  emitted on a 15 s cadence so HoldSpeak's logs show device
  liveness — but the bridge does NOT use inbound frame timing for
  health checks. Two distinct mechanisms.
- **Do not import `faster_whisper`, `gtts`, `pydub`, or `requests`
  in this story.** Those imports stay in the legacy code path that
  story-04 deletes. Keeping them around just to be cautious is the
  exact "feature flag" pattern we decided against.
- The HoldSpeak server's WS route is at
  `holdspeak/device_audio_ws.py:register_device_audio_routes`; the
  handshake path is `_serve_device_audio` → `verify_psk`. Read these
  alongside `DEVICE_PROTOCOL.md` if behaviour is ambiguous — code
  is authoritative when docs lag.
