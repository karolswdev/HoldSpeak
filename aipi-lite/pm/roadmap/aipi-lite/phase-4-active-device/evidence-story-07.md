# Evidence — AIPI-4-07 — Remote Gesture Simulation Services + Bridge CLI

- **Shipped:** 2026-05-10
- **Commit:** pending close-out commit on branch `mine` (working tree)
- **Owner:** karol

## Files touched

### Firmware (`aipi.yaml`)

- New ESPHome API services:
  - `simulate_left_press(duration_ms: int)` — publishes `left_button_sim` ON, delays `duration_ms`, publishes OFF. Bridge subscribes via `subscribe_states` and runs the same short-vs-long classifier as for real `left_button` presses.
  - `simulate_voice_typing(duration_ms: int)` — calls `voice_assistant.start`, delays `duration_ms`, calls `voice_assistant.stop`. Tests the firmware → UDP → bridge → HoldSpeak audio path without needing a meeting.
- New template binary_sensor `left_button_sim` (no GPIO; API-driven). `name: "left_button_sim"` (alphanumeric+underscore identity — see "Lessons learned").
- New `ota: - platform: esphome` block so future flashes can be over-the-air. Previous firmware lacked it; AIPI-4-07's first flash was USB-only because the *running* firmware needed an `esphome` OTA endpoint to receive updates.

### Bridge (Python)

- `bridge/device.py` — `_left_button_sim_key` field; `_cache_button_entities` resolves both real and sim keys; `_handle_state_change` dispatches on either match; `_on_disconnect` invalidates both keys.
- `bridge/cli.py` — new `_press(client, services_by_name, gesture, log, *, settle_s=None)` helper (testable; tests pass `settle_s=0`); `_remote_press(settings, gesture)` integration wrapper that creates an APIClient, lists services, calls `_press`, disconnects; new `--press {left-short, left-long, voice-typing}` argparse mode.

### Tests

- `tests/test_remote_press.py` — 6 cases covering each gesture's service-name + duration_ms mapping (`left-short`→100ms, `left-long`→6000ms, `voice-typing`→3000ms), missing-service error path, unknown-gesture defensive check, execute-service error path.
- `tests/test_bookmark_gesture.py` extended with 4 dual-key dispatch cases: sim-key alongside real; sim-only; sim-key state event triggers classifier; both keys both work.

### Documentation

- `docs/HOLDSPEAK_BRIDGE.md` §9 "Remote gesture testing" — three `--press` invocations, firmware prerequisite, disconnect-race lesson learned.

## Verification artifacts

```
$ .venv/bin/python -m pytest -q
131 passed in 2.82s

$ .venv/bin/ruff check .
All checks passed!

$ .venv/bin/python -m bridge --check  # post-flash, post-fix
{"port": 50000, "event": "check.udp.ok", ...}
{"host": "aipi.local",
 "services": ["force_toggle_mode",
              "simulate_left_press",
              "simulate_voice_typing",
              "update_link",
              "update_screen"],
 "event": "check.device.ok", ...}
```

**Live-hardware verification (2026-05-10):**

Compile + USB flash on `/dev/ttyACM0` succeeded; reboot clean; `--check` confirmed the new services + clean removal of the old `prepare_speaker`/`restore_mic` (AIPI-2-08 cleanup) + presence of `update_link` (AIPI-2-07 LCD pushback).

`python -m bridge --press left-short` outside any meeting → 5 invocations, all logged `event.suppressed gesture=bookmark reason=not_in_meeting` (timestamps in bridge log: 20:51:59, 20:52:02, 20:53:39, 20:55:13, 20:57:07). Zero spurious meeting bookmarks.

`python -m bridge --press voice-typing` → bridge log:

```
20:57:39.527  device.voice_assistant.start  (conversation_id="" sample_rate=1 udp_audio_port=50000)
20:57:42.488  device.voice_assistant.stop   (cancelled=True)
20:57:42.928  press.fired                   (gesture=voice-typing duration_ms=3000)
```

Exact 3 s duration between `start` and `stop`. End-to-end transcription (audio → HoldSpeak → host typing) was not re-tested via the simulate path because typing into a live host window during an automated session is intrusive; the downstream code is the same as AIPI-2-02's voice typing flow which shipped verified 2026-05-08.

`python -m bridge --press left-short` inside a HoldSpeak meeting → bookmark in transcript at `timestamp: 15.62406s`. Full chain: see [`evidence-story-01.md`](./evidence-story-01.md).

## Acceptance criteria — re-checked

- [x] `aipi.yaml` defines `left_button_sim` template binary_sensor + `simulate_left_press` + `simulate_voice_typing` API services. Compile + USB flash via `/dev/ttyACM0` succeeded 2026-05-10. `ota: - platform: esphome` added; future flashes can be OTA.
- [x] `bridge/device.py` resolves both `left_button` and `left_button_sim` keys on connect; dispatches state changes from either to the existing classifier — verified live (gestures fired via the simulate path triggered the same `_fire_bookmark_attempt` chain as real presses would).
- [x] `bridge/cli.py` accepts `--press {left-short, left-long, voice-typing}`; helper connects, calls the matching service with the right `duration_ms`, exits 0 on success / 1 on missing-service / 1 on connection error — verified by the test suite (6 cases) and by live invocations.
- [x] Tests: dual-key dispatch + CLI helper coverage; 131/131 passing; ruff clean.
- [x] Live-hardware verification — see live trace above; both in-meeting + out-of-meeting paths verified; voice-typing firmware-bridge integration verified.
- [x] Documentation update — `docs/HOLDSPEAK_BRIDGE.md` §9 added.

## Deviations from plan

- **Two bugs surfaced + fixed during live verification:**
  1. **`object_id` mismatch.** ESPHome derives the API `object_id` from the *display name*, not the `id:` field. `name: "Left Button (sim)"` became `left_button__sim_` (parens + space → underscores). Bridge's filter on `object_id == "left_button_sim"` silently missed it. Fixed by setting `name: "left_button_sim"` (alphanumeric+underscore identity). Lesson: ESPHome's name → object_id derivation eats non-alphanumeric chars; for entities that need a stable API name, prefer name-without-special-chars OR set `object_id:` explicitly.
  2. **Disconnect-after-execute race.** `client.execute_service()` returns after queuing the frame, not after the firmware finishes the script. Immediate `disconnect()` was racing the firmware's `binary_sensor.template.publish` and silently dropping the state changes. Fixed with a `duration_ms / 1000 + 0.5` settle wait before disconnect; tests skip via `settle_s=0` parameter so the suite stays at 2.8 s. Lesson saved as a runbook §9 note for future agents touching this code.
- **OTA was not available on the previous firmware.** ESPHome 2026.4 auto-injects `ota: - platform: web_server` but `esphome upload` only does OTA via `ota: - platform: esphome`. First flash had to be USB; added an explicit `ota: - platform: esphome` block so future flashes can OTA.
- **`esphome upload` doesn't compile by default.** First flash attempt silently flashed a stale cached binary (reused `.esphome/build/aipi/.pioenvs/aipi/firmware.bin` from before this story's edits). Workaround: explicit `esphome compile` then `esphome upload`, or `esphome run --no-logs` which always compiles. Worth noting in any future runbook touching ESPHome flashing.

## Follow-ups

- None outstanding. The `simulate_left_press` + `simulate_voice_typing` substrate is sufficient for current bridge-side gesture verification needs. If new gestures get added (e.g., bookmark-from-quick-tap-other-button, mode-cycle from a triple-tap), the same pattern extends naturally — add a new `simulate_*` service + a CLI gesture mapping.
