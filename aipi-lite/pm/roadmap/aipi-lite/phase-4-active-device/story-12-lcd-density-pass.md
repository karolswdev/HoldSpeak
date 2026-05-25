# AIPI-4-12 — LCD density pass: multi-line middle + montserrat_8 + scroll bottom

- **Project:** aipi-lite
- **Phase:** 4
- **Status:** done
- **Depends on:** AIPI-4-11 (middle LCD zone substrate)
- **Owner:** karol

## Problem

After AIPI-4-11 shipped the middle slot, the widget was a single line of
montserrat_10 at the screen's vertical center. The bottom slot used
WRAP. Two limits surfaced in the live tuning session 2026-05-10:

1. **Middle slot was tiny.** A single 12 px line could hold ~30 chars
   of montserrat_10. Long transcript flashes got truncated with an
   ellipsis after 30 chars; intel rotations had no room to rotate
   through interesting payloads.
2. **Bottom slot WRAP wrapped silently.** Multi-line `Recording M:SS`
   text would clip when the bottom widget didn't have height for the
   extra line.

User feedback during the session was direct: *"we could fit a TON of
text if we did it intelligently on our esp device, no?"*

## Scope

### In

- Grow `lcd_middle_label` from `align: CENTER, width: 120, height:
  default` to `align: TOP_MID, y: 20, width: 124, height: 85` so it
  claims the dead space between the top widgets and the bottom slot.
- Switch `lcd_middle_label.text_font` from default (montserrat_10) to
  `montserrat_8` so each line drops from ~12 px to ~9 px and total
  capacity goes from ~3 lines to ~10 lines.
- Switch `ai_response_label` (bottom) `long_mode` from `WRAP` to
  `SCROLL_CIRCULAR` so long payloads marquee-scroll horizontally
  instead of clipping.
- Bump HoldSpeak's `LCD_TEXT_MAX_CHARS` from 30 to 150 (HS-17-15) so
  upstream truncation matches the new widget capacity.

### Out

- Custom non-LVGL-builtin fonts — explored (`gfonts://Silkscreen` at
  size 6 baked in via ESPHome's gfonts integration) but reverted; 6 px
  was unreadable on this LCD at desk distance.
- Container-based vertical scroll on the middle widget. LVGL labels
  don't natively scroll wrapped multi-line content; would need a
  scrollable parent obj or `lv_textarea`. Out of scope; AIPI-4-14
  paged-rotation pattern (cycle stats / paged intel) covers the
  "more content than fits" case at the protocol layer instead.

## Acceptance Criteria

- [x] `lcd_middle_label` is multi-line WRAP, ~10 lines × ~28 chars at
  montserrat_8.
- [x] `ai_response_label` runs `SCROLL_CIRCULAR`; short payloads still
  render static.
- [x] HoldSpeak's `LCD_TEXT_MAX_CHARS` set to 150.
- [x] Compiled + OTA-flashed to `aipi-green.local` 2026-05-10.
- [x] Live verification: 299-char test payload pushed via probe
  script wraps cleanly across the middle without clipping; user
  confirmed visually.

## Notes

- **Why montserrat_8 not unscii_8?** unscii_8 is pixel-perfect bitmap
  but monospace (~20 chars/line at 124 px) and has no Font Awesome
  glyphs. montserrat_8 is proportional (~28 chars/line) and still
  legible; FA isn't needed in the middle slot anyway.
- **Why y=20 not y=14?** The top widgets (mode_label + link_label +
  tx_label from AIPI-4-13) occupy ~16 px vertical. 4 px buffer keeps
  the visual breathing room while still claiming most of the middle.
- **Bottom-slot SCROLL_CIRCULAR trade-off.** When text fits the
  widget, no scroll. When text overflows, it marquee-scrolls. The
  cost is the user sees motion on overflow, which can be distracting
  for an always-on tick like `Recording M:SS` — but those payloads
  fit comfortably so scroll is dormant most of the time.
