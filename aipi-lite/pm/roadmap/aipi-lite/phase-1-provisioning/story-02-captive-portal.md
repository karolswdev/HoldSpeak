# AIPI-1-02 - Captive Portal for New-Network Setup

- **Project:** aipi-lite
- **Phase:** 1
- **Status:** in-progress
- **Depends on:** AIPI-1-01
- **Unblocks:** AIPI-1-06
- **Owner:** karol

## Problem

With AIPI-1-01 the device starts an AP when no known network
responds, but there's no UI on it — the AP is just an open
network. The user needs a way to enter a new SSID + password
from a phone or laptop without touching firmware. ESPHome's
`captive_portal:` component does exactly this: a tiny HTTP
server that pops up automatically when a device joins the AP,
shows a config page, accepts new credentials, persists them to
NVS, and reboots the device into client mode on the new network.

## Scope

- **In:**
  - Add `captive_portal:` component (no config needed; defaults
    are fine).
  - Update the LCD top label to display `Setup-AP` (or similar
    short string) when the device is in AP mode, so the user
    knows to expect a captive portal.
  - Confirm the captive portal is reachable at the AP's gateway
    IP from a phone (auto-redirect on iOS/Android; manual
    `http://192.168.4.1` on stubborn clients).

- **Out:**
  - Customizing the captive portal HTML — defaults are sufficient
    for v1.
  - Improv-WiFi BLE — AIPI-1-03.
  - Left-button-triggered AP-mode entry (when a known network
    *is* reachable but the user wants to re-provision) — AIPI-1-05.

## Acceptance Criteria

- [x] `aipi.yaml` includes `captive_portal:` and compiles cleanly.
  Evidence: 2026-05-07 — `esphome compile` SUCCESS, 48.15s,
  RAM 17.6% / Flash 20.1%.
- [ ] When the device is in AP mode, joining `AiPi-Setup` from a
  phone triggers the OS's captive-portal popup → ESPHome's config
  page renders. **Pending hardware test (gated on AIPI-1-01
  scenario 3 — needs both known networks unreachable to enter AP).**
- [ ] Submitting a new SSID + password on the page persists the
  creds and reboots the device into client mode on the new
  network (verify by confirming the device gets an IP on the
  new network). **Pending hardware test.**
- [x] LCD top label reads `Setup-AP` (or equivalent) while in AP
  mode and reverts to the existing mode label
  (`Hold-to-talk` / `Always listening`) once back on a client
  network. *Logic in place:* `refresh_mode_label` script now
  branches on the `wifi.connected:` condition and is fired by
  `wifi.on_connect` / `wifi.on_disconnect`. Visual confirmation
  on hardware still pending (gated on entering AP mode).

## Test Plan

- Unit: n/a.
- Integration: `esphome compile aipi.yaml` clean.
- Manual:
  1. Boot the device with neither known network present.
  2. Phone joins `AiPi-Setup`; verify captive portal appears.
  3. Enter test SSID + password; verify device reconnects.
  4. Verify LCD label transitions correctly.

## Notes

- ESPHome's captive portal automatically saves credentials to
  the existing `wifi.networks:` slot (or appends — confirm
  behavior from docs). Either way, the user gets a connected
  device after one round-trip.
- Skip the static asset bundling work; the upstream HTML is
  fine.
- If a user wants to forget a network later, hold-during-boot
  reset (AIPI-1-05) wipes everything.
