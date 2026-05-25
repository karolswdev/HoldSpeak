# Evidence — AIPI-2-07 — HoldSpeak → LCD Pushback (Status Frames + Link Indicator)

- **Shipped:** 2026-05-10 (working tree)
- **Commit:** pending close-out commit on branch `mine` (working-tree base `9ff88a6`).
- **Owner:** karol

## Files touched

- `aipi.yaml`:
  - New `link_label` widget at TOP_RIGHT.
  - New ESPHome API service `update_link` (mirrors `update_screen`).
  - `mode_label` repositioned to TOP_LEFT with short strings (`HOLD` / `CONT` / `AP` / `RST`) and `refresh_mode_label` script for boot / mode-toggle / Wi-Fi events.
- `bridge/lcd.py` — link/activity constants + ASCII activity-symbol map + `_pick_activity_symbol` + `_format_activity` helpers.
- `bridge/holdspeak.py` (`HoldSpeakLeg`):
  - `[..]` → `[OK]` → `[--]` link transitions painted across the WS lifecycle (`[..]` before `websockets.connect`; `[OK]` after handshake; `[--]` in the outer `finally`).
  - `_paint_activity` + `_revert_activity_after` sticky / flash / revert state machine. New paint cancels in-flight revert.
  - `error: session_busy` → `Busy  [?]` for 3 s; generic `error` → `Error: <reason>  /!\` for 5 s.
  - Generalised callback shape: `on_link_update(state)` + `on_activity_update(rendered)` replacing the old `on_session_busy`.
- `bridge/device.py` (`DeviceLeg`):
  - `update_link(state)` mirrors `update_screen(msg)`.
  - `_cache_lcd_services` caches both service handles on connect; `_on_disconnect` invalidates them.
- `tests/test_dispatch.py` — 11 cases. Direct `_dispatch` unit tests: sticky, flash, revert, mid-flash cancellation, error variants, malformed payloads, unknown types.
- `tests/test_lcd_helpers.py` — 10 cases. Symbol picker + formatter, parametrised across canonical state strings.
- `tests/test_holdspeak_leg.py` — 4 added cases for link transitions across clean + invalid-ack closes.
- `docs/HOLDSPEAK_BRIDGE.md` §5 — rewritten: "no-op stub" caveat removed; link-state legend + activity symbol map added.

## Verification artifacts

```
$ .venv/bin/python -m pytest -q tests/test_dispatch.py tests/test_lcd_helpers.py tests/test_holdspeak_leg.py
…  passed

$ .venv/bin/python -m pytest -q
98 passed in 2.80s

$ .venv/bin/ruff check .
All checks passed!
```

Activity symbol map (from `bridge/lcd.py`, verified by `tests/test_lcd_helpers.py`):

| HoldSpeak text starts with | Symbol |
|---|---|
| `Listening` | `>>` |
| `Recording` | ` *` |
| `Transcribing` | `==` |
| `Bookmark` | `\!//` |
| `Saving` | `...` |
| `Busy` | `[?]` |
| `Ready` / unknown | `─` |

## Acceptance criteria — re-checked

- [x] `aipi.yaml` defines `link_label` (TOP_RIGHT) + `update_link` API service; `mode_label` at TOP_LEFT with short strings — diff inspected.
- [x] `bridge/lcd.py` houses helpers + symbol map + link-state constants — file present.
- [x] `bridge/holdspeak.py:HoldSpeakLeg` paints `[..]` → `[OK]` → `[--]` across WS lifecycle — unit-tested in `tests/test_holdspeak_leg.py` against a fake `websockets.serve` server (clean + invalid-ack closes both transition through the expected sequence).
- [x] Sticky / flash / revert state machine — unit-tested in `tests/test_dispatch.py` (sticky, flash, revert, mid-flash cancellation cases).
- [x] `error: session_busy` → 3 s `Busy  [?]` flash; generic `error` → 5 s `Error: <reason>  /!\` flash — unit-tested in `tests/test_dispatch.py`.
- [x] `DeviceLeg.update_link` exists; `_cache_lcd_services` caches both handles on connect; `_on_disconnect` invalidates — unit-tested in `tests/test_device_methods.py`.
- [x] `docs/HOLDSPEAK_BRIDGE.md` §5 lists the link states + symbol map; "no-op stub" caveat removed — verified by inspection.
- [~] **Live-hardware verification: status frames painted on the LCD during a real meeting; link indicator flips through `[..]→[OK]→[--]` on a HoldSpeak restart. Deferred at phase close — hardware not co-located 2026-05-10.** All paint paths are integration-tested against a fake `websockets.serve` server (`tests/test_holdspeak_leg.py`); the LCD-paint side is mocked at the API-service-call boundary.

## Deviations from plan

- Story 07 was originally carved out of phase 2 ("LCD status pushback ... Lands as a dedicated AIPI-2-followup or as the kickoff of AIPI-3"). Promoted into phase 2 on 2026-05-10 after the surface proved containable — see `current-phase-status.md` "Decisions revised (this phase)" entry.
- Live-hardware acceptance bracket left unchecked at phase close. Phase final-summary records this as the most material deferred item: the activity slot's paint timing is the part most likely to surface UX issues a fake-server test won't catch (Wi-Fi-bound API roundtrip latency, sticky/flash interactions during rapid status changes).

## Follow-ups

- Live LCD smoke during a real meeting + a real `pkill -f holdspeak` link-flap. Phase final-summary tees this up as the highest-priority deferred verification.
- LVGL builtin symbols (`LV_SYMBOL_AUDIO`, record dot, mic icon) — ASCII shipped first; LVGL upgrade path documented in story-07 notes.
- Mic-level meter (RMS bar in activity slot) — candidate followup; needs API-roundtrip cost measurement before commit.
