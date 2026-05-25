"""LCD-paint constants + helpers.

The bridge owns two of the three LCD label zones (link top-right,
activity bottom). This module is the single place where their state
strings, ttl semantics, and symbol map live so a UX change doesn't
require hunting through `HoldSpeakLeg`.
"""

from __future__ import annotations

# LCD link-state symbols the bridge pushes to the firmware's `link_label`
# (top-right of the LCD) on every WebSocket state transition.
#
# AIPI-4-09 (2026-05-10): switched from ASCII `[OK]`/`[..]`/`[--]` to
# LVGL builtin symbols. Coverage live-verified during AIPI-4-04 — same
# font (Montserrat 10), same display, all three codepoints render.
# Single glyph each instead of 4-char ASCII frees the rest of the
# top-right cell for future status info.
LINK_OFFLINE = ""    # LV_SYMBOL_CLOSE — bridge running, WS down
LINK_CONNECTING = ""  # LV_SYMBOL_REFRESH — WS connecting / handshaking
LINK_ONLINE = ""     # LV_SYMBOL_WIFI — WS connected + handshake complete

# Activity symbols painted at the right edge of the bottom label
# (`<status text>  <symbol>`). The bridge picks a symbol from the
# leading word of HoldSpeak's status text so the firmware doesn't
# need a new release to learn new states.
#
# AIPI-4-04 (2026-05-10): switched from ASCII glyphs to LVGL builtin
# symbols (Font Awesome 5 codepoints in U+F000-U+F8FF). Live-verified
# on hardware against Montserrat 10 — the body font ships with LVGL
# symbol glyph coverage for the codepoints below. Two probed glyphs
# DID NOT render and are not used: LV_SYMBOL_GPS (U+F0F5) and
# LV_SYMBOL_BULLET (U+F87C). See docs/LCD_SYMBOLS.md for the full
# verified set.
_ACTIVITY_SYMBOLS = {
    "Listening": "",     # LV_SYMBOL_AUDIO — speaker icon
    "Recording": "",     # LV_SYMBOL_PLAY — "in progress" triangle
    "Transcribing": "",  # LV_SYMBOL_KEYBOARD
    "Bookmark": "",      # LV_SYMBOL_BELL — "marked moment"
    "Saving": "",        # LV_SYMBOL_SAVE — floppy disk
    "Busy": "",          # LV_SYMBOL_WARNING — yellow triangle
    "Ready": "",         # LV_SYMBOL_OK — checkmark
}
# Unknown HoldSpeak status text → no symbol. Better than picking a
# wrong icon when the bridge doesn't recognize the leading word.
# `_format_activity` skips the trailing `  <sym>` when symbol is empty.
DEFAULT_ACTIVITY_SYMBOL = ""
ERROR_ACTIVITY_SYMBOL = ""  # LV_SYMBOL_CLOSE — X mark

# Default flash durations (ms) for synthesised activity events that
# don't come from a HoldSpeak `status.ttl_ms`.
SESSION_BUSY_FLASH_MS = 3000
ERROR_FLASH_MS = 5000
BOOKMARK_FLASH_MS = 1500


def _pick_activity_symbol(text: str) -> str:
    """Pick an ASCII state symbol from the leading word of `text`.

    Pure helper — exposed for unit tests. Strips trailing punctuation
    from the leading word ("Listening..." → "Listening") so HoldSpeak
    can stylise its status strings naturally without breaking the
    lookup. Unknown leading words map to the default dash so HoldSpeak
    can introduce new status strings without a bridge release.
    """
    leading = text.split(maxsplit=1)[0] if text else ""
    leading = leading.rstrip(".:!?,;")
    return _ACTIVITY_SYMBOLS.get(leading, DEFAULT_ACTIVITY_SYMBOL)


def _format_activity(text: str, symbol: str | None = None) -> str:
    """Format an activity line as `{text}  {symbol}`.

    When `symbol` is None the picker is consulted. `text` is passed
    through unchanged — the bridge does not editorialise HoldSpeak's
    wording.

    AIPI-4-04: an empty symbol (e.g., the default for unknown leading
    words) suppresses the trailing two-spaces-and-glyph so the line
    doesn't end in dangling whitespace.
    """
    sym = symbol if symbol is not None else _pick_activity_symbol(text)
    if not sym:
        return text
    return f"{text}  {sym}"
