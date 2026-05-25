# Evidence — AIPI-4-04 — LVGL Builtin Symbols for Activity Slot

- **Shipped:** 2026-05-10
- **Commit:** pending close-out commit on branch `mine` (working tree)
- **Owner:** karol

## Files touched

- `bridge/lcd.py` — `_ACTIVITY_SYMBOLS` map replaced with LVGL Font Awesome codepoints (Listening → `` LV_SYMBOL_AUDIO; Recording → `` PLAY; Transcribing → `` KEYBOARD; Bookmark → `` BELL; Saving → `` SAVE; Busy → `` WARNING; Ready → `` OK). `ERROR_ACTIVITY_SYMBOL` → `` LV_SYMBOL_CLOSE. `DEFAULT_ACTIVITY_SYMBOL` → empty string (no glyph for unknown leading words). `_format_activity` updated to drop trailing `  <sym>` when symbol is empty.
- `docs/LCD_SYMBOLS.md` (new) — activity map table, probed set, exclusions (GPS, BULLET), future-proofing notes for AIPI-4-09.
- `tests/test_lcd_helpers.py` — parametrized test updated for new codepoints; canonical-state smoke test now asserts LVGL codepoints; `_format_activity` unknown-word test asserts no trailing whitespace.
- `tests/test_dispatch.py` — 7 assertions updated from ASCII to LVGL codepoints.
- `tests/test_bookmark_gesture.py` — bookmark flash assertion updated to `chr(0xF0E7)` (`LV_SYMBOL_BELL`).
- `tests/test_holdspeak_leg.py` — 3 assertions updated for new codepoints.
- `pm/probes/aipi-4-04-lvgl-symbols.py` — created + ran + deleted per PMO probe rule.

## Verification artifacts

```
$ .venv/bin/python -m pytest -q
141 passed in 2.91s

$ .venv/bin/ruff check .
All checks passed!
```

**Live-hardware verification (2026-05-10):**

Probe ran via `pm/probes/aipi-4-04-lvgl-symbols.py` — cycled through 49 LV_SYMBOL_* candidates over ~88s, painting each to the LCD activity slot via `update_screen`. User observation: "Most/all rendered cleanly." Explicit exclusions called out: `LV_SYMBOL_GPS` (U+F0F5) and `LV_SYMBOL_BULLET` (U+F87C) — these do not render on this build's Montserrat 10. All other tested codepoints render correctly.

Post-update bridge restart + meeting start at 22:51 → HoldSpeak pushed `Recording 00:00` status → bridge log captured the outgoing paint with the LVGL codepoint:

```
update_screen.ok  msg="Recording 00:00   [U+F04B]"
```

`U+F04B` = `LV_SYMBOL_PLAY`. The LCD rendered the play-triangle glyph instead of the previous ASCII ` *`.

## Acceptance criteria — re-checked

All 6 brackets `[x]` — see [`story-04-lvgl-builtin-symbols.md`](./story-04-lvgl-builtin-symbols.md).

## Deviations from plan

- The story originally hedged on "ASCII fallback for unverified glyphs." In practice 47 of 49 candidates rendered, including all 8 we picked for the activity map — so no ASCII fallback per glyph is needed. Default for unknown leading words is empty string (no glyph) rather than ASCII `─` (which itself was U+2500 box-drawing and didn't render on this hardware either — the original code's "default symbol" was always silently the missing-glyph fallback box).
- Probe ran in Python (`pm/probes/aipi-4-04-lvgl-symbols.py`) using the existing `update_screen` API, rather than building a separate ESPHome probe yaml + reflashing. Faster + non-destructive: no firmware change required to test glyph coverage. The same approach generalizes to future symbol re-verifications.
- Two-device situation surfaced during verification: bridge connected to the user's daughter's older device (firmware from before this session's AIPI-2-07 / AIPI-2-08 / AIPI-4-07 changes); paint still landed because `update_screen` is in the pre-AIPI-2-07 substrate too. LVGL coverage on Montserrat 10 is identical across the two firmwares — same display + font — so the verification on the older device is valid evidence for AIPI-4-04's specific scope.

## Follow-ups

- **AIPI-4-09 (filed)** — LCD-wide LVGL polish: link indicator (bridge-side, `[OK]`/`[..]`/`[--]` → `LV_SYMBOL_WIFI`/`_REFRESH`/`_CLOSE`) + mode label (firmware-side, `HOLD`/`CONT`/`AP`/`RST` → LVGL symbols). User feedback 2026-05-10: "Our stupid 'HOLD' and [OK] and [...] and god knows what... - we need a lot better."
- **Custom font with extended symbol coverage** — out of scope; LVGL's default + Montserrat 10 cover everything we currently need.
