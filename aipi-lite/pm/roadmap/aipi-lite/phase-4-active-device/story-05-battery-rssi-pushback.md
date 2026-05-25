# AIPI-4-05 — Battery + RSSI Pushback (Device → Server)

- **Project:** aipi-lite
- **Phase:** 4
- **Status:** backlog
- **Depends on:** AIPI-2 (full phase); HoldSpeak `device_health` frame schema + handler (shipped in HS-17)
- **Unblocks:** —
- **Owner:** karol

## Problem

The device knows its battery percentage and WiFi RSSI but doesn't tell HoldSpeak. HoldSpeak could warn the user when battery is below a threshold, surface device-health alongside meeting attribution, or refuse to start a meeting on a device about to die. Currently the user has to physically look at the device.

This story is a **bridge → server initiative**: a new outbound frame type (`device_health`) carrying battery + RSSI, emitted on threshold-cross + 60s heartbeat. HoldSpeak HS-17 shipped the paired schema + handler on 2026-05-10, so this story is unblocked and backlogged for bridge-side sensor/cadence work.

## Scope

### In

- `DeviceHealth` Pydantic model in `holdspeak_proto.py`: `type="device_health"`, `battery_pct: int (0-100)`, `rssi_dbm: int (negative)`, `at: int (unix_ms)`. `extra="forbid"` like every other frame.
- Bridge subscribes to ESPHome's existing battery + WiFi RSSI sensors via aioesphomeapi `subscribe_states`.
- Bridge maintains a small cache: last-pushed (battery_pct, rssi_dbm).
- Emission rule: emit when battery changes by ≥ 5 % OR RSSI changes by ≥ 10 dBm OR every 60 s (heartbeat). Whichever comes first; reset the heartbeat after any emission.
- Frame goes out on the existing HoldSpeak WS connection (no new transport).
- Graceful handling of HoldSpeak rejecting the unknown frame (`extra="forbid"` on HS side): log + suppress emissions for the rest of the session; reset on reconnect.
- Tests: `DeviceHealth` model round-trip; emission cadence (debounce + heartbeat); rejection handling.

### Out

- HoldSpeak UI display of device health — that's the HS-side feature.
- Battery warnings *on the device* (e.g., LCD `Low battery!`) — phase-4 follow-up; not blocking.
- Charging-state distinction (`charging: true/false`) — could be added when needed; phase-4-followup.
- Predictive battery analytics (estimated minutes remaining, etc.).

## Acceptance criteria

- [x] **Blocked-on:** HoldSpeak ships `device_health` frame schema in `~/dev/HoldSpeak/docs/DEVICE_PROTOCOL.md` AND a server-side handler that updates `MeetingState.devices[i].battery_pct` / `rssi_dbm`. HS-17 shipped this on 2026-05-10.
- [ ] `DeviceHealth` Pydantic model added to `holdspeak_proto.py` with `extra="forbid"`.
- [ ] Bridge subscribes to ESPHome battery + RSSI sensors via `subscribe_states`.
- [ ] Emission cadence implemented: threshold-cross (±5 % battery, ±10 dBm RSSI) OR 60 s heartbeat.
- [ ] Bridge handles HoldSpeak rejecting unknown frame: log `device_health.rejected.suppressed` once; suppress further emissions until reconnect.
- [ ] Tests: `tests/test_models.py` adds `DeviceHealth` round-trip + invalid-input cases; `tests/test_device_health.py` tests cadence + suppression + reset-on-reconnect.
- [ ] Live verification once HS-side handler ships: drain device battery to 50 % during a meeting; verify HoldSpeak meeting view reflects updated battery_pct within ~60 s; same for RSSI by walking out of WiFi range.

## Test plan

- **Unit:** `DeviceHealth` model round-trip; cadence scheduler (mock clock + sensor-update events; assert emission count over a 5-minute simulated window).
- **Integration:** fake `websockets.serve` records emitted frames; verify cadence + content; simulate HS-side rejection, verify suppression.
- **Manual (post-paired):** observe HoldSpeak UI / API while device drains.

## Notes

- **Dependency on a paired HoldSpeak phase.** Resolved by HoldSpeak HS-17 on 2026-05-10.
- **Why not just send the frame and have HoldSpeak ignore it?** HoldSpeak's `DeviceHandshake`-style models use `extra="forbid"` in several protocol paths, so pre-HS-17 version skew could reject unexpected frames. Do not run this bridge story against older HoldSpeak builds unless suppression is verified.
- **Sensor exposure:** the existing `aipi.yaml` has `sensor.battery_voltage` (or similar) wired; need to confirm + possibly add a percentage-form sensor + the WiFi RSSI sensor. Probably small firmware addition; folded into this story when unblocked.
- **Why threshold + heartbeat, not pure-throughput:** sensor noise would otherwise spam frames. ±5 % battery is well above ADC noise; ±10 dBm RSSI is well above WiFi-radio jitter. 60 s heartbeat ensures HoldSpeak knows the device is alive even when sensor values are stable.
