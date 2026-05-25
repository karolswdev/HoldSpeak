# AIPI-4-09 — LCD-Wide LVGL Polish (Link Indicator + Mode Label)

- **Project:** aipi-lite
- **Phase:** 4
- **Status:** in-progress (bridge half landed 2026-05-10; firmware half pending reflash)
- **Depends on:** AIPI-4-04 (LVGL coverage verified for the activity slot — same font + LCD, so the link + mode label can use the same symbol set)
- **Unblocks:** —
- **Owner:** karol

## Problem

AIPI-4-04 swapped the activity slot's ASCII glyphs (`>>`, ` *`, `\!//`, etc.) for LVGL builtin symbols (Font Awesome 5). The link indicator (top-right) and mode label (top-left) still use ASCII — `[OK]` / `[..]` / `[--]` for link state, `HOLD` / `CONT` / `AP` / `RST` for mode. User feedback 2026-05-10 after the activity-slot polish landed:

> "It's so populous with many emojis! Our stupid `HOLD` and `[OK]` and `[...]` and god knows what — we need a lot better."

This story closes the rest of the LCD with the same LVGL treatment. Two halves with different change surfaces:

- **Link indicator** (top-right): bridge-side. The bridge already pushes `[OK]` / `[..]` / `[--]` strings via the `update_link` API service. Swapping for LVGL codepoints requires only `bridge/lcd.py` constant changes — no firmware reflash.
- **Mode label** (top-left): firmware-side. The label is painted by the `refresh_mode_label` script in `aipi.yaml` based on Wi-Fi state + `continuous_mode` global. Swapping for LVGL requires editing the script and reflashing — same cost as any firmware change.

## Scope

### In

**Bridge-side link indicator** (`bridge/lcd.py`):
- `LINK_ONLINE` from `"[OK]"` → `""` (LV_SYMBOL_WIFI).
- `LINK_CONNECTING` from `"[..]"` → `""` (LV_SYMBOL_REFRESH — rotation icon, suggests "trying").
- `LINK_OFFLINE` from `"[--]"` → `""` (LV_SYMBOL_CLOSE — X).
- Tests updated to assert codepoints (use `chr(0xF0xx)` pattern from AIPI-4-04).
- `docs/LCD_SYMBOLS.md` extended with a "Link indicator" subsection.
- No firmware change needed — the bridge just paints strings via the existing `update_link` API service.

**Firmware-side mode label** (`aipi.yaml`):
- `refresh_mode_label` script updated to render LVGL codepoints instead of `HOLD` / `CONT` / `AP` / `RST`.
- Candidates (subject to live verification, but probable set):
  - `HOLD` → `LV_SYMBOL_KEYBOARD` (U+F0F3) or `LV_SYMBOL_PLUS` (U+F067, suggests "press to add input"). KEYBOARD overloads with Transcribing in the activity slot; PLUS is cleaner.
  - `CONT` → `LV_SYMBOL_LOOP` (U+F079) — "loop"/"continuous", perfect fit.
  - `AP` → `LV_SYMBOL_WIFI` (U+F1EB) + maybe `LV_SYMBOL_PLUS` overlaid; or `LV_SYMBOL_HOME` (U+F015 — "starting fresh"). Pick during implementation; AP is rare enough that any unambiguous symbol works.
  - `RST` → `LV_SYMBOL_REFRESH` (U+F021) — "reset"/"restart", obvious fit.
- After firmware change, the mode label is one glyph not 4 chars — saves LCD real estate.
- Documentation updated: `docs/LCD_SYMBOLS.md` extended with a "Mode label" subsection; runbook `docs/HOLDSPEAK_BRIDGE.md` if it references the old labels.
- Reflash required.

### Out

- Animated glyphs (LVGL supports them via styles, but the existing label substrate is one-glyph-at-a-time).
- Multi-glyph mode labels (e.g., `HOLD` + a `LV_SYMBOL_KEYBOARD` icon side-by-side). The labels are 4 chars wide max in current layout — sticking to a single glyph keeps the layout stable.
- A `prefer_ascii=true` setting for users who want the old labels back. AIPI-4-04 settled this — LVGL renders cleanly on this hardware; ASCII fallback adds complexity for no benefit. If a future hardware variant needs ASCII, branch the firmware.
- Replacing the activity-slot ASCII fallback. That was AIPI-4-04; nothing here.

## Acceptance Criteria

- [x] `bridge/lcd.py`: `LINK_ONLINE` / `LINK_CONNECTING` / `LINK_OFFLINE` switched to LVGL codepoints (`LV_SYMBOL_WIFI` / `LV_SYMBOL_REFRESH` / `LV_SYMBOL_CLOSE`). Tests updated (`tests/test_holdspeak_leg.py` link-transition tests now import the constants); suite 145/145 green; ruff clean.
- [ ] `aipi.yaml`: `refresh_mode_label` script renders LVGL codepoints. Compile + flash succeeds.
- [ ] `docs/LCD_SYMBOLS.md` extended with link-indicator + mode-label subsections.
- [ ] `docs/HOLDSPEAK_BRIDGE.md` updated if it references the old text labels.
- [x] Live verification (bridge-side, no reflash, 2026-05-10): bridge restart → `update_link.ok state=""` fired at 23:04:31.751 (LV_SYMBOL_WIFI) on connection to the primary device. User confirmed WiFi glyph visible on LCD top-right.
- [ ] Live verification (firmware-side, with reflash): LCD's top-left shows the chosen LVGL glyph for each mode; verify all four states (HOLD/CONT default boot, CONT after triple-tap, AP on Wi-Fi failure, RST during factory-reset).

## Test Plan

- **Unit:** bridge-side constant test (test_lcd_helpers.py or a small new file). Pure assertion that the new constants are the right codepoints.
- **Integration:** no new automated test required — the existing `test_holdspeak_leg.py` link-transition tests already check `_call_link` paint sequence; they'll naturally exercise the new codepoints with my changes.
- **Live hardware:** observation of LCD during bridge lifecycle + mode-cycle.

## Notes

- **Splittable:** the bridge-side link indicator change can ship independently of the firmware-side mode label change. Recommend landing the bridge half first (no reflash) so the user gets immediate visual win, then planning the firmware half with the next reflash window.
- **Symbol choices for the mode label are reversible** — they're 4 codepoint constants in a lambda. Adjust based on live observation.
- **Why not a richer Bluetooth/battery/RSSI strip in the LCD's top row** — those would require firmware changes to add more LVGL labels + a status bar layout. Out of scope here; could be a phase-5 polish story if AIPI-4-05 (battery + RSSI pushback) ships and we want the device to display its own health.
- **`LV_SYMBOL_WIFI` for online is intuitive** — users associate WiFi icon with "connected to the network." `LV_SYMBOL_CLOSE` for offline is unambiguous. `LV_SYMBOL_REFRESH` for connecting suggests "in motion."
