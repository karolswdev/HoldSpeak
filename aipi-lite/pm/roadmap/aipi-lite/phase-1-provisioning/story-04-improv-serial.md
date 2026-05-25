# AIPI-1-04 - improv_serial USB Recovery

- **Project:** aipi-lite
- **Phase:** 1
- **Status:** in-progress
- **Depends on:** none
- **Unblocks:** AIPI-1-06
- **Owner:** karol

## Problem

If BLE is unavailable (older phone, BLE permissions revoked, etc.)
*and* the captive portal is unreachable (e.g., the user
inadvertently hard-set the device to a network they no longer have
access to and the AP fallback never triggers because the device
*can* see that network even though the user can't authenticate to
it), the only path back is reflashing — which is a high-friction
recovery for what should be a config change.

`improv_serial:` is the same Improv-WiFi standard but over USB
serial. The official ESPHome flasher web tool (improv-wifi.com)
or any Improv-WiFi-compatible CLI can push creds via the device's
USB-Serial/JTAG.

## Scope

- **In:**
  - Add `improv_serial:` to `aipi.yaml`. No config needed; defaults
    fine.
  - Verify the path: plug device into USB, open
    `https://www.improv-wifi.com/`, click "Connect", push creds.
  - Confirm the device picks up the new credentials and reconnects
    without reflashing.

- **Out:**
  - Custom serial protocol (Improv-WiFi is the standard).
  - Bundled CLI tool (the web flasher is sufficient).

## Acceptance Criteria

- [x] `aipi.yaml` includes `improv_serial:` and compiles cleanly.
  Evidence: 2026-05-07 — single-line addition. Bundled into the
  same compile cycle as AIPI-1-02/03; SUCCESS in 48.15s.
- [ ] Connect via the Improv-WiFi web flasher; verify the device
  identifies as Improv-capable. **Pending hardware test.**
- [ ] Push a test SSID + password via the web flasher; verify the
  device reconnects to the new network without a reflash.
  **Pending hardware test.**

## Test Plan

- Unit: n/a.
- Integration: `esphome compile aipi.yaml` clean.
- Manual:
  1. Provision the device onto a *bad* SSID via captive portal
     to deliberately break it.
  2. Plug into USB.
  3. Use the Improv-WiFi web flasher to push correct creds.
  4. Verify recovery without `esphome upload`.

## Notes

- `improv_serial` shares the USB-Serial/JTAG with normal logging /
  flashing. If conflicts surface, ESPHome docs note workarounds.
- This is the "I'm completely stuck" path. Document it in
  `docs/PROVISIONING.md` (AIPI-1-06).
