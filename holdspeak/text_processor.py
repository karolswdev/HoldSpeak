"""Text post-processing for transcribed speech."""

import re
from typing import Optional, Sequence

import pyperclip


class TextProcessor:
    """Process transcribed text to handle punctuation commands and substitutions.

    HS-59-02: takes the user's spoken-symbol dictionary and merges it over
    the built-in tables. A user entry with the same spoken phrase as a
    built-in replaces it (the phrase is removed from every built-in table
    first, then inserted into its own attach mode's table), so the user
    always wins. With no entries the instance tables equal the class tables
    and the output is byte-identical.
    """

    # Punctuation that removes space before it (attaches to previous word)
    # e.g., "hello period" -> "hello."
    ATTACH_LEFT: dict[str, str] = {
        "period": ".",
        "full stop": ".",
        "comma": ",",
        "question mark": "?",
        "exclamation mark": "!",
        "exclamation point": "!",
        "colon": ":",
        "semicolon": ";",
        "close quote": '"',
        "end quote": '"',
        "unquote": '"',
        "close paren": ")",
        "close parenthesis": ")",
    }

    # Punctuation that removes space after it (attaches to next word)
    # e.g., "open quote hello" -> '"hello'
    ATTACH_RIGHT: dict[str, str] = {
        "open quote": '"',
        "open paren": "(",
        "open parenthesis": "(",
    }

    # Punctuation that removes space on both sides
    # e.g., "self dash aware" -> "self-aware"
    ATTACH_BOTH: dict[str, str] = {
        "dash": "-",
        "hyphen": "-",
    }

    # Special replacements that handle their own spacing
    NEWLINES: dict[str, str] = {
        "new line": "\n",
        "newline": "\n",
        "new paragraph": "\n\n",
    }

    def __init__(self, spoken_symbols: Optional[Sequence[dict]] = None) -> None:
        # Instance copies; the class attributes remain the pristine built-ins.
        self._attach_left = dict(self.ATTACH_LEFT)
        self._attach_right = dict(self.ATTACH_RIGHT)
        self._attach_both = dict(self.ATTACH_BOTH)
        self._newlines = dict(self.NEWLINES)
        self._plain: dict[str, str] = {}

        for entry in spoken_symbols or []:
            spoken = str(entry.get("spoken", "")).strip().lower()
            symbol = str(entry.get("symbol", ""))
            attach = str(entry.get("attach", "none") or "none").lower()
            if not spoken or not symbol:
                continue
            # User wins: drop the phrase from every table before inserting.
            for table in (
                self._attach_left,
                self._attach_right,
                self._attach_both,
                self._newlines,
                self._plain,
            ):
                table.pop(spoken, None)
            target = {
                "left": self._attach_left,
                "right": self._attach_right,
                "both": self._attach_both,
            }.get(attach, self._plain)
            target[spoken] = symbol

    def process(self, text: str) -> str:
        """Apply all text transformations.

        Args:
            text: Raw transcribed text.

        Returns:
            Processed text with punctuation commands and clipboard substituted.
        """
        if not text:
            return text

        text = self._process_punctuation(text)
        text = self._process_clipboard(text)
        return text

    def _process_punctuation(self, text: str) -> str:
        """Convert punctuation commands to actual punctuation.

        Handles word boundaries to avoid matching partial words
        (e.g., "period" but not "periodic").

        Properly handles spacing:
        - ATTACH_LEFT: removes space before (e.g., "hello period" -> "hello.")
        - ATTACH_RIGHT: removes space after (e.g., "open quote hello" -> '"hello')
        - ATTACH_BOTH: removes spaces both sides (e.g., "self dash aware" -> "self-aware")
        - NEWLINES: removes surrounding spaces
        """
        # One combined pass, longest command first ACROSS every table
        # (HS-59-02): per-table ordering let a short built-in ("colon") eat
        # the inside of a longer user phrase ("double colon") that lives in
        # a different table. The built-ins never overlapped across tables,
        # so their behavior is unchanged (locked by the golden set).
        entries: list[tuple[str, str, str]] = []
        entries.extend((c, r, "plain") for c, r in self._plain.items())
        entries.extend((c, r, "left") for c, r in self._attach_left.items())
        entries.extend((c, r, "right") for c, r in self._attach_right.items())
        entries.extend((c, r, "both") for c, r in self._attach_both.items())
        entries.extend((c, r, "newline") for c, r in self._newlines.items())

        for command, replacement, mode in sorted(
            entries, key=lambda e: len(e[0]), reverse=True
        ):
            escaped = re.escape(command)
            if mode == "plain":
                # Spacing preserved; the replacement is literal text, never
                # a regex template (backslashes / \g<> must not be special).
                pattern = rf"\b{escaped}\b"
            elif mode == "left":
                # Optional space before is removed (attach to previous word).
                pattern = rf"\s*\b{escaped}\b"
            elif mode == "right":
                # Optional space after is removed (attach to next word).
                pattern = rf"\b{escaped}\b\s*"
            else:  # both / newline: surrounding spaces removed
                pattern = rf"\s*\b{escaped}\b\s*"
            text = re.sub(
                pattern, lambda _m, s=replacement: s, text, flags=re.IGNORECASE
            )

        return text

    def _process_clipboard(self, text: str) -> str:
        """Replace 'clipboard' with actual clipboard contents.

        Only substitutes if clipboard contains text. Leaves 'clipboard'
        unchanged if clipboard is empty or contains non-text data.
        """
        # Check if "clipboard" appears in text (case-insensitive)
        if not re.search(r"\bclipboard\b", text, flags=re.IGNORECASE):
            return text

        try:
            clipboard_content = pyperclip.paste()
            # Only substitute if clipboard has actual text content
            if clipboard_content and clipboard_content.strip():
                pattern = r"\bclipboard\b"
                text = re.sub(
                    pattern, clipboard_content, text, flags=re.IGNORECASE
                )
        except Exception:
            # If clipboard access fails, leave text unchanged
            pass

        return text
