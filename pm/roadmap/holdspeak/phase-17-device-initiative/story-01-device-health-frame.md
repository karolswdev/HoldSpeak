# HS-17-01 — `device_health` Frame: Schema + Handler + State Extension

- **Project:** holdspeak
- **Phase:** 17
- **Status:** done
- **Depends on:** HS-14 (full phase — device WS substrate)
- **Unblocks:** HS-17-03, AIPI-4-05 (device-side bridge stories)
- **Owner:** karol

## Problem

The AIPI-Lite device knows its battery percentage and WiFi RSSI but has no way to tell HoldSpeak. AIPI-Lite roadmap story AIPI-4-05 (battery + RSSI pushback) is sitting `blocked` because the wire schema + server handler don't exist yet. This story lights up the device → server side: accept `device_health` frames, store last-known values per device, expose them via the device registry and active meeting descriptors, and make the values available to the web runtime.

## Scope

### In

- New inbound WS frame type in `holdspeak/device_audio_ws.py`:
  ```
  {"type": "device_health", "battery_pct": int (0-100), "rssi_dbm": int (typically -100..-30), "at": int (unix_ms)}
  ```
  Pydantic model in `holdspeak/device_audio.py` (or wherever the existing WS frame models live) with `extra="forbid"`.
- Handler: on receipt, update the device registry descriptor for the WS connection's `device_id`. If a meeting is active and has an attached descriptor for the same device, its exposed snapshot reflects the same health fields.
- State extension: the device registry's descriptor gains `battery_pct: int | None`, `rssi_dbm: int | None`, `last_health_at: int | None`. Active `MeetingState.devices[i]` snapshots expose those fields when present.
- API read path: add `GET /api/devices/health` or extend the existing runtime status API with `battery_pct` / `rssi_dbm` / `last_health_at` in each device descriptor. Backwards-compatible additive fields only.
- Validation: `battery_pct` and `rssi_dbm` use strict Pydantic bounds. Out-of-range values are invalid, logged, and dropped; they are not clamped. The WS stays open.
- Protocol-doc update: `docs/DEVICE_PROTOCOL.md` gains a "device_health" section with the schema + example + field semantics. (HS-17-04 will consolidate the doc; this story lands the additive update.)
- Integration test `tests/integration/test_device_health_pushback.py`: open a WS, complete handshake, send a `device_health` frame, assert state updated; send an invalid frame, assert WS stays open + frame dropped.
- Unit tests for the Pydantic model: round-trip + validation (out-of-range battery, out-of-range RSSI, missing field, extra field).

### Out

- Time-series persistence of device-health history (in-memory last-value only).
- Battery/RSSI thresholds + alerting UI (HS-17-03 ships the read-only display; alerting is a follow-up).
- Health emissions when NO meeting is active should still update the device registry. Meeting state is a consumer/snapshot, not the canonical health store.
- Charging-state distinction (`charging: bool`) — additive followup if needed.

## Acceptance Criteria

- [x] `DeviceHealthFrame` Pydantic model defined with `extra="forbid"`; `battery_pct: int = Field(ge=0, le=100)`; `rssi_dbm: int = Field(ge=-120, le=0)`; `at: int`.
- [x] WS handler in `holdspeak/device_audio_ws.py` dispatches `type=="device_health"` to the device-state setter.
- [x] Device registry descriptor extended with `battery_pct`, `rssi_dbm`, `last_health_at`; active meeting device snapshots expose those values when attached.
- [x] Existing JSON serializations (meeting view, API responses) include the new fields when present, null when absent.
- [x] `GET /api/devices/health` returns the new fields.
- [x] Invalid frames (out-of-range values, missing required fields, extra fields) are logged + dropped; WS stays open.
- [x] `docs/DEVICE_PROTOCOL.md` gains a `device_health` section.
- [x] Integration coverage in `tests/integration/test_device_audio_ingest.py` covers valid frame, health API projection, callback projection, and invalid-frame survival.
- [x] Unit tests for `DeviceHealthFrame` round-trip + validation.

## Test Plan

- **Unit:** `tests/unit/test_device_health_model.py` — Pydantic round-trip + each validation failure mode.
- **Integration:** `tests/integration/test_device_health_pushback.py` — WS handshake + send-frame + assert-state + invalid-frame survival.
- **Manual (post-AIPI-4-05):** real AIPI-Lite device drains battery during a meeting; observe the chosen runtime/meeting API reflecting decreasing `battery_pct` within ~60 s; same for RSSI by walking out of WiFi range.

## Notes

- **WS-stays-open on invalid frame** is deliberate. Killing a meeting because the device sent a malformed health update would be a worse failure mode than ignoring the frame. Log loudly enough for ops; don't escalate.
- **Where state lives** — the registry is the canonical home. `MeetingState.devices[i]` is a meeting-facing projection so the UI does not need to join two state sources.
- **Field naming:** `battery_pct` and `rssi_dbm` chosen over `battery_percentage` and `rssi` because they're unambiguous about units. Tiny lift; consistent with codebase conventions.
- **Backwards compatibility:** older AIPI-Lite bridges (pre-AIPI-4-05) never emit this frame, so the absence is the default. Older HoldSpeak versions with `extra="forbid"` on the WS-dispatch model would reject — but AIPI-4-05's contract handles rejection by suppressing further emission for the session, so the failure mode is graceful.
