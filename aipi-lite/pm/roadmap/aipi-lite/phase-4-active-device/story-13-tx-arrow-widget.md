# AIPI-4-13 — TX-arrow widget (top-right) for voice-typing state

- **Project:** aipi-lite
- **Phase:** 4
- **Status:** done
- **Depends on:** AIPI-2-07 (LCD substrate); HS-14-07 (status push)
- **Owner:** karol

## Problem

Pre-AIPI-4-13, holding the device's right button (voice-typing trigger)
overwrote the bottom LCD slot's persistent text:

- Firmware `on_press` → `ai_response_label = "Listening..."`
- HoldSpeak `_on_device_voice_start` also pushed `Listening...`
  (ttl=0) to the bottom widget
- On release: `Thinking...` replaced it
- After transcribe: snippet flashed for 4 s and the bottom widget
  reverted to the sticky meeting state

Result: every right-button press clobbered `Recording M:SS` mid-meeting
for several seconds. The user's instinct on 2026-05-10 was correct —
*"when we tx with the right button, why must we actually update the
lower LVGL? Why not the upper, next to the WiFi symbol, as like…
arrow up?"*

## Scope

### In

- New `tx_label` LVGL label widget at TOP_RIGHT, immediately left of
  `link_label`. Single-glyph wide (16 px), montserrat_10 (default), no
  text by default.
- Firmware `right_button.on_press` (out-of-continuous-mode branch)
  paints `LV_SYMBOL_UP` (``) to `tx_label`; `on_release` clears
  it. The voice-assistant start/stop calls are unchanged.
- Narrow `link_label` width from 60 → 16 so the two top-right glyphs
  sit side-by-side without overlap.
- HoldSpeak side: drop `device_status.send(..., "Listening...")` from
  `_on_device_voice_start` and `device_status.send(..., "Thinking...")`
  from `_on_device_voice_stop`. The transcript snippet still fires
  (now with `ttl_ms=4000` → middle slot via AIPI-4-11's routing).

### Out

- CONT-mode bidirectional arrows (`↑↓`). Scaffolded in the story
  narrative; not implemented because CONT mode itself is retired per
  phase-2 decisions.
- Right-button hold visual on the bottom slot ever. The activity slot
  is owned by HoldSpeak's persistent meeting state from this point on.

## Acceptance Criteria

- [x] `tx_label` widget defined in `aipi.yaml`, painted on/off by the
  right-button on_press/on_release.
- [x] `link_label` width = 16 (was 60).
- [x] HoldSpeak's `web_runtime.py` no longer pushes `Listening...` /
  `Thinking...` to attached devices.
- [x] OTA-flashed to `aipi-green.local`.
- [x] Live verification: hold right button → arrow appears top-right
  next to WiFi; release → arrow disappears; bottom widget keeps
  showing `Ready ✓` / `Recording M:SS` throughout.

## Notes

- **LV_SYMBOL_UP** = ``. Available in montserrat_10 (which
  bundles a small Font Awesome subset). No need to load a custom font.
- **CONT-mode placeholder.** The same widget can paint `↑↓` (two
  glyphs in one label) if CONT mode is ever revived. No additional
  widget needed.
- **Why firmware-side, not bridge-side?** Right-button hold/release
  is local hardware state; bridge round-trips would add latency for
  no benefit. The bottom-slot clobber removal IS bridge-side because
  HoldSpeak is the one pushing the offending text.
- **Live-tuning artifact.** This story closed the immediate symptom
  the user flagged. The pattern (firmware owns transport-state glyphs;
  bridge owns content payloads) is the right general design.
