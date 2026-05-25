# AIPI-1-01 - Multi-SSID + AP-Mode Fallback Config

- **Project:** aipi-lite
- **Phase:** 1
- **Status:** in-progress
- **Depends on:** none
- **Unblocks:** AIPI-1-02, AIPI-1-05
- **Owner:** karol

## Problem

`aipi.yaml`'s `wifi:` block today is single-SSID, hard-coded via
`!secret wifi_ssid` / `!secret wifi_password`. The device only
joins one network; if that network isn't reachable, it sits in a
reconnect loop forever. We need ESPHome's `wifi.networks:` list
(multiple known SSIDs, tried in order) and a `wifi.ap:` fallback
so the device boots its own AP when none of the known networks
respond.

This story does the config plumbing only — the captive portal
that serves the AP is AIPI-1-02.

## Scope

- **In:**
  - Replace `wifi.ssid` + `wifi.password` with a `wifi.networks:`
    list. Default two entries: `home` (existing creds) +
    `phone-hotspot` (placeholder; user fills in).
  - Add `wifi.ap:` block with `ssid: AiPi-Setup` and a password
    referenced from secrets.
  - `secrets.yaml.example` (or equivalent) documents the new
    fields: `wifi_ssid_home`, `wifi_password_home`,
    `wifi_ssid_phone`, `wifi_password_phone`, `wifi_ap_password`.
  - `secrets.yaml` (gitignored) updated locally to populate the
    new fields.

- **Out:**
  - `captive_portal:` component — AIPI-1-02.
  - Improv-WiFi (BLE / serial) — AIPI-1-03 / AIPI-1-04.
  - Left-button bindings — AIPI-1-05.
  - Documentation runbook — AIPI-1-06.

## Acceptance Criteria

- [x] `aipi.yaml` `wifi:` block has `networks:` (≥ 2) + `ap:`.
- [x] Build succeeds: `esphome compile aipi.yaml` exits 0.
  Evidence: 2026-05-07 — `SUCCESS Took 36.59 seconds`,
  RAM 13.5% / Flash 15.0%, image 1219539 bytes.
- [x] On flash + boot with the home SSID reachable, device joins
  home as before (verify mDNS + ping).
  Evidence: 2026-05-07 — flashed via `/dev/ttyACM0` (USB JTAG,
  MAC `10:51:db:8f:76:98`); on boot, `getent hosts aipi.local` →
  `192.168.1.44`; `ping aipi.local` → 0% loss (2/2);
  ARP confirms the MAC at that IP.
- [ ] On flash + boot with home SSID unreachable but phone
  hotspot reachable, device joins the hotspot (verify by
  switching off home WiFi + booting; device's IP is reachable
  on the hotspot's subnet). **Pending hardware test.**
- [ ] On flash + boot with neither known network reachable,
  device starts the `AiPi-Setup` AP (verify by scanning for
  the SSID from a phone — the captive portal redirect comes in
  AIPI-1-02; just the AP being visible is enough for this
  story). **Pending hardware test.**

## Test Plan

- Unit: n/a (firmware config).
- Integration: `esphome compile aipi.yaml` for build cleanliness.
- Manual: three boot-and-verify scenarios above.

## Notes

- Keep the existing `home` network as the first entry so the
  default behavior is unchanged for users who don't fill in the
  phone-hotspot placeholder.
- ESPHome `wifi.ap:` requires a password ≥ 8 chars; document
  this in the secrets template.
- The AP uses the device's own IP space (default 192.168.4.x).
  No conflict with home networks expected since the AP only
  exists when the device is *not* on a known network.
