# HS-17-15 — `LCD_TEXT_MAX_CHARS` bump (30 → 150)

- **Project:** holdspeak
- **Phase:** 17
- **Status:** done
- **Depends on:** AIPI-4-12 (device-side widget grew multi-line)
- **Owner:** karol

## Problem

HS-17-08 set `LCD_TEXT_MAX_CHARS = 30` based on the original single-
line montserrat_10 middle widget capacity. AIPI-4-12 grew the middle
widget to multi-line wrap with montserrat_8: ~10 lines × ~28 chars =
~280 chars of capacity. The 30-char cap was now leaving ~85% of the
widget empty.

## Scope

### In

- `LCD_TEXT_MAX_CHARS = 30` → `150` in `holdspeak/device_status.py`.
  150 is a comfortable ceiling — leaves a safety margin under the
  ~280-char theoretical max and avoids truncation surprises if the
  device font changes.
- All consumers of `truncate_for_lcd()` get the new ceiling for free
  (per-segment pushback, intel pushback, ack markers, etc.).

### Out

- Per-call configurable ceiling — `max_len` parameter already exists
  for callers that need a tighter cap; no new surface needed.

## Acceptance Criteria

- [x] Constant updated in `device_status.py`.
- [x] `test_truncate_for_lcd_default_is_lcd_max` test asserts the
  new value and the truncation math (`len = LCD_TEXT_MAX_CHARS` for
  overflowing input, ends with `…`).
- [x] `test_push_segment_truncates_long_text` updated to use a
  payload that overflows the new limit.
- [x] Full HS suite passing (1809/1809 passed in session).

## Notes

- Trivial change; filed as its own story for traceability with
  AIPI-4-12's matching firmware capacity grow.
- The 150-char limit applies at the LCD push path only; the durable
  transcript stores untruncated text.
