# AIPI-4-08 — Link State Re-trigger on Device Reconnect

- **Project:** aipi-lite
- **Phase:** 4
- **Status:** done
- **Depends on:** AIPI-2-07 (LCD pushback substrate)
- **Unblocks:** —
- **Owner:** karol

## Problem

When the bridge starts and HoldSpeakLeg's WS handshake to localhost wins the race against DeviceLeg's mDNS-resolved API connection (which is typical — localhost is faster than mDNS), the bridge's link-state paint `update_link("[OK]")` silently no-ops because `DeviceLeg._update_link_service` isn't cached yet. The bridge then has no mechanism to re-paint when DeviceLeg eventually connects, so the link indicator gets stuck at the firmware's boot-default `[--]` forever even though both legs are actually online.

**Live-observed 2026-05-10:** device showed `[--]` permanently throughout an entire working session. Bookmarks, audio, transcripts all flowed correctly — but the link indicator never updated. User had to infer connectedness from behavior, not LCD. UX-confusing — looks broken.

## Scope

### In

- New async method `HoldSpeakLeg.republish_link_state()` that re-emits the current link state via `on_link_update`. Idempotent. Safe to call before any session has started (no-op).
- New optional callback `on_device_ready` on `DeviceLeg.__init__`; called from `_on_connect` after `_cache_lcd_services` + `_cache_button_entities` both complete.
- `bridge/cli.py:_run` wires `device.on_device_ready = holdspeak.republish_link_state` post-construction, same late-bound pattern as `is_in_meeting` / `paint_bookmark_flash`.
- Unit test: simulate DeviceLeg connecting after HoldSpeakLeg handshake; assert `update_link` called with current link state.

### Out

- Re-painting activity (bottom label) on reconnect. HoldSpeak's next status frame will overwrite the activity slot, so it self-heals. Only the link indicator has this stale-paint problem (it's bridge-owned, not HoldSpeak-pushed).
- Restructuring the leg startup order to avoid the race. Race-tolerant > order-dependent.

## Acceptance Criteria

- [x] `HoldSpeakLeg.republish_link_state()` exists; calls `on_link_update(current_state)` if a state has been set; no-op otherwise.
- [x] `DeviceLeg.__init__` accepts `on_device_ready: Callable[[], Awaitable[None]] | None = None`.
- [x] `DeviceLeg._on_connect` calls `on_device_ready()` after `_cache_lcd_services` + `_cache_button_entities` + `subscribe_states` complete.
- [x] `cli.py:_run` wires `device.on_device_ready = holdspeak.republish_link_state` post-construction.
- [x] Unit tests: 10 cases in `tests/test_link_retrigger.py` covering republish-no-state, state-tracking, handler-unset, handler-errors, re-fire, latest-state-wins, callback-fires-after-cache, None-safe, error-swallowing, and an end-to-end race recovery scenario.
- [x] Live verification (2026-05-10): bridge restarted with device powered off, HoldSpeak handshook at 22:25:00 (race won — `update_screen.skip` confirms the cache-miss path), then user powered the device on. At 22:26:20.536 device connected; at 22:26:20.680 `update_link.ok state="[OK]"` fired — the republish landed exactly as designed. LCD reflected `[OK]`. Bonus: voice typing followed at 22:26:39 ("Find out if everything's alright!") and 22:26:58 ("I want to talk to this device.") — both transcribed correctly, confirming no regression to the audio path.

## Test Plan

- **Unit:** mock `on_link_update` + `on_device_ready`; simulate handshake-then-device-connect ordering; assert update_link gets called twice (once during handshake's silent no-op, once on republish).
- **Live:** kill + restart bridge; observe LCD link indicator transitions.

## Notes

- Republish is one-shot on connect (not on every state change). If a future reconnect cycle re-creates the race, the republish fires again from the next `_on_connect`.
- This bug existed since AIPI-2-07 (the link indicator was introduced there) but only became visible once the device + bridge restart cadence increased during hardware testing.
