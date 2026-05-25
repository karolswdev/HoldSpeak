# Evidence — AIPI-4-11 — Middle LCD Zone for Transient Flashes

- **Shipped:** 2026-05-10
- **Commit:** pending close-out commit on branch `mine` (working tree)
- **Owner:** karol

## Files touched

### Firmware (`aipi.yaml`)

- New `lcd_middle_label` LVGL widget (CENTER align, 120 px wide, single line, default empty).
- New `update_middle` ESPHome API service mirroring `update_screen` / `update_link`.
- Compiled + OTA-flashed to `aipi-green.local` via `esphome -s device_name aipi-green run aipi.yaml --device aipi-green.local --no-logs`. OTA worked first try (the `ota: - platform: esphome` block baked in during the AIPI-4-07 reflash earlier in the session enabled this).

### Bridge

- `bridge/device.py`:
  - New `_update_middle_service` cache field; populated by `_cache_lcd_services` alongside `update_screen` + `update_link`.
  - New `update_middle(text)` async method calling `execute_service(_update_middle_service, ...)`. Falls back to silent skip when the service is missing (pre-AIPI-4-11 firmware) with a one-time warning log.
  - `_on_disconnect` invalidates the new service handle.
- `bridge/holdspeak.py`:
  - New `on_middle_update` callback (optional kwarg on `__init__`).
  - `_paint_activity` refactored to route by `ttl_ms`:
    - `ttl_ms == 0` (sticky) → `_call_activity` (bottom slot). Updates `_sticky_activity` + `_sticky_text` as before.
    - `ttl_ms > 0` (flash) → `_call_middle` (middle slot). Schedules `_clear_middle_after(ttl_ms / 1000)` which paints empty string after the TTL.
  - Renamed `_activity_revert_task` → `_middle_clear_task` (semantics changed from "re-paint sticky" to "empty the middle slot").
  - New `_call_middle(rendered)` helper paralleling `_call_activity`.
- `bridge/cli.py`:
  - New `_on_middle` async wrapper calling `device.update_middle`.
  - Passes `on_middle_update=_on_middle` to `HoldSpeakLeg`.

### Tests

- `tests/test_dispatch.py`: `_make_leg()` returns 4-tuple including `middle_paints`; sticky tests assert bottom + empty middle; flash tests (status flash, session_busy, generic error) assert middle + empty bottom; "new-paint-during-flash-cancels-revert" rewritten to verify middle-clear cancellation + bottom-sticky-untouched.
- `tests/test_holdspeak_leg.py`: `_build_leg` accepts `on_middle_update`; `test_session_busy_paints_middle_with_busy_symbol` (renamed from `_paints_activity_with_`); `test_session_status_flash_paints_middle_and_clears` (renamed from `_flash_reverts_to_sticky`) asserts the new clear-not-revert behavior + verifies bottom sticky untouched.
- `tests/test_bookmark_gesture.py`: `test_holdspeak_paint_bookmark_flash_calls_middle_callback` (renamed from `_activity_callback`) asserts bookmark flash hits middle, not activity.

## Verification artifacts

```
$ .venv/bin/python -m pytest -q
145 passed in 3.34s

$ .venv/bin/ruff check .
All checks passed!
```

**Live-hardware verification (2026-05-10):** AIPI-Lite `aipi-green.local`, bridge connected, HoldSpeak running (with HS-17-05 cadence bumped to 1s + HS-17-13 noise filter — sibling changes in the same session). Started meeting `0f6c3773`. User held the right button and spoke a sentence.

Bridge log over the ~4-minute meeting:

```
update_screen.ok  Recording 00:00  ─ ... Recording 03:57    (238 ticks, 1/s)
update_middle.ok  Karol: stupidly enough that                  ttl=3000 flash
update_middle.ok  ""                                            (auto-clear)
update_middle.ok  Karol: Okay, it's just a dumb…              ttl=3000 flash
update_middle.ok  ""                                            (auto-clear)
```

Independence verified: the bottom ticked every 1 second uninterrupted (238 sequential `update_screen` paints) while the middle flashed real speech + cleared. Zero collisions. Zero `Me: ...` or `Remote: You` noise (HS-17-13 filter working in parallel).

User confirmed: *"yeah, for some seconds I saw a center screen with my speech there."*

## Acceptance criteria — re-checked

6 of 7 brackets `[x]` — see [`story-11-middle-lcd-zone.md`](./story-11-middle-lcd-zone.md). The one open bracket (runbook update) is a small follow-up, non-blocking.

## Deviations from plan

- The `_paint_activity` refactor was cleaner than the story spec'd: instead of adding a parallel `_paint_middle` method, the existing function routes by ttl_ms internally. Single entry point keeps the dispatch tidy.
- The middle slot's revert mechanic is "clear to empty" (paint `""`) rather than "revert to last middle content." Simpler + matches the user's mental model (transient content has no memory). If a future story wants "last segment stays til replaced," it's a small change.
- Bookmark flash (`paint_bookmark_flash` in AIPI-4-01) now lands in the middle automatically via the refactored `_paint_activity` — no new code in that path. Free dividend of the lifetime-based routing.

## Follow-ups

- **`docs/HOLDSPEAK_BRIDGE.md` runbook update** — small content addition describing the three-zone layout. Defer to next runbook touch.
- **AIPI-4-09 firmware half** (HOLD/CONT/AP/RST → glyphs) still pending — same reflash window now that OTA is wired could carry it.
- **HS-17-09 (realtime action items)** and other HS-17 push-back stories now have a natural home (middle slot). Pairs perfectly.
