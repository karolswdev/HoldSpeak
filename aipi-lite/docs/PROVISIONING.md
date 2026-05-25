# AIPI-Lite Provisioning Runbook

This is the canonical guide for getting an AIPI-Lite onto a network —
whether you're flashing a fresh device, swapping networks on the road,
or recovering one that's wedged on creds you no longer have.

The device exposes **four** provisioning paths, listed in order of
expected friction (lowest first). Each one is described below, plus a
**factory-reset gesture** at the bottom for the "I'm completely stuck"
case.

---

## TL;DR

| Situation | Path |
|---|---|
| First time flashing | [§1 First-time flash](#1-first-time-flash) |
| Already-flashed device on a known network | nothing to do — it auto-joins |
| Already-flashed device on an unknown network | [§2 Captive portal](#2-re-provision-via-captive-portal) or [§3 Improv-WiFi BLE](#3-re-provision-via-improv-wifi-ble) |
| Device is wedged, AP fallback isn't kicking in | [§4 USB recovery](#4-usb-recovery-via-improv_serial) |
| You want to wipe everything stored at runtime and start over | [§5 Factory reset](#5-factory-reset-gesture) |

---

## 1. First-time flash

You'll do this once per device. After this, the next four sections cover
how the device handles network changes without reflashing.

### Prerequisites

- ESP32-S3 AIPI-Lite hardware (Xorigin / XiaoZhi clone)
- USB-C cable (data, not charge-only)
- ESPHome installed: `pipx install esphome` or `uv tool install esphome`
- This repo cloned

### Steps

1. **Copy the secrets template:**

   ```bash
   cp secrets.yaml.example secrets.yaml
   ```

2. **Fill in `secrets.yaml`** with at minimum two networks (home + a
   travel fallback like a phone hotspot) and an AP password ≥ 8 chars:

   ```yaml
   wifi_ssid_home: "YourHomeWiFi"
   wifi_password_home: "..."

   wifi_ssid_phone: "YourPhoneHotspot"
   wifi_password_phone: "..."

   wifi_ap_password: "pick-something-≥8-chars"
   ```

   **Why two networks:** the device tries `home` first, falls through to
   `phone-hotspot` if home isn't reachable. Without a second entry, your
   only fallback is the AP-mode captive portal, which is slower to use.

3. **Plug in via USB and flash:**

   ```bash
   esphome run aipi.yaml --device /dev/ttyACM0
   ```

   On Linux the device usually shows up at `/dev/ttyACM0` (USB
   JTAG/serial). On macOS it's `/dev/cu.usbmodem*`; on Windows, `COMx`.
   First flash takes 30–60 s for compile + upload.

4. **Verify:** the device should join `home` (LCD top label switches off
   `Setup-AP` once associated) and become reachable as `aipi.local`:

   ```bash
   ping aipi.local
   ```

   You're done.

---

## 2. Re-provision via captive portal

Use this when you've moved to a network that isn't in `secrets.yaml` —
coffee shop, work, an AirBnB. The device serves its own AP
(`AiPi-Setup`) and a setup page when none of the known networks are
reachable.

### What you'll see on the device

- LCD top label flips to **`Setup-AP`** when the AP is active.
- LCD reverts to the normal mode label (`Hold-to-talk` / `Always
  listening`) once the device joins a station.

### Steps

1. **Wait for `Setup-AP` to appear** on the LCD (the device will fall
   back to AP mode within ~90 s of failing to join any known network),
   or trigger AP mode immediately by long-pressing the **left button**
   for 3–5 s while the device is running. See [§5
   alternatives](#alternative-trigger-ap-mode-without-rebooting).
2. On your phone or laptop, **join the WiFi network `AiPi-Setup`**
   using the password you set in `wifi_ap_password`.
3. Most modern OSes auto-pop a captive-portal page when joining an AP
   that has no internet. If yours does, the ESPHome captive portal
   appears with a list of nearby networks + a credentials form.
   - **iOS not auto-popping?** Open Safari and visit
     `http://192.168.4.1`. The captive portal will load.
   - **Android nagging about "no internet"?** Tell it to stay
     connected anyway, then open `http://192.168.4.1` in Chrome.
4. Enter the new SSID + password and submit. The device saves the
   credentials to NVS, drops the AP, and reconnects on the new
   network.

### Important caveat

**AP mode does not auto-return to STA mode after a timeout.** Once the
device is in `Setup-AP`, the only ways back to a station network are:

- successful captive-portal submission (which writes new NVS creds and
  reconnects automatically), or
- power-cycling the device (it'll retry the YAML-defined networks +
  any NVS-saved creds from boot).

If you triggered AP mode by long-press and then changed your mind,
power-cycle.

### Alternative: trigger AP mode without rebooting

While the device is running and connected to a station network, hold
the **left button** for 3–5 s. The LCD flips to `Setup-AP`, the device
disconnects from STA, and the AP comes up within ~1 s. Useful when you
want to add a new network without yanking the existing one.

---

## 3. Re-provision via Improv-WiFi (BLE)

Cleaner UX than the captive portal on most phones — no "no internet"
warnings, no manual `192.168.4.1` workaround. Uses the same Improv-WiFi
standard as ESP Web Tools.

### Prerequisites

- A phone with Bluetooth LE (any iPhone since 2014, any modern Android)
- The official **Improv-WiFi** app:
  - **iOS:** [Improv-WiFi on the App Store](https://apps.apple.com/app/improv-wifi/id1639874852)
    *(or search the App Store for "Improv-WiFi")*
  - **Android:** [Improv-WiFi on Play](https://play.google.com/store/apps/details?id=com.improv_wifi)
    *(or search Play for "Improv-WiFi")*

### Steps

1. **Power on the AIPI-Lite.** It advertises over BLE whenever WiFi
   isn't configured, or whenever the `authorizer` permits — and we ship
   `authorizer: none`, so it's always discoverable.
2. **Open the Improv-WiFi app** and tap **Scan**. The device shows up as
   `AiPi`.
3. **Tap the device, enter the new SSID + password,** and tap connect.
   The app pushes the credentials over a BLE GATT characteristic;
   ESPHome saves them to NVS and connects to the new network.
4. The app reports success when the device gets an IP. The device's
   LCD reverts from `Setup-AP` (if it was in AP) back to the normal
   mode label.

### Notes

- BLE coexists with the existing audio pipeline thanks to the ESP32-S3
  WiFi/BT coexistence support and octal PSRAM headroom. Audio
  glitches under heavy concurrent BLE+WiFi load haven't been observed
  in testing.
- `authorizer: none` means anyone in BLE range can pair while the
  device is provisioning. For a personal/single-user device this is
  acceptable; if you ever expose the device in a contested
  environment, switch the authorizer to a button-confirmation mode
  (deferred decision; see `pm/roadmap/aipi-lite/phase-1-provisioning/current-phase-status.md`).

---

## 4. USB recovery via `improv_serial`

The "I'm completely stuck" path. Use this when:

- BLE is unavailable on the host you have at hand,
- the captive portal is unreachable (e.g., the device thinks a network
  is reachable but can't authenticate, so AP fallback never kicks in),
- and you'd rather not reflash from source.

### Steps

1. **Plug the AIPI-Lite into a host via USB.**
2. In a Chromium-based browser (Chrome, Edge), open
   [https://www.improv-wifi.com/](https://www.improv-wifi.com/).
3. Click **Connect** and pick the AIPI-Lite serial port from the
   browser's port-picker (Linux: `/dev/ttyACM0`; Windows: `COMx`;
   macOS: `/dev/cu.usbmodem*`).
4. The site detects that the device is Improv-capable and shows a
   form. Enter SSID + password, submit. The device saves to NVS and
   reconnects.

### Notes

- `improv_serial` shares the USB-Serial/JTAG with normal logging /
  flashing. If you hit a port-busy error, close any `esphome logs` /
  `esphome upload` / serial-monitor sessions first.
- This path doesn't require WiFi access on the host — it's pure
  USB-serial. Useful when you're somewhere with no working WiFi at
  all and can't even spin up an AP-mode handshake.

---

## 5. Factory-reset gesture

Wipes WiFi credentials saved at runtime in NVS (the ones the captive
portal / Improv apps write). YAML-defined networks
(`wifi_ssid_home`, `wifi_ssid_phone`) and the AP password live in the
firmware itself and are **not** affected.

### Steps

1. **Power off** the device (unplug USB).
2. **Hold the left button down.**
3. **Plug USB back in** to power up the device, while keeping the left
   button held.
4. **Keep holding for ≥ 5 s after boot.** The LCD top label flips to
   `Reset` once the gesture is confirmed and the device reboots.
5. Release the button. On the next boot, no NVS creds exist; the
   device tries the YAML-defined `wifi.networks:` first, and if those
   don't connect, falls back to AP mode.

If you release the button before 5 s, the gesture is cancelled (you'll
see a log line on the serial console; LCD doesn't flip).

### What gets wiped

- WiFi credentials saved at runtime by captive portal or Improv-WiFi.
- That's it. The device's identity, the rest of NVS (`api_password`,
  pairing state if any, etc.) is untouched.

### What does NOT get wiped

- YAML-defined network entries (`wifi_ssid_home`, `wifi_ssid_phone`).
- AP-mode password (`wifi_ap_password`).
- Anything in `secrets.yaml` — that's compile-time, not runtime.
- The continuous-mode persistence flag (set by triple-tapping the
  right button); it's a separate `globals:` entry.

If you want to truly nuke everything and start over, just reflash:
`esphome run aipi.yaml --device /dev/ttyACM0`.

---

## Troubleshooting cheatsheet

| Symptom | First thing to check |
|---|---|
| `aipi.local` doesn't resolve after flash | mDNS not available on host; ping the IP from your router's DHCP table |
| Device boots into AP mode every time | NVS creds are stale or YAML networks are unreachable; factory-reset (§5) and reprovision |
| Captive portal page won't load on iOS | Open `http://192.168.4.1` manually in Safari |
| Improv-WiFi app doesn't see the device | Bluetooth permissions on the phone; force-close app and retry |
| `improv_serial` web flasher reports port busy | Close any `esphome logs` or serial monitor sessions and retry |
| Long-press doesn't trigger AP mode | Confirm the *left* button (GPIO1) — the right button (GPIO42) is for voice-typing and the triple-tap mode toggle |

---

## Source canon

- Firmware: [`aipi.yaml`](../aipi.yaml)
- Roadmap: [`pm/roadmap/aipi-lite/`](../pm/roadmap/aipi-lite/)
- Phase 1 (provisioning): [`pm/roadmap/aipi-lite/phase-1-provisioning/`](../pm/roadmap/aipi-lite/phase-1-provisioning/)
