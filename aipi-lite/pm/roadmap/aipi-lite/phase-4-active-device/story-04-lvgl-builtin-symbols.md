# AIPI-4-04 — LVGL Builtin Symbols for Activity Slot

- **Project:** aipi-lite
- **Phase:** 4
- **Status:** done
- **Depends on:** AIPI-2-07 (the activity-symbol map this story modifies)
- **Unblocks:** AIPI-4-02 (block-glyph variant of the mic meter, if rendered)
- **Owner:** karol

## Problem

AIPI-2-07 shipped ASCII activity-symbol glyphs (`>>`, ` *`, `\!//`, `...`, `[?]`, `/!\`) because Montserrat 10's symbol-glyph coverage on this hardware build was unverified. ASCII works but is visually thin — `LV_SYMBOL_AUDIO`, `LV_SYMBOL_PLAY`, and similar constants would lift the device's polish. This story verifies which `LV_SYMBOL_*` constants render correctly and replaces ASCII with the verified set.

## Scope

### In

- Hardware-test which `LV_SYMBOL_*` constants render correctly on this device's LCD with Montserrat 10. Build a fixture YAML that paints each candidate symbol with a label; flash; visually inspect.
- Build the **verified set table**: which symbol → renders / `?` / square box. Document in `docs/LCD_SYMBOLS.md` (new) or appended to `docs/DEVICE_AUDIO_OUTPUT.md`.
- Update `bridge/lcd.py` symbol map to use verified `LV_SYMBOL_*` constants; preserve ASCII fallback for unverified glyphs.
- Mapping intent (subject to verification):
  - `Listening` → `LV_SYMBOL_AUDIO` (or fallback `>>`)
  - `Recording` → `LV_SYMBOL_PLAY` or a record-dot if available (or fallback ` *`)
  - `Bookmark` → `LV_SYMBOL_BOOKMARK` (or fallback `\!//`)
  - `Saving` → `LV_SYMBOL_SAVE` (or fallback `...`)
  - `Busy` → `LV_SYMBOL_WARNING` (or fallback `[?]`)
  - `Error` → `LV_SYMBOL_CLOSE` (or fallback `/!\`)
  - `Ready` / unknown → no symbol (or fallback `─`)
- Update `tests/test_lcd_helpers.py` to parametrise over both the LVGL set and the ASCII fallback set.
- Optional: provide a `prefer_ascii` setting in `bridge.env` for users who want explicit consistency (default: prefer-LVGL-when-rendered).

### Out

- Custom font with extended symbol coverage. LVGL's defaults + Montserrat 10's bundled symbols are the surface; loading a custom font is its own story.
- Multi-color symbols. The activity slot is monochrome.
- Animated symbols (LVGL supports them but the activity slot's revert/flash mechanic doesn't.)

## Acceptance criteria

- [x] Probe built (`pm/probes/aipi-4-04-lvgl-symbols.py` — Python script via aioesphomeapi instead of YAML, faster since no reflash needed) cycling through 49 LV_SYMBOL_* candidates via `update_screen`; flashed-and-visually-inspected step replaced by live observation on the running device.
- [x] Verified set documented in `docs/LCD_SYMBOLS.md` (new): activity-slot map (8 codepoints), error symbol (1), plus a wider list of 38 additional verified codepoints available for future use. Two explicit exclusions: `LV_SYMBOL_GPS` (U+F0F5) + `LV_SYMBOL_BULLET` (U+F87C).
- [x] `bridge/lcd.py` symbol map updated to LVGL codepoints (`AUDIO`, `PLAY`, `KEYBOARD`, `BELL`, `SAVE`, `WARNING`, `OK`); `ERROR_ACTIVITY_SYMBOL` → `LV_SYMBOL_CLOSE`; `DEFAULT_ACTIVITY_SYMBOL` changed to empty string + `_format_activity` updated to drop trailing whitespace when symbol is empty. No per-glyph ASCII fallback needed (all 8 LVGL picks rendered cleanly).
- [x] `tests/test_lcd_helpers.py` + `tests/test_dispatch.py` + `tests/test_bookmark_gesture.py` + `tests/test_holdspeak_leg.py` updated to assert LVGL codepoints (using `chr(0xF0xx)` references for diff-friendliness).
- [x] Manual visual check passed on running hardware: `Recording 00:00  [U+F04B]` paint observed in bridge log + LCD rendered the play-triangle glyph correctly.
- [x] `prefer_ascii=true` setting NOT added — story originally hedged on this; in practice all picks rendered cleanly, so the toggle would be solving a non-problem. Documented in `docs/LCD_SYMBOLS.md` as the rationale.
- [x] Probe deleted post-verification per PMO "delete probes after they resolve" rule.

## Test plan

- **Hardware probe:** the verification YAML is the test. Flash, inspect, record.
- **Unit:** symbol-picker selects the right constant for each state; ASCII fallback returns expected string.
- **Manual:** drive each canonical state from a fake HoldSpeak (status frame fixture); visually confirm correct symbol on LCD.

## Notes

- **`LV_SYMBOL_*` source:** ESPHome's LVGL integration includes the LVGL symbol font automatically when you reference `\uF0xx` codepoints; the question is which codepoints Montserrat 10 (the body font) actually contains. ESPHome's docs say LVGL *automatically* uses a symbol font for symbol codepoints regardless of the body font, but coverage varies by ESPHome version + LVGL version on this build.
- **Coordination with AIPI-4-02:** if block-character glyphs (`▁▃▅▇`) render on this hardware, AIPI-4-02's mic-meter can use them; if not, ASCII bars. This story should also test the block-character glyph set as a side-effect.
- **PMO probe rule:** the verification YAML lives under `pm/probes/`, gets a name like `aipi-4-04-lvgl-symbols.yaml`, and gets deleted in the close-out commit (per AIPI-2-08's deletion of `pm/probes/aipi-1-05-left-button.yaml` after that probe resolved).
- **Why monospace for both ASCII and LVGL:** the activity slot is rendered in a monospace-ish layout; both glyph paths need to fit the same column width to avoid layout reflow.
