# Evidence — AIPI-4-14 — Double-tap left-button cycles meeting stats

- **Shipped:** 2026-05-10
- **Commits:** `4b9f18e` (firmware + bridge) + `0c0e7cf` (HoldSpeak cycle handler)
- **Owner:** karol

## Files touched

### Firmware (`aipi.yaml`)

- `left_button` filter: `delayed_on/off: 50ms` → `20ms` so fast
  double-taps don't merge.
- `left_button.on_multi_click` added with pattern
  `[ON 0–0.4s, OFF 0–0.4s, ON 0–0.4s]` → publishes
  `left_double_tap_event = ON` for 30 ms then back to OFF.
- New `left_double_tap_event` template `binary_sensor` (no GPIO).

### Bridge

- `bridge/device.py`:
  - New constant `LEFT_DOUBLE_TAP_WINDOW_MS = 700`.
  - New instance state `_left_double_tap_event_key`,
    `_last_double_tap_event_ms`,
    `_left_button_last_short_release_ms`,
    `_left_button_pending_single_tap`.
  - `_cache_button_entities` resolves the new entity key.
  - `_handle_state_change` routes rising edges of the new entity into
    `_handle_left_double_tap_event` which cancels the pending single-
    tap timer + spawns `_fire_double_tap_event` (emits
    `EventFrame(name="double_left_click")`).
  - `_delayed_single_tap` checks `_last_double_tap_event_ms` and
    suppresses the bookmark if the firmware-side double-tap fired in
    the past second.
- `tests/test_bookmark_gesture.py`: 5 new bridge tests covering the
  classifier (the bridge-side fallback path; firmware on_multi_click
  doesn't run in unit tests).

### HoldSpeak

- `holdspeak/device_meeting_stats.py` (NEW): formatters
  `format_numbers_view` / `format_speakers_view` / `format_intel_view`
  + `pick_next_view(current_index)` + `CYCLE_ORDER` constant.
- `holdspeak/web_runtime.py`:
  - `device_stats_cycle: dict[str, int]` closure-local per-device
    cycle index.
  - `_on_device_event` branches on `name == "double_left_click"` →
    resolves active meeting, requires device attached, advances
    index, sends formatted payload (`ttl_ms=4000` → middle slot).
  - `_stop_active_meeting` calls `device_stats_cycle.clear()`.
- `tests/unit/test_device_meeting_stats.py` (NEW): 15 tests covering
  all three formatters + cycle advance + view dispatch + edge cases.

## Verification

```
$ .venv/bin/python -m pytest -q   # bridge side
150 passed in 4.15s

$ cd /home/karol/dev/HoldSpeak && .venv/bin/python -m pytest tests/unit/test_device_meeting_stats.py -q
15 passed in 0.04s
```

### Live verification — 2026-05-10

OTA-flashed `aipi-green.local` with new firmware. Started meeting
`4137086e` with `aipi-1` attached. User double-tapped repeatedly:

Bridge log (`/tmp/bridge-live.log`):

```
left_double_tap_event.received
event.double_left_click.emitted
control.sent {"type":"event","name":"double_left_click", ...}
```

Repeat × N — each one cycled the LCD's middle slot through:
- View 0: Numbers (`Recording 00:00 / Segments / Bookmarks`)
- View 1: Speakers (`- Karol: 0` or top-3 once segments existed)
- View 2: Intel (`Not yet ready` — llama-cpp unavailable in this env)
- → wraps to View 0

User confirmation: *"spoke and did a bunch of things — yes, the
double clicks actually did work"*.

### Iteration notes (live debugging on 2026-05-10)

- Initial bridge-side classifier with 400 ms window: failed live
  because firmware OFF debounce ate intermediate releases. Bumped
  window to 700 ms — still failed.
- Diagnosis via the bridge's `left_button.edge` diag log (now
  removed): the merge pattern was `press, press, release` (two ON
  edges, single OFF) — clear evidence the firmware was emitting one
  combined event.
- Decided to move detection firmware-side via `on_multi_click`. After
  OTA flash, double-tap worked reliably; user confirmed live.

## Acceptance criteria — re-checked

All 9 brackets `[x]` — see [`story-14-double-tap-cycle.md`](./story-14-double-tap-cycle.md).

## Deviations from plan

- **Detection moved from bridge-side timing to firmware-side
  on_multi_click** mid-implementation (after the live bridge-side
  classifier failed). Bridge-side timing kept as a fallback for the
  simulate-press path that doesn't go through firmware on_multi_click.
- **Per-device cycle index storage** is closure-local, not on
  `MeetingSession` state. Simpler and the lifecycle matches the
  meeting (cleared on stop).

## Follow-ups

- Add bridge tests for the firmware-event path (currently only the
  bridge-side fallback classifier is covered by unit tests). The
  firmware-event path is integration-style; could mock the new entity
  key + dispatch a synthetic state edge.
- Document the cycle gesture in `docs/HOLDSPEAK_BRIDGE.md` runbook.
