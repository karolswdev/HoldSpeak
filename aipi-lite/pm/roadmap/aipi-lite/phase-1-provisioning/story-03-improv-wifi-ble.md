# AIPI-1-03 - Improv-WiFi BLE Provisioning

- **Project:** aipi-lite
- **Phase:** 1
- **Status:** in-progress
- **Depends on:** none
- **Unblocks:** AIPI-1-06
- **Owner:** karol

## Problem

The captive portal works but has rough edges: iOS sometimes
declines to auto-pop, Android's "no internet" warnings can
disconnect users mid-config, and typing a long WPA2 password on
a captive-portal page is fiddly. **Improv-WiFi** is an open
standard for sending WiFi credentials over BLE (or serial); the
official iOS / Android **Improv-WiFi** apps render a clean
pairing flow. ESPHome ships `esp32_improv:` for the BLE half.

## Scope

- **In:**
  - Add `esp32_improv:` to `aipi.yaml` with `authorizer: none`
    (single-user product; no in-device confirmation step
    required).
  - Verify BLE coexistence with the existing audio pipeline
    (octal PSRAM headroom, 240 MHz CPU, ESP32-S3 BT LE 5).
  - Confirm pairing flow with the official Improv-WiFi mobile app
    (iOS or Android, whichever is at hand): scan → discover
    "AiPi" → enter SSID + password → device joins.

- **Out:**
  - Custom mobile app (use the official Improv-WiFi app).
  - In-device authorizer (button confirmation) — defer until
    multi-user need surfaces.
  - improv_serial — AIPI-1-04 (separate transport, same standard).

## Acceptance Criteria

- [x] `aipi.yaml` includes `esp32_improv:` and compiles cleanly.
  Evidence: 2026-05-07 — added with `authorizer: none`. Compile
  SUCCESS, 48.15s. BLE stack pulled into the image: RAM 13.5% →
  17.6%, Flash 15.0% → 20.1%. Within budget; octal PSRAM headroom
  unaffected.
- [ ] Audio loop (Whisper transcribe + LLM round-trip) still
  works correctly with BLE active — no glitches in capture or
  playback. **Pending hardware test.**
- [ ] The official Improv-WiFi mobile app discovers the device
  during BLE scan (when device is in AP mode or just generally
  advertising — `esp32_improv` advertises whenever WiFi isn't
  configured or whenever `authorizer` permits).
  **Pending hardware test.**
- [ ] Pushing creds from the app provisions the device onto a
  new SSID without USB + without captive portal.
  **Pending hardware test.**

## Test Plan

- Unit: n/a.
- Integration: `esphome compile aipi.yaml` clean.
- Manual:
  1. Boot the device.
  2. Open Improv-WiFi app on phone, scan; verify device appears.
  3. Send creds for a new SSID; verify device reconnects.
  4. While provisioned + on WiFi: kick off a 30-sec voice
     interaction; verify no audio drops attributable to BLE.

## Notes

- ESP32-S3 supports BT LE 5; coexistence with WiFi is well-supported
  in ESP-IDF. The risk is memory pressure under heavy concurrent
  workloads; octal PSRAM mitigates.
- `authorizer: none` means anyone in BLE range can pair. For a
  single-user product on a personal device, the trade-off is
  acceptable — see "Decisions deferred" in `current-phase-status.md`
  for when to revisit.
- No bridge changes for this story; provisioning is purely
  device-side.
