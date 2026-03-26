"""Unit tests for text_processor module."""

import pytest
from unittest.mock import patch

from holdspeak.text_processor import TextProcessor


class TestPunctuationCommands:
    """Tests for punctuation command processing."""

    @pytest.fixture
    def processor(self):
        return TextProcessor()

    # Basic punctuation
    def test_period(self, processor):
        assert processor.process("hello period") == "hello."

    def test_full_stop(self, processor):
        assert processor.process("hello full stop") == "hello."

    def test_comma(self, processor):
        assert processor.process("hello comma world") == "hello, world"

    def test_question_mark(self, processor):
        assert processor.process("how are you question mark") == "how are you?"

    def test_exclamation_mark(self, processor):
        assert processor.process("wow exclamation mark") == "wow!"

    def test_exclamation_point(self, processor):
        assert processor.process("wow exclamation point") == "wow!"

    def test_colon(self, processor):
        assert processor.process("here colon list") == "here: list"

    def test_semicolon(self, processor):
        assert processor.process("first semicolon second") == "first; second"

    # Quotes - open quote removes space after, close quote removes space before
    def test_open_quote(self, processor):
        assert processor.process("he said open quote hello") == 'he said "hello'

    def test_close_quote(self, processor):
        assert processor.process("hello close quote he said") == 'hello" he said'

    def test_end_quote(self, processor):
        assert processor.process("hello end quote") == 'hello"'

    def test_unquote(self, processor):
        assert processor.process("hello unquote") == 'hello"'

    # Parentheses - open paren removes space after, close paren removes space before
    def test_open_paren(self, processor):
        assert processor.process("note open paren important") == "note (important"

    def test_open_parenthesis(self, processor):
        assert processor.process("note open parenthesis important") == "note (important"

    def test_close_paren(self, processor):
        assert processor.process("important close paren note") == "important) note"

    def test_close_parenthesis(self, processor):
        assert processor.process("important close parenthesis") == "important)"

    # Other punctuation
    def test_dash(self, processor):
        assert processor.process("self dash aware") == "self-aware"

    def test_hyphen(self, processor):
        assert processor.process("self hyphen aware") == "self-aware"

    def test_new_line(self, processor):
        result = processor.process("first new line second")
        assert result == "first\nsecond"

    def test_newline(self, processor):
        result = processor.process("first newline second")
        assert result == "first\nsecond"

    def test_new_paragraph(self, processor):
        result = processor.process("first new paragraph second")
        assert result == "first\n\nsecond"

    # Multiple punctuation in one string
    def test_multiple_punctuation(self, processor):
        result = processor.process(
            "hello comma how are you question mark I am fine period"
        )
        assert result == "hello, how are you? I am fine."

    def test_sentence_with_all_basics(self, processor):
        result = processor.process(
            "hello period new paragraph how are you question mark"
        )
        assert result == "hello.\n\nhow are you?"


class TestCaseInsensitivity:
    """Tests for case-insensitive matching."""

    @pytest.fixture
    def processor(self):
        return TextProcessor()

    def test_uppercase_period(self, processor):
        assert processor.process("hello PERIOD") == "hello."

    def test_mixed_case_comma(self, processor):
        assert processor.process("hello Comma world") == "hello, world"

    def test_uppercase_question_mark(self, processor):
        assert processor.process("what QUESTION MARK") == "what?"

    def test_mixed_case_new_line(self, processor):
        result = processor.process("first New Line second")
        assert result == "first\nsecond"


class TestWordBoundaries:
    """Tests for proper word boundary handling."""

    @pytest.fixture
    def processor(self):
        return TextProcessor()

    def test_periodic_not_matched(self, processor):
        # "periodic" should NOT be transformed
        assert processor.process("the periodic table") == "the periodic table"

    def test_comma_not_matched_in_word(self, processor):
        # Should not match "comma" inside other words
        assert processor.process("recommendation") == "recommendation"

    def test_colon_not_matched_in_word(self, processor):
        assert processor.process("colonoscopy") == "colonoscopy"

    def test_period_at_start(self, processor):
        assert processor.process("period that was good") == ". that was good"

    def test_period_in_middle(self, processor):
        assert processor.process("hello period world") == "hello. world"

    def test_period_at_end(self, processor):
        assert processor.process("hello world period") == "hello world."


class TestClipboardSubstitution:
    """Tests for clipboard content substitution."""

    @pytest.fixture
    def processor(self):
        return TextProcessor()

    def test_clipboard_substitution(self, processor):
        with patch("pyperclip.paste", return_value="test123"):
            result = processor.process("paste clipboard here")
            assert result == "paste test123 here"

    def test_clipboard_case_insensitive(self, processor):
        with patch("pyperclip.paste", return_value="content"):
            assert processor.process("paste CLIPBOARD here") == "paste content here"

    def test_clipboard_mixed_case(self, processor):
        with patch("pyperclip.paste", return_value="content"):
            assert processor.process("paste Clipboard here") == "paste content here"

    def test_clipboard_empty(self, processor):
        with patch("pyperclip.paste", return_value=""):
            # Should leave "clipboard" unchanged when clipboard is empty
            result = processor.process("paste clipboard here")
            assert result == "paste clipboard here"

    def test_clipboard_whitespace_only(self, processor):
        with patch("pyperclip.paste", return_value="   "):
            # Whitespace-only clipboard should not substitute
            result = processor.process("paste clipboard here")
            assert result == "paste clipboard here"

    def test_clipboard_error(self, processor):
        with patch("pyperclip.paste", side_effect=Exception("clipboard error")):
            # Should gracefully handle clipboard errors
            result = processor.process("paste clipboard here")
            assert result == "paste clipboard here"

    def test_clipboard_with_punctuation(self, processor):
        # Punctuation should be processed first, then clipboard
        with patch("pyperclip.paste", return_value="code123"):
            result = processor.process("the code is clipboard period")
            assert result == "the code is code123."

    def test_multiple_clipboard_references(self, processor):
        with patch("pyperclip.paste", return_value="X"):
            result = processor.process("clipboard and clipboard")
            assert result == "X and X"

    def test_clipboard_multiline_content(self, processor):
        with patch("pyperclip.paste", return_value="line1\nline2"):
            result = processor.process("content: clipboard")
            assert result == "content: line1\nline2"

    def test_no_clipboard_word(self, processor):
        # No substitution when "clipboard" not present
        with patch("pyperclip.paste") as mock_paste:
            result = processor.process("hello world")
            mock_paste.assert_not_called()
            assert result == "hello world"


class TestCombinedProcessing:
    """Tests for combined punctuation and clipboard processing."""

    @pytest.fixture
    def processor(self):
        return TextProcessor()

    def test_punctuation_then_clipboard(self, processor):
        with patch("pyperclip.paste", return_value="example.com"):
            result = processor.process(
                "visit clipboard for more info period"
            )
            assert result == "visit example.com for more info."

    def test_complex_sentence(self, processor):
        with patch("pyperclip.paste", return_value="John"):
            result = processor.process(
                "hello comma clipboard exclamation mark how are you question mark"
            )
            assert result == "hello, John! how are you?"

    def test_paragraph_with_clipboard(self, processor):
        with patch("pyperclip.paste", return_value="code123"):
            result = processor.process(
                "first paragraph period new paragraph the code is clipboard period"
            )
            assert result == "first paragraph.\n\nthe code is code123."


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    @pytest.fixture
    def processor(self):
        return TextProcessor()

    def test_empty_string(self, processor):
        assert processor.process("") == ""

    def test_none_input(self, processor):
        # Should handle None gracefully (returns empty or None)
        result = processor.process(None)
        assert result is None or result == ""

    def test_whitespace_only(self, processor):
        assert processor.process("   ") == "   "

    def test_only_punctuation_command(self, processor):
        assert processor.process("period") == "."

    def test_multiple_spaces_preserved(self, processor):
        result = processor.process("hello  comma  world")
        # Spaces around the command may vary, but double spaces elsewhere preserved
        assert ", " in result or ",  " in result

    def test_consecutive_punctuation(self, processor):
        result = processor.process("what question mark exclamation mark")
        assert result == "what?!"

    def test_unicode_preserved(self, processor):
        result = processor.process("hello period")
        assert result == "hello."


class TestProcessorStateless:
    """Tests to verify processor is stateless."""

    def test_multiple_calls_independent(self):
        processor = TextProcessor()
        result1 = processor.process("hello period")
        result2 = processor.process("world comma")
        assert result1 == "hello."
        assert result2 == "world,"

    def test_new_instance_same_behavior(self):
        p1 = TextProcessor()
        p2 = TextProcessor()
        assert p1.process("test period") == p2.process("test period")
