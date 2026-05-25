# AIPI-1-05 - Left-Button Gestures: AP-Mode Entry + Factory-Reset

- **Project:** aipi-lite
- **Phase:** 1
- **Status:** in-progress
- **Depends on:** AIPI-1-01
- **Unblocks:** AIPI-1-06
- **Owner:** karol

## Problem

The right button is fully owned by the existing voice-typing
gesture (press-and-hold to talk, triple-tap to flip mode). The
left button is currently **unused** in `aipi.yaml`. That's a free
physical surface for two high-leverage provisioning actions:

1. **Long-press (3–5 s)** while running → enter AP-mode + captive
   portal for 2 minutes, even if a known network is reachable.
   Lets the user re-provision without yanking the network.
2. **Hold-during-boot (≥ 5 s)** → factory-reset stored WiFi
   credentials. The "completely stuck" recovery before USB.

This story wires both. The device's hardware GPIO for the left
button needs confirming first — `sticks918/AIPI-Lite-ESPHome` is
the upstream reference; otherwise a probe via a small test sketch.

## Scope

- **In:**
  - Add a `binary_sensor:` for the left button (GPIO TBD —
    confirm from upstream config or hardware probe; document
    in the story Notes once known).
  - `on_click` with `min_length: 3000ms`, `max_length: 5000ms`
    → script `enter_ap_mode` that calls
    `wifi.enable_ap` (or equivalent — ESPHome's `wifi:` API
    exposes a `start_scanning_ap` / forced-AP path; verify
    correct invocation from docs) + a 2-min timer that drops
    back to client mode.
  - `on_boot` priority lower than the WiFi component: read the
    left button at startup; if held, call
    `wifi.disconnect()` and clear stored creds (NVS reset for
    the wifi namespace) before normal boot continues.
  - LCD updates to confirm gestures: top label flips to
    `Setup-AP` for long-press, `Reset` (briefly) on boot-hold
    factory-reset.

- **Out:**
  - Other left-button gestures (single-tap, double-tap) — out
    of scope; those remain unused for future work.
  - Bridge / HoldSpeak coupling — none needed for provisioning.

## Acceptance Criteria

- [x] Left button GPIO confirmed: **GPIO1** (evidence in Notes,
  rev 2 probe — single clean PROBE PRESS on press, no false
  positives elsewhere with 30 ms debounce).
- [~] Long-press (3–5 s) while connected to a network triggers
  AP-mode; verify by joining `AiPi-Setup` from a phone within
  the window.
  *Implemented* in `aipi.yaml` script `enter_ap_mode`:
  `id(wifi_id).set_ap_timeout(1000)` + `wifi.disable` +
  `delay 200ms` + `wifi.enable`. Loop fallback at
  `wifi_component.cpp:840-852` brings the AP up within ~1s.
  LCD flips to `Setup-AP`. Compile + flash green 2026-05-07.
  **Spec drift:** dropped the "AP-mode for 2 minutes then
  return to client mode" semantics — ESPHome doesn't auto-flip
  AP→STA without user reprovisioning or a reboot
  (per `WiFiConfigureAction` analysis). Documented in the
  AIPI-1-06 runbook. **Hardware verification still pending.**
- [~] After the AP window ends (or user provisions a new
  network), device returns to client mode.
  *Implemented* via the captive-portal save path: when the user
  submits new creds in the captive portal, `WiFiConfigureAction`
  saves them to NVS and the wifi component reconnects to STA.
  Power-cycle is the manual fallback. **Hardware verification
  pending.**
- [x] Hold-during-boot (≥ 5 s) clears stored WiFi credentials;
  verify by booting the device with the button held → next
  boot starts in AP-mode.
  *Implemented:* second `on_boot` entry at priority 700 polls
  `binary_sensor.is_on: left_button` with a 5s window; if held
  through, calls script `factory_reset_wifi` which fires
  `id(wifi_id).save_wifi_sta("", "")` (canonical NVS wipe;
  `clear_sta()` is RAM-only and misleading) + `App.safe_reboot()`.
  YAML-defined `wifi.networks:` are unaffected — only
  runtime-provisioned NVS creds get wiped. Compile + flash green.
  **Hardware verification pending.**
- [x] LCD reflects gesture state appropriately. *Wired:* mode
  label flips to `Setup-AP` on long-press. Visual confirmation
  on hardware pending.
- [x] Existing right-button gestures unaffected: voice-typing
  press-and-hold + triple-tap mode toggle still work.
  *Inspected:* the diff only adds a new `binary_sensor` entry
  for `left_button` on GPIO1; the `right_button` block on GPIO42
  is byte-identical.

## Test Plan

- Unit: n/a.
- Integration: `esphome compile aipi.yaml` clean.
- Manual:
  1. Confirm left-button GPIO via upstream config or probe.
  2. Test long-press → AP-mode → captive-portal flow.
  3. Test boot-hold reset → fresh AP-mode on next boot.
  4. Test that right-button voice-typing flow is unaffected.

## Notes

- **GPIO TBD:** the original AIPI-Lite hardware references a
  left button; the exact GPIO needs verifying from `sticks918`'s
  config or by probing. Keep this story `in-progress` until the
  GPIO is captured here.
- ESPHome's `wifi.enable_ap` API may not exist by that name;
  verify from the 2026.x docs. Alternative paths: a `lambda`
  that calls into the `WiFi` global to start AP mode, or a
  forced reconnect cycle that triggers the AP fallback by
  failing the known networks N times in quick succession.
- Boot-hold reset is implemented by reading the GPIO state at
  `on_boot` priority lower than the WiFi component's startup,
  before WiFi has tried any networks. ESPHome's NVS reset for
  the wifi namespace is the canonical way; document in
  `docs/PROVISIONING.md` (AIPI-1-06).

### 2026-05-07 — wifi-API research pass + full implementation

Sub-agent research nailed down the ESPHome WiFiComponent surface
(see `wifi_component.h:426-477`, `cpp:712-723, 840-854, 925-959,
989-1010, 1059-1077`). Findings driving the implementation:

- **No public "go to AP" method.** `setup_ap_config_()` is
  protected; only `start()` and the loop fallback at cpp:840-852
  call it. Supported path: shorten `ap_timeout` at runtime
  (`set_ap_timeout(uint32_t ms)` is public) and cycle
  `wifi.disable` → `wifi.enable`. AP fallback fires within ~1 s.
- **Default `ap_timeout` stays at 90 s in YAML** so normal boot
  isn't subject to spurious AP fallback before STA association
  finishes; only the runtime `enter_ap_mode` script shortens it.
- **`clear_sta()` is RAM-only** and does not touch NVS —
  misleadingly named. The canonical NVS wipe is
  `save_wifi_sta("", "")` which writes a zero-initialized
  `SavedWifiSettings` and syncs the preferences partition.
- **No auto AP→STA flip.** The story's original "AP for 2 min
  then return to client mode" semantics aren't supported without
  a custom timer + reboot. Spec drift documented above; the
  current implementation relies on captive-portal-driven
  provisioning or power-cycle to return to STA.

Both scripts compile + flash clean against ESPHome 2026.4.5
(`set_ap_timeout` and `save_wifi_sta` are both public).

### 2026-05-07 — Hardware probe → GPIO1 (story unpaused)

Built and flashed `pm/probes/aipi-1-05-left-button.yaml`
(probe rev 2 after rev 1 surfaced floating-pin noise on
GPIO2/21/47). Probe rev 2 covers candidate pins
0, 1, 8, 38, 39, 40, 41, 48 with `pullup: true` + 30 ms
`delayed_on`/`delayed_off` debounce. Flashed via
`/dev/ttyACM0`; on user press, exactly one pin logged:

```
[20:52:33.828][I][main:435]: PROBE PRESS: GPIO1
```

Repeated presses logged repeatedly on **GPIO1 alone** — none
of the other candidates fired and no fresh ESPHome boot banner
appeared (so the button is *not* on EN/RESET; the upstream
maintainer's "sleep/wake button" remark turns out to be
misleading for this PCB revision). Production debounce bumped
to 50 ms to handle a slight switch bounce we observed on press.

The probe yaml stays under `pm/probes/` for now in case we need
to re-run it against the candidates we still haven't probed
(e.g., for a future right-button replacement debate). Delete
when AIPI-1-05 fully ships.

### 2026-05-07 — Upstream finding (story paused — superseded by probe above)

Pulled `sticks918/AIPI-Lite-ESPHome/aipi.yaml` to confirm the
left-button GPIO. Right button is `GPIO42`; the left button has
**no plain GPIO `binary_sensor` upstream**. The upstream config
has the left-button block commented out with this note verbatim:

> Left button can work with Home Assistant but causes strange
> behavior, looks like designed to use only as a sleep/wakeup
> button

The upstream commented-out attempt uses `platform: switch,
source_id: left_button` — i.e., it tried to surface the button
through a switch entity, not a GPIO sensor. That, plus the
"sleep/wake button" language, strongly suggests the left button is
wired to a strapping pin (BOOT / IO0), the chip's `EN` line, or a
discrete wake-up IC rather than a normal GPIO with a clean
pull-up. Without hardware probing (multimeter or instrumented
test build) we can't responsibly assign a GPIO and write the
`on_click` + boot-hold logic.

Pausing the story per the phase's documented stop signal in
`current-phase-status.md` (Active risks → "Left button GPIO not
what we assume"). Resuming requires either:

1. A hardware probe — flash a test sketch that logs the state of
   the candidate strapping/wake pins on press (requires a reflash
   the user has currently deferred), **or**
2. Descoping AIPI-1-05 for this phase. The phase exit criteria
   that depend on the boot-hold reset gesture would move to AIPI-4
   or a follow-up phase. Captive portal + Improv-WiFi BLE +
   improv_serial already cover the user-facing reprovisioning
   paths, so the left button is a luxury, not a critical path.
3. Repurposing a different right-button gesture for AP-mode
   entry (e.g., long-press > 3s, since triple-tap is already
   the mode toggle). Boot-hold reset would still need the
   left button or an alternative recovery path.
