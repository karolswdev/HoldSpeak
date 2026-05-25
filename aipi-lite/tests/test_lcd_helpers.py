"""Pure-function tests for the bridge's activity symbol picker + formatter.

Sister to `test_models.py`: these helpers are how the bridge translates
HoldSpeak's free-form status text into the `<text>  <symbol>` line the
firmware paints on the bottom LCD label. Coverage is here so future
edits can iterate the symbol map without spinning up a whole session.
"""

from __future__ import annotations

import pytest

from bridge import (
    _ACTIVITY_SYMBOLS,
    DEFAULT_ACTIVITY_SYMBOL,
    _format_activity,
    _pick_activity_symbol,
)


def test_picker_known_word_returns_mapped_symbol():
    assert _pick_activity_symbol("Listening...") == _ACTIVITY_SYMBOLS["Listening"]
    assert _pick_activity_symbol("Recording 12:34") == _ACTIVITY_SYMBOLS["Recording"]
    assert _pick_activity_symbol("Bookmark @ 47s") == _ACTIVITY_SYMBOLS["Bookmark"]
    assert _pick_activity_symbol("Saving meeting...") == _ACTIVITY_SYMBOLS["Saving"]


def test_picker_unknown_word_returns_default():
    assert _pick_activity_symbol("Reticulating splines") == DEFAULT_ACTIVITY_SYMBOL
    assert _pick_activity_symbol("WAT") == DEFAULT_ACTIVITY_SYMBOL


def test_picker_empty_text_returns_default():
    assert _pick_activity_symbol("") == DEFAULT_ACTIVITY_SYMBOL


def test_picker_is_case_sensitive():
    """Document the deliberate choice — HoldSpeak's strings are
    consistently capitalised; matching exactly avoids accidental matches
    on transcript words like "listening" appearing inside text."""
    assert _pick_activity_symbol("listening...") == DEFAULT_ACTIVITY_SYMBOL


def test_format_uses_picker_for_default_symbol():
    rendered = _format_activity("Recording 12:34")
    assert rendered == f"Recording 12:34  {_ACTIVITY_SYMBOLS['Recording']}"


def test_format_respects_explicit_symbol_override():
    """Error frames + session_busy pass an explicit symbol that
    overrides the picker. Confirm the override wins."""
    rendered = _format_activity("Busy", symbol="")  # LV_SYMBOL_WARNING
    assert rendered == "Busy  "


def test_format_unknown_word_omits_trailing_symbol():
    """AIPI-4-04: default symbol is empty (no glyph for unknown
    states); the formatter must drop the trailing `  ` instead of
    leaving dangling whitespace."""
    rendered = _format_activity("Reticulating splines")
    assert rendered == "Reticulating splines"


@pytest.mark.parametrize(
    "text,expected_codepoint",
    [
        ("Listening...", ""),     # LV_SYMBOL_AUDIO
        ("Recording 00:00", ""),  # LV_SYMBOL_PLAY
        ("Transcribing...", ""),  # LV_SYMBOL_KEYBOARD
        ("Bookmark @ 47s", ""),   # LV_SYMBOL_BELL
        ("Saving meeting...", ""),  # LV_SYMBOL_SAVE
        ("Ready", ""),            # LV_SYMBOL_OK
    ],
)
def test_format_renders_each_canonical_state(text, expected_codepoint):
    """Smoke-test the table — these are the strings HoldSpeak is
    documented to send, and the corresponding LVGL symbols the bridge
    ships (AIPI-4-04). Codepoints verified live 2026-05-10 on Montserrat 10."""
    rendered = _format_activity(text)
    assert expected_codepoint in rendered, (
        f"{text!r} → {rendered!r} did not contain U+{ord(expected_codepoint):04X}"
    )
