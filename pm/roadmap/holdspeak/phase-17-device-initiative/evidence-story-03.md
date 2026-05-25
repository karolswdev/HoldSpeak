# Evidence — HS-17-03 — Device Health UI

- **Date:** 2026-05-10
- **Status:** done
- **Story:** [HS-17-03](./story-03-device-health-ui.md)

## What changed

- Added a compact dashboard Devices rail panel.
- Attached devices render label/id.
- Battery and RSSI render only when present.
- Missing health fields produce no placeholder.
- Stale values are muted and tagged `stale` based on host `last_seen` age.
- Runtime broadcasts `device_health` updates to the dashboard after a valid device frame updates active meeting state.

## Verification

```bash
npm run build
```

Result: passed, 7 static pages built.

```bash
.venv/bin/pytest -q tests/integration/test_web_server.py::TestDashboardEndpoint::test_dashboard_includes_device_health_surface tests/integration/test_web_server.py::TestDeviceHealthEndpoint tests/integration/test_device_audio_ingest.py::TestDeviceActiveFrames
```

Result: `7 passed in 0.88s`.

```bash
.venv/bin/pytest -q tests/unit/test_device_active_frames.py tests/unit/test_device_recording_tick.py tests/unit/test_device_status_helpers.py tests/unit/test_meeting_state.py tests/integration/test_device_audio_ingest.py tests/integration/test_device_meeting_session.py tests/integration/test_device_status_pushback.py tests/integration/test_device_audio_ingest.py
```

Result: `196 passed in 3.53s`.

## Notes

- Playwright was not installed in the local virtualenv, so no screenshot evidence was captured.
- The current web test stack covers the dashboard shell, bundled Alpine helper names, browser-readable health API, and WS/runtime update path. Real-device visual confirmation is deferred to AIPI-Lite bridge dogfood.
