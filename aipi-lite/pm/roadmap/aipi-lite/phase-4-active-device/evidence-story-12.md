# Evidence — AIPI-4-12 — LCD density pass

- **Shipped:** 2026-05-10
- **Commit:** `768c0b9` (firmware+bridge) + `2a6a476` (HoldSpeak 150-char limit)
- **Owner:** karol

## Files touched

### Firmware (`aipi.yaml`)

- `lcd_middle_label` widget: `align: CENTER` → `align: TOP_MID, y: 20,
  width: 124, height: 85`; `text_font: montserrat_8` added.
- `ai_response_label` widget: `long_mode: WRAP` → `long_mode:
  SCROLL_CIRCULAR`; width 120 → 124.
- OTA-flashed to `aipi-green.local` via `esphome run aipi.yaml
  --device aipi-green.local --no-logs -s device_name aipi-green`.

### HoldSpeak (HS-17-15 sibling)

- `holdspeak/device_status.py`: `LCD_TEXT_MAX_CHARS = 30` → `150`.
- `tests/unit/test_device_status_helpers.py`: `test_truncate_for_lcd_default_is_lcd_max`
  asserts the new constant + truncation behaviour.

## Verification

```
$ .venv/bin/python -m pytest -q
145/145 passed (firmware+bridge side)
93/93 passed (HoldSpeak device_status helpers)
```

**Live (2026-05-10):** Pushed a 299-char test payload via probe:

```python
txt = ("Karol: this is a much longer transcript meant to exercise the
       8 px font + wider middle widget. With Montserrat 8 we should
       fit around ten lines of about twenty-eight characters each,
       plenty of room for a whole paragraph, intel snippets, action
       items, or multiple stacked segments. Read me on the LCD.")
await c.execute_service(service=middle, data={"msg": txt})
```

User confirmed visually: *"It does wrap and does look good"*. Bottom
widget tested with `Recording M:SS` ticks — short payload renders
static (no marquee on payloads that fit).

## Acceptance criteria — re-checked

All 5 brackets `[x]` — see [`story-12-lcd-density-pass.md`](./story-12-lcd-density-pass.md).

## Deviations from plan

- **Briefly tried 6 px gfonts Silkscreen.** Compiled, OTA'd, pushed
  test payload — user feedback was *"very hard to read"*. Reverted to
  montserrat_8 in same session. The dafont/Silkscreen experiment
  proved ESPHome's gfonts integration works (useful to know for
  future custom-font needs) even though the specific font wasn't
  legible at this size on this hardware.
- **Considered unscii_8.** It's a pixel-perfect bitmap font available
  as an LVGL builtin. Tried but its monospace width (~20 chars/line)
  was less dense than montserrat_8's proportional (~28). Reverted.

## Follow-ups

- AIPI-4-09 firmware half (mode-label glyphs) is the natural next
  LCD-polish move now that the widget capacity is sorted.
- Vertical scroll for content overflow within the middle widget
  (LVGL doesn't support this for `lv_label`); workaround is paged
  rotation at the protocol layer (AIPI-4-14 cycle, HS-17-07 paged
  intel).
