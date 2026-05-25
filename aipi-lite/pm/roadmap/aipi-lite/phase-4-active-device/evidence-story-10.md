# Evidence — AIPI-4-10 — Activity Sticky Re-publish on Device Reconnect

- **Shipped:** 2026-05-10
- **Commit:** pending close-out commit on branch `mine` (working tree)
- **Owner:** karol

## Files touched

- `bridge/holdspeak.py` — new `republish_sticky_activity()` async method. Companion to AIPI-4-08's `republish_link_state()`; re-fires the most recent sticky activity paint via `on_activity_update`. No-op when `_sticky_activity` is None.
- `bridge/cli.py` — `_on_device_ready` wrapper coroutine calls both `republish_link_state()` then `republish_sticky_activity()`. Link first so the user sees connection state before activity.
- `tests/test_link_retrigger.py` — 4 new cases covering republish-no-sticky, re-fire after sticky, latest-sticky-wins on multiple paints, and flash-paints-don't-update-sticky.

## Verification artifacts

```
$ .venv/bin/python -m pytest -q
145 passed in 2.83s

$ .venv/bin/ruff check .
All checks passed!
```

**Live-hardware verification (2026-05-10):** bridge restarted at 23:08:14. HoldSpeak handshake completed (23:08:14.665) before DeviceLeg cached LCD services — same race that motivated AIPI-4-08. `update_screen.skip reason="service not cached"` confirms the silent no-op of `_paint_activity("Ready")` at handshake. DeviceLeg connected (23:08:14.872) → `_on_device_ready` fired → `republish_sticky_activity()` re-fired the sticky:

```
23:08:14.665  update_screen.skip  reason="service not cached"  ← the bug: silent no-op
23:08:14.872  connect.device.ok
23:08:14.974  update_screen.ok  msg="Ready  "            ← AIPI-4-10 republish fired
```

`` = `LV_SYMBOL_OK` (checkmark). The LCD activity slot now renders `Ready` followed by the checkmark glyph instead of the firmware-default ASCII `Ready`.

User feedback that surfaced this: "why is HOLD not a glyph? And Ready?" — Ready was the bridge-side gap (race-condition silent paint), now closed. HOLD is firmware-owned and tracked separately in AIPI-4-09's firmware half.

## Acceptance criteria — re-checked

All 4 brackets `[x]` — see [`story-10-activity-republish.md`](./story-10-activity-republish.md).

## Deviations from plan

- None. Implementation matched the story's design exactly. The wrapper pattern in `cli.py` (an `_on_device_ready` coroutine that calls two republish methods in sequence) was a minor variation over passing a single method directly, but is equivalent semantically.

## Follow-ups

- AIPI-4-08's evidence file noted that activity-slot republish was deliberately out-of-scope on the assumption HoldSpeak's next status frame would self-heal the activity slot. In practice, between sessions and outside meetings, HoldSpeak doesn't push status frames — hence the gap. AIPI-4-10 closes it.
- Could have been folded into AIPI-4-08 as a single fix, but AIPI-4-08 was already committed and the broader-scope rename (`republish_link_state` → `republish_lcd_state`) would have churned the test suite. Two methods + a wrapper is the lower-churn path.
