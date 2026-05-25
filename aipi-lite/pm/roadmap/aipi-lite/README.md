# AIPI-Lite — Roadmap

**Last updated:** 2026-05-10 (Phase 2 closed; Phase 3 active; Phase 4 [active device] + Phase 5 [hands-free] opened as parallel scaffolds; AIPI-1 still in-progress pending hardware verification + close-out).
**Current phase:** [phase-3-cross-network-transport](./phase-3-cross-network-transport/current-phase-status.md) — TLS (`wss://`), tunnel/VPN choice (Tailscale recommended), remote-friendly tuning, PSK lifecycle. Pairs with HoldSpeak HS-15.
**Status:** in-progress.

**Phase 1 (provisioning):** implementation-complete on disk
([commit `f7590a2`](#)); hardware verification + close-out commit
owed on the user's schedule. See
[phase-1-provisioning/current-phase-status.md](./phase-1-provisioning/current-phase-status.md).

## Vision

The AIPI-Lite is the physical client for [HoldSpeak](https://github.com/karolswdev/HoldSpeak). The
canonical hardware is the AIPI-Lite ESP32-S3 robot (Xorigin / XiaoZhi); the
firmware lives in `aipi.yaml` (ESPHome), the host-side glue lives in
`bridge.py`. Together they let a person carry a small physical surface that
captures audio (push-to-talk *or* always-listening), reflects state on a
128×128 LCD, and feeds a HoldSpeak instance running locally.

This roadmap covers the **device-side** work — firmware + bridge — that
graduates the AIPI-Lite from a single-purpose Qwen toy (which is what the
upstream repo shipped) into a first-class HoldSpeak satellite.

The early phases here are independent of HoldSpeak's roadmap; later phases
pair 1:1 with HoldSpeak phases (e.g., AIPI-2 ⟷ HS-14, AIPI-3 ⟷ HS-15).

## Source canon

- `aipi.yaml` — ESPHome firmware. Ground truth for hardware wiring + button
  gestures + LCD widgets.
- `bridge/` — Python host-side bridge. Was a self-contained STT + LLM + TTS
  loop pre-AIPI-2; the AIPI-2 rewrite replaced it with a thin HoldSpeak
  protocol translator. AIPI-2-08 split the (then-1500-LOC) `bridge.py` into
  the `bridge/` package; entry point is `python -m bridge`.
- `README.md` — upstream description of the AIPI-Lite robot's audio
  pipeline + hardware workarounds (octal PSRAM, EMI dance, ES8311 mute).
- HoldSpeak roadmap (sibling): `~/dev/HoldSpeak/pm/roadmap/holdspeak/` —
  the host-side counterpart. AIPI-Lite phases that pair with HoldSpeak
  phases reference each other.

## Methodology

This roadmap follows the PMO methodology distributed by
`pmo-roadmap` and used by HoldSpeak — see
`~/dev/HoldSpeak/pm/roadmap/roadmap-builder.md`. The directory contract,
file templates, and lifecycle rules are identical. The PMO commit hook
is **not** installed in this repo (yet); commits are still expected to
honor the spirit of the contract (evidence, master-doc updates, no
bypass) per the project's discipline.

## Phase index

| Phase | Goal (one line) | Status | Folder |
|---|---|---|---|
| 1 | Provisioning: portable WiFi (multi-SSID + captive portal + Improv-WiFi + improv_serial), left-button gestures for AP-mode entry + reset | in-progress | [phase-1-provisioning](./phase-1-provisioning/) |
| 2 | Bridge protocol translator: replace standalone STT/LLM/TTS with a thin HoldSpeak WebSocket forwarder; AIPI-Lite becomes a HoldSpeak satellite end-to-end. Pairs with HoldSpeak HS-14. | done | [phase-2-bridge-protocol-translator](./phase-2-bridge-protocol-translator/) |
| 3 | Cross-network transport: TLS (`wss://`), tunnel/VPN choice (Tailscale recommended), remote-friendly tuning, PSK lifecycle. Pairs with HoldSpeak HS-15. | in-progress | [phase-3-cross-network-transport](./phase-3-cross-network-transport/) |
| 4 | Active device: bookmark gesture, mic-level meter, multi-device meetings, LVGL symbols, battery/RSSI pushback (HS-blocked), last-transcript gesture (HS-blocked). Parallel to phase 3. | not-started | [phase-4-active-device](./phase-4-active-device/) |
| 5 | Hands-free: ESPHome `micro_wake_word` integration, VAD-driven session end, HOLD/WAKE/BOTH mode coexistence. | not-started | [phase-5-hands-free](./phase-5-hands-free/) |

(Status values: `planning`, `in-progress`, `done`, `paused`, `cancelled`.)

## Operating cadence

Every shipping commit updates, in the same commit:

1. The story file header (status flip).
2. The phase's `current-phase-status.md` story-status row + "Where we are".
3. This README's "Last updated" line.
4. Any project-canon doc touched by the story (e.g. `aipi.yaml`, `README.md`).

For now, no pre-commit hook enforces this; honor it by hand.

## Project metadata

- **Slug:** `aipi-lite`
- **Story ID prefix:** `AIPI` (e.g. `AIPI-1-01`)
- **Greenfield?:** yes — no users, no released versions, schema and APIs change freely.

## Glossary

- **AIPI-Lite** — the ESP32-S3 robot hardware (also known as Xorigin / XiaoZhi).
- **Improv-WiFi** — open standard for provisioning ESP32 WiFi via BLE or
  serial. ESPHome ships `esp32_improv` (BLE) and `improv_serial`.
- **AP-mode fallback** — when no known network connects, the device boots
  its own access point (`AiPi-Setup`) and serves a captive portal for new
  network configuration.
- **Bridge** — the `bridge/` package (run via `python -m bridge`). The
  host-side Python process that talks to the device's ESPHome API and
  forwards audio + control to HoldSpeak.
