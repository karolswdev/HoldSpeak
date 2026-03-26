"""Text post-processing for transcribed speech."""

import re

import pyperclip


class TextProcessor:
    """Process transcribed text to handle punctuation commands and substitutions."""

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
        # Process longer commands first to handle multi-word commands properly
        # e.g., "new paragraph" before "new"

        # ATTACH_LEFT: space before is removed
        for command in sorted(self.ATTACH_LEFT.keys(), key=len, reverse=True):
            punctuation = self.ATTACH_LEFT[command]
            # Match optional space before, the command, then word boundary
            pattern = rf"\s*\b{re.escape(command)}\b"
            text = re.sub(pattern, punctuation, text, flags=re.IGNORECASE)

        # ATTACH_RIGHT: space after is removed
        for command in sorted(self.ATTACH_RIGHT.keys(), key=len, reverse=True):
            punctuation = self.ATTACH_RIGHT[command]
            # Match word boundary, command, then optional space after
            pattern = rf"\b{re.escape(command)}\b\s*"
            text = re.sub(pattern, punctuation, text, flags=re.IGNORECASE)

        # ATTACH_BOTH: spaces on both sides removed
        for command in sorted(self.ATTACH_BOTH.keys(), key=len, reverse=True):
            punctuation = self.ATTACH_BOTH[command]
            # Match optional space, command, optional space
            pattern = rf"\s*\b{re.escape(command)}\b\s*"
            text = re.sub(pattern, punctuation, text, flags=re.IGNORECASE)

        # NEWLINES: remove surrounding spaces, add newline
        for command in sorted(self.NEWLINES.keys(), key=len, reverse=True):
            replacement = self.NEWLINES[command]
            # Match optional space, command, optional space
            pattern = rf"\s*\b{re.escape(command)}\b\s*"
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

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
