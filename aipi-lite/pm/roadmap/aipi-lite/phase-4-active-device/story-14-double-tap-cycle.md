# AIPI-4-14 — Double-tap left-button cycles meeting-stat views

- **Project:** aipi-lite
- **Phase:** 4
- **Status:** done
- **Depends on:** AIPI-4-01 (left-button gesture substrate); HS-14-07
  (event frames); HS-17-08 (per-segment pushback so the cycle has
  Speakers data to show)
- **Owner:** karol

## Problem

Phase 4 wired a single-tap left-button bookmark gesture (AIPI-4-01).
But during a meeting the user often wants a quick read of the current
state without breaking flow — *how long has this been running, who's
talked most, what intel is in?* The user proposed *"double-left-click
— like, couldn't we 'cycle' through different meeting stats while in
meeting mode?"* 2026-05-10.

## Scope

### In

**Firmware (`aipi.yaml`):**
- Lower `left_button` filter debounce from `delayed_on/off: 50 ms` to
  `20 ms` so fast double-taps don't merge.
- Add `on_multi_click` to `left_button` with pattern
  `[ON 0–0.4 s, OFF 0–0.4 s, ON 0–0.4 s]` → pulses a new
  `left_double_tap_event` template binary_sensor for 30 ms.
- New `left_double_tap_event` template binary_sensor (no GPIO; pulsed
  by the on_multi_click action).

**Bridge (`bridge/device.py`):**
- Cache the new entity key in `_cache_button_entities`.
- `_handle_state_change` routes rising edges of `left_double_tap_event`
  into `_handle_left_double_tap_event` which fires
  `EventFrame(name="double_left_click")` upstream and cancels any
  pending single-tap timer / stamps a suppression timestamp so the
  bookmark scheduled by the two underlying release edges gets
  swallowed.
- Keep the bridge-side timing classifier (`LEFT_DOUBLE_TAP_WINDOW_MS
  = 700`) for the simulate-press path, which doesn't route through
  firmware on_multi_click.

**HoldSpeak (`holdspeak/web_runtime.py` + `device_meeting_stats.py`):**
- `_on_device_event` branches on `name == "double_left_click"`:
  resolves active meeting, requires device attached, advances
  per-device cycle index, dispatches the next view.
- New `device_meeting_stats` module with three view formatters
  (Numbers, Speakers, Intel) + `pick_next_view(current_index)`
  helper. Cycle order: Numbers → Speakers → Intel → wrap.
- `device_stats_cycle: dict[str, int]` per-device index cleared
  on meeting stop.

### Out

- Single-tap-outside-meeting on its own — handled by AIPI-4-06.
- A fourth view (Bookmarks list, Action items only, etc.) — three is
  plenty for v1.
- Custom user-defined cycle orderings — over-engineered.

## Acceptance Criteria

- [x] Firmware on_multi_click pulses `left_double_tap_event` on real
  hardware double-taps.
- [x] Bridge subscribes to the new entity, fires
  `EventFrame(name="double_left_click")` on rising edge, suppresses
  the spurious bookmark scheduled by the two underlying release
  edges.
- [x] HoldSpeak's `_on_device_event` advances a per-device cycle
  index and paints the next view to the middle slot (ttl=4000 →
  persists per AIPI-4-11 v2 until next replacement).
- [x] Numbers view: `Recording M:SS / Segments: N / Bookmarks: N`.
- [x] Speakers view: top 3 speakers by segment count.
- [x] Intel view: latest topics + first action item, or `Not yet
  ready` placeholder.
- [x] Per-device cycle index resets on meeting stop.
- [x] Bridge tests: 5 new in `tests/test_bookmark_gesture.py`.
- [x] HoldSpeak tests: 15 new in `tests/unit/test_device_meeting_stats.py`.
- [x] Live-verified end-to-end on `aipi-green.local` in meeting
  `4137086e` 2026-05-10.

## Notes

- **Why firmware on_multi_click, not bridge-side timing?** The bridge
  classifier worked for simulated taps (`simulate_left_press` with
  300 ms gap → clean double-tap detected). But on real hardware the
  firmware's OFF debounce was eating the intermediate release on
  fast taps — bridge saw `press, press, release` (one merged event)
  and classified as single tap. on_multi_click tracks the click
  sequence natively against actual button state, robust against
  debounce-merging.
- **20 ms debounce.** Lowered from 50 ms as a safety belt; even with
  on_multi_click, looser debounce avoids edge cases. Mechanical
  bounce on this button is well under 10 ms in practice.
- **Suppression timestamp.** When firmware fires the double-tap
  event, two underlying release edges have ALSO produced two
  short-press events that get classified bridge-side. Without
  suppression, the second one would schedule a bookmark 700 ms later.
  Stamping `_last_double_tap_event_ms` lets `_delayed_single_tap`
  abort if a double-tap fired in the past second.
- **Cycle-index storage.** A closure-local `dict[str, int]` in
  `web_runtime.py` keyed by device_id. No persistence across server
  restarts; meeting state doesn't survive restarts either, so the
  scope is correct.
