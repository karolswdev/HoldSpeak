# Evidence — AIPI-4-01 — Bookmark Gesture (Left-Button Quick-Tap During Meeting)

- **Shipped:** 2026-05-10
- **Commit:** pending close-out commit on branch `mine` (working tree)
- **Owner:** karol

## Files touched

### Bridge (Python)

- `bridge/device.py` — `_cache_button_entities` resolves real + sim left-button entity keys; `_handle_state_change` dispatches when key matches either; `_handle_left_button_state` classifies short vs. long press against `BOOKMARK_PRESS_THRESHOLD_MS=500`; `_spawn_bookmark_attempt` + `_fire_bookmark_attempt` emit `EventFrame(name="long_press", at=time.time())` and call `paint_bookmark_flash` when `is_in_meeting()` returns True.
- `bridge/holdspeak.py` — new `_sticky_text` field tracks the raw status text (alongside the existing `_sticky_activity` rendered string); `is_in_meeting()` returns True iff sticky starts with `Recording`; `paint_bookmark_flash()` wraps `_paint_activity` with `BOOKMARK_FLASH_MS=1500` and the `Bookmark` symbol.
- `bridge/lcd.py` — added `BOOKMARK_FLASH_MS = 1500` constant.
- `bridge/cli.py` — `_run` wires `device.is_in_meeting = holdspeak.is_in_meeting` and `device.paint_bookmark_flash = holdspeak.paint_bookmark_flash` post-construction (closes the leg dependency cycle).

### Tests

- `tests/test_bookmark_gesture.py` — 23 cases: `_cache_button_entities` (real + sim resolution; missing entity; lookup error); `_handle_state_change` dispatch (uncached / other-key / real-key / sim-key); `_handle_left_button_state` classifier (press timestamp; short-press spawn; long-press no-spawn; release-without-press; press-press-release latest-wins; post-release timestamp clear); `_fire_bookmark_attempt` gating + emission (in-meeting emit + flash + `at` timestamp; outside-meeting suppression; unwired-callback suppression; flash-error swallowing); `HoldSpeakLeg.is_in_meeting` (default / Recording / Listening / Ready); `HoldSpeakLeg.paint_bookmark_flash` (callback path + sticky preservation).

## Verification artifacts

```
$ .venv/bin/python -m pytest -q
131 passed in 2.82s

$ .venv/bin/ruff check .
All checks passed!
```

**Live-hardware verification (2026-05-10):**

Bridge running, HoldSpeak running on `127.0.0.1:38869`, device flashed with `aipi.yaml` ≥ AIPI-4-07 (so the `simulate_left_press` service was available to drive the gesture remotely):

```
21:01:05.963  loop.ready
21:01:05.974  handshake.send (device_id=aipi-1, label=Karol, version=1)
21:01:05.975  connect.holdspeak.handshake.ok
21:01:06.199  connect.device.ok (host=aipi.local, port=6053)
```

Meeting started via `POST /api/meeting/start {"devices":["aipi-1"]}` at 21:01:25. HoldSpeak pushed `Recording 00:00 ttl_ms=0` (sticky); bridge painted `Recording 00:00   *` to LCD via `update_screen`.

`python -m bridge --press left-short` fired at 21:01:41:

```
21:01:41.599  device  event.bookmark.emitted
21:01:41.599  device  update_screen.ok msg="Bookmark  \!//"
21:01:41.607  holdspeak ws.status.recv text="Bookmark @ 16s" ttl_ms=2500
21:01:41.607  device  update_screen.ok msg="Bookmark @ 16s  \!//"
21:01:44.108  device  update_screen.ok msg="Recording 00:00   *"  (TTL revert)
```

Meeting stopped 21:02:20; saved meeting state at `GET /api/meetings/380b38e5`:

```json
{
  "id": "380b38e5",
  "started_at": "2026-05-10T15:01:25.982757",
  "ended_at": "2026-05-10T15:02:19.995910",
  "bookmarks": [
    {
      "timestamp": 15.62406,
      "label": "Bookmark @ 00:15",
      "created_at": "2026-05-10T15:01:41.606825"
    }
  ]
}
```

Bookmark `timestamp: 15.62406s` corresponds to `(21:01:41.60 - 21:01:25.98) = 15.62 s` into the meeting — exact match.

**Out-of-meeting suppression:** prior to starting the meeting, 5 separate `--press left-short` invocations during this same session each logged `event.suppressed gesture=bookmark reason=not_in_meeting`; zero transcript bookmarks generated. Verified in the bridge log timeline (20:51:59, 20:52:02, 20:53:39, 20:55:13, 20:57:07).

## Acceptance criteria — re-checked

- [x] Design decision (classifier bridge-side, no `aipi.yaml` change for gesture) — landed in code.
- [x] Bridge subscribes via `subscribe_states`; classifier with 500 ms threshold — verified live; `_cache_button_entities` resolves both `left_button` and `left_button_sim` keys (via AIPI-4-07).
- [x] In-meeting short-press emits `EventFrame(name="long_press", at=<unix_seconds>)` — verified live; bookmark `timestamp: 15.62406s, created_at: 2026-05-10T15:01:41.606825` recorded by HoldSpeak server-side.
- [x] Out-of-meeting suppression: `event.suppressed reason=not_in_meeting`; no frame emitted — verified live (5 invocations).
- [x] LCD flash + revert via existing `_paint_activity` mechanism — verified live (`update_screen.ok msg="Bookmark  \!//"` at 21:01:41.599; TTL revert to `Recording 00:00   *` at 21:01:44.108).
- [x] HoldSpeak meeting transcript shows the bookmark at the press timestamp — verified live (saved meeting JSON above).
- [x] Tests: model + classifier + gating coverage — `tests/test_bookmark_gesture.py` 23 cases, 131/131 suite passing.

## Deviations from plan

- The story originally proposed two separate test files (`test_event_frame.py` for model round-trip + `test_bookmark_gating.py` for gating). Combined into one file `tests/test_bookmark_gesture.py`. Model round-trip was already covered by `tests/test_models.py` from AIPI-2-01.
- The `at` field on `EventFrame` is unix-seconds float (`time.time()`), not unix-ms. Matches `holdspeak_proto.EventFrame.at: float | None` shape. The story originally said `<unix_ms>`; reality is float seconds. Recorded for honesty.
- Live verification was done via the AIPI-4-07 `--press left-short` path rather than a physical button press. The bridge-side dispatcher treats real + sim entity state changes identically (dual-key dispatch in `_handle_state_change`), so the bridge code path is the same; the firmware-side path differs (real GPIO press vs. template binary_sensor publish) but is equivalent from the bridge's perspective.

## Follow-ups

- **Physical button press verification** with the device's actual left button (not the simulated path). The dispatcher chain is the same; this would only catch differences in how the firmware emits state changes for GPIO vs. template binary_sensor. Low risk; defer until convenient.
- **Server-pushed `Bookmark @ 16s` confirmation**: HoldSpeak's HS-14-07 status emitter pushes a bookmark-confirmation status frame after server-side bookmark creation. This is HoldSpeak side, validated indirectly by the LCD pushback chain. No follow-up needed on the AIPI-Lite side.
