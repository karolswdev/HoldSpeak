# Evidence — AIPI-4-13 — TX-arrow widget

- **Shipped:** 2026-05-10
- **Commit:** `768c0b9` (firmware widget + bridge) + `2a6a476` (HoldSpeak `Listening/Thinking` drop)
- **Owner:** karol

## Files touched

### Firmware (`aipi.yaml`)

- New `tx_label` LVGL widget at TOP_RIGHT, `x: -22, y: 4, width: 16,
  text_align: RIGHT, long_mode: CLIP`. Default empty.
- `link_label` width 60 → 16 to make room for tx_label adjacent.
- `right_button.on_press` (non-CONT branch) now paints
  `tx_label = ""` (LV_SYMBOL_UP) instead of touching
  `ai_response_label`.
- `right_button.on_release` clears `tx_label`. No more
  `ai_response_label = "Thinking..."`.

### HoldSpeak (`web_runtime.py`)

- `_on_device_voice_start`: removed `device_status.send(device_id,
  "Listening...")`. Comment notes the AIPI-4-13 reasoning.
- `_on_device_voice_stop`: removed `device_status.send(device_id,
  "Thinking...")`. Snippet truncation bumped 80 → 150 chars (matches
  the new `LCD_TEXT_MAX_CHARS`).

## Verification

OTA-flashed to `aipi-green.local`; restarted bridge + HoldSpeak.

**Live (2026-05-10):** User held right button, then released:

> "Are you showing any speaking?" — user, after testing

The transcript snippet flashed on the **middle** slot
(`Karol: <text>`), and the bottom slot stayed on `Ready ✓` /
`Recording M:SS` throughout. TX arrow visible top-right during hold;
gone on release.

User confirmation: *"Yep. I do see it."* (referring to the snippet
landing on the middle without clobbering the bottom).

## Acceptance criteria — re-checked

All 5 brackets `[x]` — see [`story-13-tx-arrow-widget.md`](./story-13-tx-arrow-widget.md).

## Deviations from plan

- **CONT-mode `↑↓`.** Spec'd in scope but not implemented because the
  CONT firmware path is dormant (continuous mode retired in phase 2).
  Easy follow-up if/when CONT is revived: two-glyph payload in the
  same tx_label.
- **Initial `delayed_off: 50 ms` was unchanged in this story** —
  later reduced to 20 ms by AIPI-4-14 because the double-tap path
  needed faster off-debounce. Both stories touched the same button
  filter chain.

## Follow-ups

- Battery / RSSI icons could share the same top-right glyph-strip
  pattern once AIPI-4-05 bridge half ships.
