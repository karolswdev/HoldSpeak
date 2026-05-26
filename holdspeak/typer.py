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

    def type_text(
        self,
        text: str,
        *,
        target_profile: str | None = None,
        submit: bool = False,
    ) -> None:
        """Type/paste text into the active application.

        Args:
            text: The text to type
            target_profile: Optional delivery target hint. On Linux, terminal
                targets such as Claude Code and Codex usually paste with
                Ctrl+Shift+V instead of Ctrl+V.
            submit: If True, press Enter after inserting text.
        """
        if not text or not text.strip():
            return

        text = text.strip()

        if self.use_clipboard:
            self._paste_text(text, target_profile=target_profile)
        else:
            self._type_text_slowly(text)
        if submit:
            self._press_enter()

    def _paste_text(self, text: str, *, target_profile: str | None = None) -> None:
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

        # Simulate Cmd+V (macOS), Ctrl+V for generic Linux text fields, and
        # Ctrl+Shift+V for Linux terminal targets.
        modifiers = self._paste_modifiers(target_profile)
        for modifier in modifiers:
            self._keyboard.press(modifier)
        self._keyboard.press('v')
        self._keyboard.release('v')
        for modifier in reversed(modifiers):
            self._keyboard.release(modifier)

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

    def _press_enter(self) -> None:
        self._keyboard.press(Key.enter)
        self._keyboard.release(Key.enter)

    def _paste_modifiers(self, target_profile: str | None) -> tuple[object, ...]:
        if sys.platform == "darwin":
            return (Key.cmd,)
        if _is_terminal_target(target_profile):
            return (Key.ctrl, Key.shift)
        return (self._paste_modifier,)


def _is_terminal_target(target_profile: str | None) -> bool:
    return str(target_profile or "").strip().lower() in {
        "claude_code",
        "codex_cli",
        "terminal_shell",
    }


def type_with_applescript(text: str) -> None:
    """Alternative: use AppleScript for text injection (most reliable on macOS)."""
    if sys.platform != "darwin":
        raise RuntimeError("AppleScript text injection is only available on macOS")
    # Escape special characters for AppleScript
    escaped = text.replace('\\', '\\\\').replace('"', '\\"')
    script = f'tell application "System Events" to keystroke "{escaped}"'
    subprocess.run(['osascript', '-e', script], check=True)
