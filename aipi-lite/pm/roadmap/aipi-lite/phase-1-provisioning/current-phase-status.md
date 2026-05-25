# Phase 1 - Provisioning: Portable WiFi + Left-Button Gestures

**Last updated:** 2026-05-07 (AIPI-1-06 partial close — `docs/PROVISIONING.md` shipped; per-story evidence files, `final-summary.md`, and README phase-flip pending hardware verification of AIPI-1-01..05).

## Goal

Today the AIPI-Lite firmware bakes a single SSID + password into the
build (`secrets.yaml`) at compile time. To change networks you reflash
over USB. That's a non-starter the moment the device leaves the user's
home WiFi — coffee shop, work, AirBnB, conference, friend's house —
and the user only has two physical buttons (right + left) to interact
with the device.

This phase makes the AIPI-Lite **portable**:

- Pre-configure multiple known networks (home, phone hotspot) so the
  device just works in expected places.
- Auto-fall back to AP-mode + captive portal when none of the known
  networks are reachable, so the user can configure a new network
  from a phone in under a minute.
- Add Improv-WiFi over BLE so a phone app can pair and push credentials
  without typing on a 128×128 captive portal.
- Add improv_serial as a USB-tethered recovery path when the device
  is bricked off the network entirely.
- Wire the **left button** (currently unused in `aipi.yaml`) to:
  - Long-press (≥ 3 s) → enter AP-mode + captive portal for 2 min,
    even if a known network is reachable. Lets the user re-provision
    without yanking the network.
  - Hold-during-boot (≥ 5 s) → factory-reset stored WiFi credentials.
    The "I'm completely stuck" recovery.

Phase scope is **device + bridge only**. No HoldSpeak coupling. The
device works against any LAN ESPHome API consumer (the existing
bridge.py, an esphome CLI, or eventually HoldSpeak via AIPI-2).

## Scope

- **In:**
  - `aipi.yaml` `wifi:` block grows a `networks:` list (home + phone
    hotspot at minimum) + an `ap:` AP-mode fallback config.
  - `secrets.yaml` template grows the new fields (`wifi_ssid_home`,
    `wifi_password_home`, `wifi_ssid_phone`,
    `wifi_password_phone`, `wifi_ap_password`).
  - `captive_portal:` component added.
  - `esp32_improv:` component added with `authorizer: none` (single-
    user product; no in-app authorizer step needed).
  - `improv_serial:` component added.
  - `binary_sensor` for the left button (GPIO TBD — confirm from the
    hardware schematic; `sticks918/AIPI-Lite-ESPHome` references both
    buttons).
  - Left-button bindings:
    - `on_click` with `min_length: 3000ms`, `max_length: 5000ms` →
      script that forces AP-mode for 2 minutes.
    - Boot-time check: if button is held during `on_boot`, clear
      stored WiFi credentials.
  - Mode-label LCD updates so the user can tell the device is in
    AP-mode vs client-mode (top label says e.g. `Setup-AP — AiPi-Setup`
    when in AP, vs the existing mode label).
  - Compile + flash instructions in a runbook
    (`docs/PROVISIONING.md`) covering: first-time setup, reprovisioning
    via captive portal, BLE pairing via Improv-WiFi app, USB recovery
    via improv_serial, factory-reset gesture.

- **Out:**
  - Cross-network "calling home" (Tailscale / Cloudflare Tunnel /
    public exposure of HoldSpeak). AIPI-3.
  - Bridge protocol changes (still talks to the local bridge.py).
    AIPI-2.
  - Wake-word / on-device VAD enhancements. AIPI-4+.
  - Web UI for provisioning beyond what `captive_portal:` already
    provides out of the box.

## Exit criteria (evidence required)

- [ ] `aipi.yaml` ships `wifi.networks:` (≥ 2), `wifi.ap:`,
  `captive_portal:`, `esp32_improv:`, `improv_serial:` components,
  and compiles cleanly under ESPHome 2026.x.
- [ ] Left-button `on_click` long-press handler fires AP-mode (verified
  by serial log line + LCD label change).
- [ ] Hold-during-boot reset clears stored WiFi (verified by booting
  with held button → device comes up in AP-mode at next boot).
- [ ] Re-provisioning via captive portal: device on unknown network →
  AP-mode → phone joins `AiPi-Setup` → captive portal page accepts a
  new SSID/password → device joins the new network on its own.
- [ ] Re-provisioning via Improv-WiFi: pair from the iOS or Android
  Improv-WiFi app → push creds → device joins the new network.
- [ ] USB recovery: `improv_serial` accepts creds via the ESPHome
  flasher tool when the device is wedged.
- [ ] `docs/PROVISIONING.md` covers all four paths with screenshots
  or terminal output.

## Story Status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| AIPI-1-01 | Multi-SSID + AP-mode fallback config | in-progress | [story-01-multi-ssid-ap-fallback.md](./story-01-multi-ssid-ap-fallback.md) | Build green 2026-05-07 (`esphome compile` → SUCCESS, 36.59s). Scenario 1 green: device flashed via `/dev/ttyACM0`, joined home WiFi, `aipi.local` → 192.168.1.44 (ping 0% loss). Scenarios 2 & 3 pending real phone-hotspot creds + AP password. |
| AIPI-1-02 | Captive portal for new-network setup | in-progress | [story-02-captive-portal.md](./story-02-captive-portal.md) | `captive_portal:` added; `refresh_mode_label` now flips to `Setup-AP` while disconnected. Build green 2026-05-07. Captive-portal flow + label flip pending hardware test (gated on entering AP mode). |
| AIPI-1-03 | Improv-WiFi BLE provisioning | in-progress | [story-03-improv-wifi-ble.md](./story-03-improv-wifi-ble.md) | `esp32_improv:` added with `authorizer: none`. Build green 2026-05-07; BLE stack lifts RAM 13.5%→17.6%, Flash 15.0%→20.1% (within budget). App discovery + audio-coexistence tests pending. |
| AIPI-1-04 | improv_serial USB recovery | in-progress | [story-04-improv-serial.md](./story-04-improv-serial.md) | `improv_serial:` added. Build green 2026-05-07. Web-flasher recovery test pending. |
| AIPI-1-05 | Left-button gestures: AP-mode entry + factory-reset | in-progress | [story-05-left-button-gestures.md](./story-05-left-button-gestures.md) | Probe shipped 2026-05-07: left button = **GPIO1**. Full implementation landed same day: `enter_ap_mode` (set_ap_timeout(1000) + wifi.disable/enable cycle → loop fallback → AP up in ~1s) + `factory_reset_wifi` (save_wifi_sta("","") + safe_reboot) + on_boot priority-700 hold-detect window (5 s). Compile + flash green via `/dev/ttyACM0`. Spec drift: AP doesn't auto-return to STA; documented in the AIPI-1-06 runbook. Hardware verification pending. |
| AIPI-1-06 | Phase exit + DoD + provisioning runbook | in-progress | [story-06-dod.md](./story-06-dod.md) | `docs/PROVISIONING.md` shipped 2026-05-07: 5 sections + TL;DR + troubleshooting cheatsheet, covers all four provisioning paths + factory-reset gesture. Per-story evidence files, `final-summary.md`, and README phase-flip all sequenced behind the hardware verification the user has deferred. |

## Where we are

AIPI-1-01..05 are all implementation-complete as of 2026-05-07.
The `wifi:` block carries a `networks:` list, `ap:` fallback
(`AiPi-Setup`), `id: wifi_id` for lambda access, and
`on_connect`/`on_disconnect` hooks that refresh the LCD.
`captive_portal:`, `esp32_improv:` (authorizer none), and
`improv_serial:` are wired. The left button is on **GPIO1**
(probed) with 50 ms debounce + on_click 3–5 s firing
`script.enter_ap_mode` (`set_ap_timeout(1000)` + wifi
disable/enable cycle → loop fallback brings AP up in ~1 s).
A second on_boot entry at priority 700 polls the left button
for a 5 s hold and fires `script.factory_reset_wifi`
(`save_wifi_sta("", "")` + `App.safe_reboot()`) on confirm.
Production firmware was reflashed after the AIPI-1-05 follow-up
landed, so the full phase-1 surface is live on the device.

Spec drift recorded in story-05: AP-mode doesn't auto-return to
STA after a timer — return is via captive-portal save (which
writes new NVS creds) or power-cycle. This becomes runbook
material in AIPI-1-06.

Verification still owed (all hardware):
- AIPI-1-01 scenarios 2 & 3 — deferred by user; needs real
  phone-hotspot creds + AP password in `secrets.yaml`.
- AIPI-1-02 captive portal page + LCD `Setup-AP` flip on real
  AP-mode entry.
- AIPI-1-03 Improv-WiFi mobile-app discovery + audio
  coexistence.
- AIPI-1-04 web-flasher recovery flow.
- AIPI-1-05 long-press → AP-mode + boot-hold → factory reset
  (both behavioural; LCD flips visible too).

AIPI-1-06 opened and partially closed 2026-05-07.
`docs/PROVISIONING.md` shipped: TL;DR table, five numbered
sections (first-time flash, captive portal, Improv-WiFi BLE,
improv_serial USB, factory-reset gesture), plus a
troubleshooting cheatsheet. The AP→STA "no auto-return" caveat
from AIPI-1-05 is folded into §2.

Pickup: nothing more to do until hardware verification.
When the user is ready to flash + run the scenarios:

1. AIPI-1-01 scenarios 2 & 3 (real hotspot creds + AP password)
2. AIPI-1-02 captive portal flow
3. AIPI-1-03 Improv-WiFi BLE pairing + audio coexistence
4. AIPI-1-04 improv-wifi.com web-flasher recovery
5. AIPI-1-05 left-button long-press → AP and boot-hold → reset

A single sitting with the device + a phone + a laptop can clear
all of those. After that, the AIPI-1-06 close-out commit
authors `evidence-story-01..05.md` (re-formatting the inline
evidence already in the story files), flips 01..06 to `done`,
authors `final-summary.md`, freezes `current-phase-status.md`,
and bumps the project README to point at phase 2.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Left button GPIO not what we assume — original AIPI-Lite robot may wire it differently than the right (GPIO42) | medium | Confirm from `sticks918/AIPI-Lite-ESPHome` upstream config + a multimeter / test build that logs the GPIO state on press. Story AIPI-1-05 owns the verification. | If the left button is on a strapping pin or doesn't have a clean pull-up, switch to using triple-tap of the right button as the AP-mode trigger and skip left-button work for this phase. |
| Improv-WiFi BLE conflicts with the existing audio pipeline (memory, BLE coexistence with WiFi on ESP32-S3) | low | ESP32-S3 supports BT LE 5 + WiFi coexistence by spec. Octal PSRAM gives memory headroom. Test on the actual hardware before declaring AIPI-1-03 done. | If enabling BLE causes audio glitches > minor, gate it behind an opt-in compile flag and document the trade-off. |
| Captive portal page UX is too rough for mobile use | low | ESPHome's built-in captive portal is plain but functional. Acceptable for v1. | If the captive portal genuinely blocks new-network setup in field testing, time-box a custom HTML override before falling back to "BLE provisioning is the only path." |
| Stored WiFi credentials persist through firmware updates in a way that surprises the user | low | ESPHome stores credentials in NVS; reflashing the same `aipi.yaml` preserves them by default. Add the boot-hold reset gesture (AIPI-1-05) so the user has an explicit knob. | If users report ghost credentials after re-flashes, document the NVS reset procedure in `docs/PROVISIONING.md` recovery section. |

## Decisions made (this phase)

- 2026-05-07 — **Use ESPHome's built-in `captive_portal:` rather than a custom HTTP page** — battle-tested, zero extra code, sufficient for v1.
- 2026-05-07 — **Improv-WiFi BLE alongside captive portal, not instead** — gives users two paths; one will be more reliable on a given platform than the other.
- 2026-05-07 — **Left-button bindings: `on_click` (3–5s) for AP-mode, boot-hold for factory-reset** — discoverable via `docs/PROVISIONING.md`; no risk of accidental trigger during normal use (the button does nothing else in this phase).
- 2026-05-07 — **Multi-SSID `networks:` list ships with `home` + `phone-hotspot` placeholders, not just `home`** — encourages users to configure their phone hotspot up front so they're never stranded.

## Decisions deferred

- **Whether to ship a default Improv-WiFi authorizer (e.g., physical button confirmation) instead of `none`** — defer until we hit a use case where the BLE channel is exposed to people who shouldn't be pairing. Default: `authorizer: none` for single-user use.
- **Web UI for ongoing network management (forget network, switch network without AP-mode)** — defer until users actually want it. Captive portal handles the "stuck" case; that's enough for now.
- **Multi-language captive portal** — defer indefinitely. English-only for v1.
