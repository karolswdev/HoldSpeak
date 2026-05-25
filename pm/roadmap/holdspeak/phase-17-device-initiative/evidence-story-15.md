# Evidence — HS-17-15 — `LCD_TEXT_MAX_CHARS` bump (30 → 150)

- **Shipped:** 2026-05-10
- **Commit:** `2a6a476`
- **Owner:** karol

## Files touched

### `holdspeak/device_status.py`

- `LCD_TEXT_MAX_CHARS = 30` → `LCD_TEXT_MAX_CHARS = 150`.
- Comment block updated to explain the AIPI-4-12 sibling reasoning.

### Tests (`tests/unit/test_device_status_helpers.py`)

- `test_truncate_for_lcd_default_is_lcd_max`: asserts the new
  constant value + the truncation math against `LCD_TEXT_MAX_CHARS +
  1` input.
- `test_push_segment_truncates_long_text`: payload sized to
  `LCD_TEXT_MAX_CHARS * 2` so the test still exercises truncation
  with the new ceiling.

## Verification

```
$ .venv/bin/python -m pytest tests/unit/test_device_status_helpers.py -q
93 passed in 0.07s

$ .venv/bin/python -m pytest -q
1757 passed, 21 skipped     # full suite
```

## Acceptance criteria — re-checked

All brackets `[x]` — see [`story-15-lcd-char-limit-bump.md`](./story-15-lcd-char-limit-bump.md).

## Deviations from plan

- None.

## Follow-ups

- If the device font ever changes (e.g., back to montserrat_10 for
  the middle widget), revisit the 150 ceiling. Currently sized for
  montserrat_8 × ~28 chars per line × ~10 lines.
