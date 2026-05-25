# LCD Symbol Map (AIPI-4-04)

The bridge's activity-slot painter uses LVGL builtin symbols (Font
Awesome 5 codepoints in U+F000–U+F8FF). The device's `default_font:
montserrat_10` in `aipi.yaml` ships LVGL symbol coverage for the
codepoints listed below — verified live 2026-05-10 against the
flashed AIPI-Lite.

## Activity-slot map

Source: `bridge/lcd.py:_ACTIVITY_SYMBOLS`. Codepoints listed as hex
rather than rendered glyphs so this doc reads correctly in tools
that lack the symbol font (diffs, terminal `cat`, GitHub's web view
on hosts without Font Awesome).

| HoldSpeak text starts with | Codepoint | LVGL constant         | Visual hint        |
|---|---|---|---|
| `Listening`    | `U+F001` | `LV_SYMBOL_AUDIO`    | speaker icon       |
| `Recording`    | `U+F04B` | `LV_SYMBOL_PLAY`     | play triangle      |
| `Transcribing` | `U+F0F3` | `LV_SYMBOL_KEYBOARD` | keyboard           |
| `Bookmark`     | `U+F0E7` | `LV_SYMBOL_BELL`     | bell (marked moment) |
| `Saving`       | `U+F0C5` | `LV_SYMBOL_SAVE`     | floppy disk        |
| `Busy`         | `U+F071` | `LV_SYMBOL_WARNING`  | warning triangle   |
| `Ready`        | `U+F00C` | `LV_SYMBOL_OK`       | checkmark          |
| (anything else)|    —     | —                    | empty, no glyph    |

Error frames render with `ERROR_ACTIVITY_SYMBOL`:

| Trigger | Codepoint | LVGL constant | Visual hint |
|---|---|---|---|
| Generic `error` frame, malformed status | `U+F00D` | `LV_SYMBOL_CLOSE` | X mark |

## Probed set

The full set probed live (2026-05-10, via `pm/probes/aipi-4-04-lvgl-symbols.py`,
since deleted per PMO methodology). Most rendered; explicit exclusions:

- `LV_SYMBOL_GPS` (U+F0F5) — **does not render** on this build's
  Montserrat 10. Excluded.
- `LV_SYMBOL_BULLET` (U+F87C) — **does not render**. Excluded.

The full probe covered 49 candidates; the active map uses 8 of them.
The remainder rendered cleanly during the probe and are available
for future use:

- Audio family: `MUTE` (U+F026), `VOLUME_MID` (U+F027), `VOLUME_MAX` (U+F028).
- Media controls: `PAUSE` (U+F04C), `STOP` (U+F04D), `PREV` (U+F048), `NEXT` (U+F051).
- Transport: `EJECT` (U+F052), `LEFT` (U+F053), `RIGHT` (U+F054), `UP` (U+F077), `DOWN` (U+F078), `LOOP` (U+F079).
- Status: `WIFI` (U+F1EB), `BATTERY_EMPTY` (U+F240), `BATTERY_3` (U+F243), `BATTERY_FULL` (U+F244), `BLUETOOTH` (U+F293), `CHARGE` (U+F0C7), `POWER` (U+F011).
- File: `DIRECTORY` (U+F07B), `DOWNLOAD` (U+F019), `UPLOAD` (U+F07C), `DRIVE` (U+F01C), `IMAGE` (U+F03E), `TRASH` (U+F2ED).
- UI: `SETTINGS` (U+F013), `HOME` (U+F015), `REFRESH` (U+F021), `LIST` (U+F00B), `EDIT` (U+F304), `EYE_OPEN` (U+F06E), `PLUS` (U+F067), `MINUS` (U+F068), `BACKSPACE` (U+F55A), `CUT` (U+F083), `COPY` (U+F0C4).
- Misc: `CALL` (U+F080), `VIDEO` (U+F008).

Pick from this verified set when extending the map.

## Future-proofing

- **Default for unknown states** is the empty string (`""`). The
  formatter (`_format_activity`) strips the trailing `  <symbol>`
  when the symbol is empty so the line doesn't end in dangling
  whitespace. Better than picking a wrong glyph for an unknown
  HoldSpeak status — the text itself carries the information.
- **Link indicator polish (AIPI-4-09 follow-up):** the bridge-side
  link indicator currently uses ASCII `[OK]` / `[..]` / `[--]`.
  `LV_SYMBOL_WIFI` (U+F1EB) renders cleanly and is the natural
  `[OK]` replacement; `LV_SYMBOL_REFRESH` (U+F021) is a good
  `[..]` connecting glyph; `LV_SYMBOL_CLOSE` (U+F00D) for `[--]`.
- **Mode label polish (AIPI-4-09 follow-up):** the firmware-side
  mode label currently shows ASCII `HOLD` / `CONT` / `AP` / `RST`.
  Replacing these with LVGL symbols requires an `aipi.yaml` change +
  reflash. `LV_SYMBOL_LOOP` (U+F079) for `CONT` is the obvious win.

## Why we ship LVGL by default (not ASCII)

This hardware build renders LVGL Font Awesome glyphs cleanly. The
ASCII fallbacks we previously used (`>>`, ` *`, `\!//`, `...`, `[?]`,
`/!\`, `─`) look comparatively crude on a graphical LCD perfectly
capable of vector icons. If a future hardware variant loses Font
Awesome coverage in Montserrat 10, the rule is:

1. Rerun the probe (resurrect from git history at this commit).
2. Mark non-rendering codepoints in this doc.
3. Pick a replacement codepoint that does render, OR fall back to
   ASCII for that one state.

The map is data, not policy — easy to change when the surface does.
