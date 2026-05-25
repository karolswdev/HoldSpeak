# Evidence — HS-17-01 — Device Health Frame

- **Date:** 2026-05-10
- **Status:** done
- **Story:** [HS-17-01](./story-01-device-health-frame.md)

## What changed

- Added `DeviceHealthFrame` with strict Pydantic validation:
  - `battery_pct` constrained to `0..100`
  - `rssi_dbm` constrained to `-120..0`
  - unknown fields rejected
- Extended `DeviceDescriptor` with `battery_pct`, `rssi_dbm`, and `last_health_at`.
- Added `DeviceRegistry.update_health(...)`.
- Added WS dispatch for `{"type":"device_health", ...}` frames.
- Added active-meeting descriptor refresh via `MeetingSession.update_device_descriptor(...)`.
- Added `GET /api/devices/health`.
- Extended `docs/DEVICE_PROTOCOL.md`.

## Verification

```bash
.venv/bin/pytest -q tests/unit/test_device_active_frames.py tests/integration/test_device_audio_ingest.py tests/integration/test_device_meeting_session.py tests/unit/test_meeting_state.py
```

Result: included in focused run, `170 passed in 1.56s`.

```bash
.venv/bin/python -m compileall -q holdspeak/device_audio.py holdspeak/device_audio_ws.py holdspeak/meeting_session.py holdspeak/web_server.py holdspeak/web_runtime.py
```

Result: passed.

## Notes

- Invalid health frames are logged and dropped; the WebSocket stays open.
- State is intentionally in-memory. No battery/RSSI history was added.
