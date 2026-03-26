"""Text injection module - types text into active application."""

from __future__ import annotations

import subprocess
import sys
import time
from typing import Optional

import pyperclip

try:
    from pynput.keyboard import Controller, Key  # type: ignore
except Exception as exc:  # pragma: no cover
    Controller = None  # type: ignore[assignment]
    Key = None  # type: ignore[assignment]
    _IMPORT_ERROR: Optional[BaseException] = exc
else:  # pragma: no cover
    _IMPORT_ERROR = None


class TextTyper:
    """Injects transcribed text into the active application.

    Uses clipboard + Cmd+V for reliable text injection on macOS.
    """

    def __init__(self, use_clipboard: bool = True):
        """Initialize the text typer.

        Args:
            use_clipboard: If True, use clipboard paste (faster, more reliable).
                          If False, simulate individual keystrokes.
        """
        if Controller is None or Key is None:
            raise RuntimeError(
                "Text injection is unavailable because `pynput` could not be initialized. "
                "On Linux this usually means there's no X server (missing `DISPLAY`) or "
                "you're on Wayland without a supported backend."
            ) from _IMPORT_ERROR

        self.use_clipboard = use_clipboard
        self._keyboard = Controller()
        self._original_clipboard: str | None = None
        self._paste_modifier = Key.cmd if sys.platform == "darwin" else Key.ctrl

    def type_text(self, text: str) -> None:
        """Type/paste text into the active application.

        Args:
            text: The text to type
        """
        if not text or not text.strip():
            return

        text = text.strip()

        if self.use_clipboard:
            self._paste_text(text)
        else:
            self._type_text_slowly(text)

    def _paste_text(self, text: str) -> None:
        """Paste text using clipboard + platform shortcut."""
        # Save original clipboard
        try:
            self._original_clipboard = pyperclip.paste()
        except Exception:
            self._original_clipboard = None

        # Set new clipboard content
        pyperclip.copy(text)

        # Small delay to ensure clipboard is set
        time.sleep(0.05)

        # Simulate Cmd+V (macOS) / Ctrl+V (Linux)
        self._keyboard.press(self._paste_modifier)
        self._keyboard.press('v')
        self._keyboard.release('v')
        self._keyboard.release(self._paste_modifier)

        # Restore original clipboard after a delay
        if self._original_clipboard is not None:
            time.sleep(0.1)
            try:
                pyperclip.copy(self._original_clipboard)
            except Exception:
                pass

    def _type_text_slowly(self, text: str) -> None:
        """Type text character by character (slower but doesn't touch clipboard)."""
        for char in text:
            self._keyboard.type(char)
            time.sleep(0.01)  # Small delay between characters


def type_with_applescript(text: str) -> None:
    """Alternative: use AppleScript for text injection (most reliable on macOS)."""
    if sys.platform != "darwin":
        raise RuntimeError("AppleScript text injection is only available on macOS")
    # Escape special characters for AppleScript
    escaped = text.replace('\\', '\\\\').replace('"', '\\"')
    script = f'tell application "System Events" to keystroke "{escaped}"'
    subprocess.run(['osascript', '-e', script], check=True)
