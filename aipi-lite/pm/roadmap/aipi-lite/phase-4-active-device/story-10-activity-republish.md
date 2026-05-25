# AIPI-4-10 — Activity Sticky Re-publish on Device Reconnect

- **Project:** aipi-lite
- **Phase:** 4
- **Status:** done
- **Depends on:** AIPI-4-08 (link republish — same race, same fix pattern)
- **Unblocks:** —
- **Owner:** karol

## Problem

AIPI-4-08 fixed the link-indicator stuck-`[--]` bug: when HoldSpeak handshake wins the race against DeviceLeg's API connection, the initial `update_link` paint silently no-ops because `_update_link_service` isn't cached yet; AIPI-4-08 added a `republish_link_state()` call from DeviceLeg's `_on_connect` to re-fire after the cache lands.

**Same race applies to the activity slot.** At handshake time the bridge calls `_paint_activity("Ready")` to seed the sticky baseline. If the device-leg hasn't cached `_update_screen_service` yet, that paint silently no-ops. AIPI-4-08 dismissed this case ("HoldSpeak's next status frame would overwrite the activity slot, so it self-heals") — but in practice, between sessions and outside of active meetings HoldSpeak doesn't push status frames, and the LCD stays at the firmware boot-default `Ready` (ASCII text from the `aipi.yaml` widget). User-visible: the bottom label never shows the LVGL `Ready  ` glyph until a meeting starts or voice typing fires.

Live-observed 2026-05-10 (right after AIPI-4-09 bridge half landed): LCD showed `HOLD [WIFI-glyph] Ready` — the link indicator updated correctly (AIPI-4-09 + AIPI-4-08 working), but `Ready` was still firmware-text instead of the `Ready  <LV_SYMBOL_OK>` the bridge had tried to paint at handshake.

## Scope

### In

- New `HoldSpeakLeg.republish_sticky_activity()` async method — re-paints `_sticky_activity` (rendered text + symbol) via `on_activity_update`. No-op if no sticky has been set.
- `cli.py:_run` wraps `device.on_device_ready` in a coroutine that calls both `republish_link_state()` and `republish_sticky_activity()` (in that order; link first so the user sees connection state before activity).
- Unit tests in `tests/test_link_retrigger.py` — covers republish-no-sticky, sticky tracked across `_paint_activity` calls, republish re-fires the latest sticky.

### Out

- Re-painting non-sticky (flash) activity. By design a flash is transient — losing one to a race is acceptable.
- Periodic re-sync (e.g., every 30 s republish in case the device LCD got out of sync somehow). One-shot on connect is enough; if the device LCD drifts we'd need a different mechanism (firmware-side state ack, etc.).

## Acceptance Criteria

- [x] `HoldSpeakLeg.republish_sticky_activity()` exists; no-op when `_sticky_activity` is None; calls `on_activity_update(_sticky_activity)` otherwise.
- [x] `cli.py:_run` rewires `device.on_device_ready` to a wrapper coroutine calling both `republish_link_state()` and `republish_sticky_activity()` (link first so connection state is visible before activity).
- [x] Unit tests added: 4 cases in `tests/test_link_retrigger.py` covering no-sticky no-op, re-fire after sticky, latest-sticky-wins on multiple paints, flash-paints-don't-update-sticky.
- [x] Live verification (2026-05-10): bridge restart → `update_screen.ok msg="Ready  "` fired at 23:08:14.974 (LV_SYMBOL_OK codepoint U+F00C). LCD activity slot showed `Ready` + checkmark glyph instead of the firmware-default ASCII `Ready`.

## Test Plan

- **Unit:** mock callbacks, simulate `_paint_activity` then `republish_sticky_activity`, assert call sequence.
- **Live:** bridge restart, observe LCD bottom row.

## Notes

- The sister method's name is `republish_link_state` (not `republish_link`); this method's name is `republish_sticky_activity` (not `republish_activity`) to make the "sticky-only" semantic explicit. Flash paints are deliberately not republished.
- Could have been folded into a renamed `republish_lcd_state()` that does both, but that'd break the existing AIPI-4-08 API. Keeping two separate methods + a wrapper in cli.py is the lower-churn fix.
