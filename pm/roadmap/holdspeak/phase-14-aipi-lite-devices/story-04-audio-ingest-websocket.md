# HS-14-04 - `/api/devices/audio` WebSocket + Backpressure

- **Project:** holdspeak
- **Phase:** 14
- **Status:** done
- **Depends on:** HS-14-01, HS-14-02, HS-14-03
- **Unblocks:** HS-14-05, HS-14-06, HS-14-07
- **Owner:** unassigned

## Problem

Wire the substrate into a real network surface. A FastAPI WebSocket
route accepts the device's first JSON handshake, validates the PSK,
registers the device with the registry, then loops: alternating
control messages (start/stop/heartbeat) and binary PCM frames. The
server can also push status messages back the other way (lit up by
HS-14-07).

Backpressure: per-device bounded queue. Default 2 s of audio
@ 16k mono int16 = 64 KB. On overflow, drop the oldest frame and
emit a structured warning (`device.queue.overflow` with `device_id`,
`dropped_bytes`).

## Scope

- **In:**
  - New module `holdspeak/device_audio_ws.py` (or a function in
    `holdspeak/web_server.py` referencing helpers in
    `device_audio.py`) wiring `WebSocket /api/devices/audio`.
  - Handshake flow: receive JSON → validate via
    `DeviceHandshake` (HS-14-03) → check PSK → call
    `registry.register(id, label)` → ack
    `{type: "hello-ack", device_id}` → enter dispatch loop.
  - Dispatch loop:
    - JSON frame `{type: "start"}` — calls
      `recorder_for(id).start_recording()`.
    - JSON frame `{type: "stop"}` — calls `stop_recording()` and
      hands the result off to the consumer set by HS-14-05 /
      HS-14-06.
    - JSON frame `{type: "heartbeat"}` — refreshes `last_seen`.
    - Binary frame — passed to `recorder.push(bytes)`.
  - Backpressure: bounded queue in `RemoteAudioRecorder` (already
    introduced minimally in HS-14-01); structured logging on
    overflow; emit `device.queue.overflow` with `device_id` +
    `dropped_bytes` count.
  - On client disconnect (clean or abrupt): unregister device,
    cancel any in-flight recording, log.
  - Bind to 127.0.0.1 like all of HoldSpeak's HTTP surface. The
    AIPI-Lite-side bridge connects from the same machine.
  - Integration test
    `tests/integration/test_device_audio_ingest.py`: opens a
    WS client, completes handshake, pushes 1 s of synthetic
    16k mono int16 audio, calls stop, asserts the resulting
    ndarray length and sample-rate.

- **Out:**
  - Voice-typing wiring — HS-14-05.
  - Meeting wiring — HS-14-06.
  - Server-to-device status push — HS-14-07.
  - Cross-network exposure (TLS, public URL) — phase 15.

## Acceptance Criteria

- [x] `WebSocket /api/devices/audio` endpoint exists in the
  FastAPI app.
- [x] Bad handshake closes with code 4001; bad PSK with 4003;
  duplicate label with 4009.
- [x] After successful handshake, the device id appears in
  `registry.active()`.
- [x] Binary frames during a recording are buffered and emerge
  in `stop_recording()`'s ndarray.
- [x] Queue overflow drops oldest, logs once per overflow event
  (not per dropped frame), updates `descriptor.queue_depth`.
- [x] Client disconnect — clean or rude — unregisters the device
  cleanly (no leaked recorder).
- [x] `tests/integration/test_device_audio_ingest.py` is green.
- [x] No regression in existing FastAPI route tests.

## Test Plan

- Unit: helpers tested in HS-14-01..03 cover most internals.
- Integration:
  `uv run pytest tests/integration/test_device_audio_ingest.py`.
  Add a backpressure case that asserts overflow drops
  oldest-first by sending audio faster than `stop_recording` can
  drain (use a controllable mock recorder).
- Manual: `wscat` against `ws://localhost:PORT/api/devices/audio`,
  send the handshake JSON manually, push a recorded WAV's PCM
  frames, verify `/api/runtime/status` shows the device
  registered.

## Notes

- WebSocket framing: JSON for control (`text` frames), raw PCM
  for audio (`binary` frames). FastAPI's `WebSocket.iter_text()`
  + `iter_bytes()` aren't both consumable concurrently; use
  `receive()` and dispatch on `type`.
- Why no protobuf / msgpack: PCM is already binary; control is
  rare. JSON is fine and grep-friendly.
- The bridge (AIPI-Lite repo) is responsible for buffering on
  flaky LAN — this server side just consumes what arrives.
- Cross-repo: bridge protocol translator is AIPI-2 in the
  AIPI-Lite roadmap. Manual smoke test for this story uses
  `wscat` rather than the actual device, to keep this story
  hermetic.
