# AIPI-4-07 — Remote Gesture Simulation Services + Bridge CLI

- **Project:** aipi-lite
- **Phase:** 4
- **Status:** done
- **Depends on:** AIPI-4-01 (the gesture pipeline this story exercises remotely)
- **Unblocks:** Hardware verification of AIPI-4-01 from anywhere on the LAN
- **Owner:** karol

## Problem

The AIPI-Lite is a small physical device with two buttons. Hardware verification of bridge-side gestures (AIPI-4-01 bookmark; AIPI-4-04 LVGL symbols; AIPI-2-* voice typing path) requires *physical* button presses — which means being co-located with the device. When the device is across the house (or across the LAN), a quick verification pass turns into a trip to wherever the hardware lives.

This story adds **remote gesture simulation**: ESPHome API services on the device that fire the same firmware-side state changes a real button press does, plus a bridge CLI subcommand that triggers them from anywhere with LAN access to the device's API port.

This is **dev infrastructure**, not a product feature. End users don't fire `--press` from their laptops; they press the button. The story exists because the bridge-side AIPI-4-01 work outpaced its hardware verification, and the friction of "go to the basement to press one button" is high enough to compound across iteration cycles.

## Scope

### In

- `aipi.yaml` additions:
  - **New template binary_sensor `left_button_sim`** that mirrors a remote-fired left-button press. Bridge subscribes to its state changes alongside the real `left_button` and runs the same classifier; pre-existing AP-mode-entry firmware logic on `left_button` stays untouched.
  - **New ESPHome API service `simulate_left_press`** (variable: `duration_ms: int`): publishes `left_button_sim` ON, waits `duration_ms`, publishes OFF. The bridge sees the state edges via `subscribe_states` and runs `_handle_left_button_state` — the same code path a real press triggers.
  - **New ESPHome API service `simulate_voice_typing`** (variable: `duration_ms: int`): calls `voice_assistant.start`, waits `duration_ms`, calls `voice_assistant.stop`. Tests the audio capture path end-to-end (firmware → bridge → HoldSpeak) without needing a meeting in HoldSpeak.
- `bridge/device.py` extension:
  - `_cache_button_entities` resolves both `left_button` and `left_button_sim` keys on connect.
  - `_handle_state_change` dispatches when `state.key` matches *either* key — same downstream classifier; no duplicate logic.
  - `_on_disconnect` invalidates both cached keys.
- `bridge/cli.py` extension:
  - New mutually-exclusive argparse mode `--press {left-short, left-long, voice-typing}`.
  - `_remote_press(settings, gesture)` connects to the device's API, looks up the matching service, calls `execute_service` with the appropriate `duration_ms`, exits 0 on success, 1 on error. Exits cleanly without touching HoldSpeak (the running bridge process — if any — handles the wire-side emission).
  - Mapping: `left-short=100ms` (well under the 500 ms classifier threshold), `left-long=6000ms` (well over typical AP-mode-entry threshold), `voice-typing=3000ms` (3 s of audio).
- Tests:
  - `tests/test_bookmark_gesture.py` extended with dual-key dispatch cases (state from `left_button_sim` key fires the same classifier; sim-key absent doesn't break dispatch).
  - `tests/test_remote_press.py` — `_press` helper unit tests covering each gesture's service-name + duration_ms mapping, missing-service error path, malformed gesture rejection.
- Documentation: `docs/HOLDSPEAK_BRIDGE.md` "Troubleshooting" section gains a "Remote gesture testing" subsection covering the `--press` flow + the OTA-flash prerequisite.

### Out

- Truly-cross-network gesture firing (over Tailscale / Cloudflare Tunnel). Same-LAN only — that's AIPI-3 territory.
- A persistent "remote control" daemon. `--press` is one-shot; reconnects on each invocation. If users invoke it dozens of times per minute we revisit, but for verification cadence one-shot is fine.
- Right-button binary_sensor simulation. The bridge subscribes to `voice_assistant` events on the right button, not the binary_sensor itself; `simulate_voice_typing` covers that path more directly.
- Custom `duration_ms` per CLI invocation. Three named gestures with fixed durations cover the main verification paths; flexibility comes via direct `aioesphomeapi` scripting if needed.
- Recording / playback of gesture sequences. One press per invocation; sequencing is shell-script territory.

## Acceptance Criteria

- [x] `aipi.yaml` defines `left_button_sim` template binary_sensor + `simulate_left_press` + `simulate_voice_typing` API services. Compile + USB flash via `/dev/ttyACM0` succeeded 2026-05-10. Also added explicit `ota: - platform: esphome` block so future flashes can be OTA (running firmware now exposes the `esphome` OTA endpoint; first flash had to be USB because previous firmware lacked it).
- [x] `bridge/device.py` resolves both `left_button` and `left_button_sim` keys on connect; dispatches state changes from either to the existing classifier.
- [x] `bridge/cli.py` accepts `--press {left-short, left-long, voice-typing}`; helper connects, calls the matching service with the right `duration_ms`, exits 0 on success / 1 on missing-service / 1 on connection error.
- [x] Tests: dual-key dispatch + CLI helper coverage; full suite stays green.
- [x] Live-hardware verification (2026-05-10):
  - `python -m bridge --press left-short` while a HoldSpeak meeting is active → bookmark appeared in transcript at `timestamp: 15.62406s` (label `Bookmark @ 00:15`); LCD painted `Bookmark  \!//` then `Bookmark @ 16s  \!//` (server confirmation); sticky `Recording 00:00   *` restored after TTL.
  - `python -m bridge --press left-short` outside a meeting → 5 invocations all logged `event.suppressed reason=not_in_meeting`; zero transcript bookmarks.
  - `python -m bridge --press voice-typing` → bridge logged `device.voice_assistant.start` at 20:57:39 + `device.voice_assistant.stop` at 20:57:42 (3 s duration confirmed). End-to-end transcription path is the same code as AIPI-2-02's voice-typing flow (already verified live 2026-05-08); not re-tested via the simulate path because typing into a live host window during an automated session is intrusive — accept the audit trail.
- [x] Documentation: `docs/HOLDSPEAK_BRIDGE.md` §9 "Remote gesture testing" added — covers the three `--press` invocations, firmware prerequisite, and the disconnect-race lesson learned during live verification.

## Test Plan

- **Unit:** `tests/test_remote_press.py` — `_press(client, services, gesture, log)` parametrized over the three gestures + missing-service fallback + bad-gesture rejection (the argparse `choices=` should make the latter unreachable, but a defensive raise belongs there anyway).
- **Integration:** `tests/test_bookmark_gesture.py` extended — sim-key state events fire the bookmark gesture indistinguishably from real-key events.
- **Manual (post-flash):** the three `--press` invocations against a live device + live HoldSpeak. Acceptance bracket above lists the expected observations.

## Notes

- **Why a template binary_sensor and not just an event:** the bridge's existing classifier consumes `subscribe_states` callbacks. Reusing that path means zero divergence between real and simulated press handling. Adding a parallel "simulated event" channel would create a second code path that could silently rot.
- **Why `simulate_voice_typing` calls `voice_assistant.start`/`stop` directly instead of simulating the right-button binary_sensor:** the bridge subscribes to `voice_assistant` events, not the right-button binary_sensor state, so simulating the binary_sensor wouldn't fire the audio path. Calling `voice_assistant.start`/`stop` from the firmware is exactly what the right-button handler does anyway.
- **Flash prerequisite is unavoidable.** This story adds firmware surface; no firmware-flash, no remote control. OTA on this build has been flaky historically (per phase-1 notes), so plan for one USB-cable session minimum.
- **Naming intent:** `simulate_*` rather than `press_*` so it's obvious from the service name that this is dev/test infra, not a production gesture.
- **Why `voice_assistant.start` from a service is safe even if a session is already active:** the firmware's voice_assistant component handles re-entrant `start` calls gracefully; worst case the in-progress session ends and a new one begins. Not a problem for verification.
- **Open question for hardware verification:** does ESPHome's `voice_assistant.start` action reliably trigger the UDP audio path the same way a real `voice_assistant.on_start` trigger does? Should be equivalent (it's the same trigger), but the live-test bracket above confirms it. If it doesn't, fall back to a different verification path or open a follow-up.
