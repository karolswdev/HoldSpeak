"""Raw desktop input driver.

This module is imported only inside the privileged desktop-effect child after
the server has validated a broker warrant. Ordinary runtime code must use the
warrant-only proxy in :mod:`holdspeak.typer`.
"""
from __future__ import annotations

import sys
import time
from typing import Optional

import pyperclip

try:
    from pynput.keyboard import Controller, Key  # type: ignore
except Exception as exc:  # pragma: no cover - platform dependency
    Controller = None  # type: ignore[assignment]
    Key = None  # type: ignore[assignment]
    _IMPORT_ERROR: Optional[BaseException] = exc
else:  # pragma: no cover - platform dependency
    _IMPORT_ERROR = None


class RawDesktopDriver:
    """The executor process's sole raw keyboard/clipboard capability."""

    def __init__(self, use_clipboard: bool = True) -> None:
        if Controller is None or Key is None:
            raise RuntimeError("desktop input backend unavailable") from _IMPORT_ERROR
        self.use_clipboard = bool(use_clipboard)
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
        if not text or not text.strip():
            return
        clean = text.strip()
        if self.use_clipboard:
            self._paste_text(clean, target_profile=target_profile)
        else:
            self._type_text_slowly(clean)
        if submit:
            self._press_enter()

    def _paste_text(self, text: str, *, target_profile: str | None = None) -> None:
        try:
            self._original_clipboard = pyperclip.paste()
        except Exception:
            self._original_clipboard = None
        pyperclip.copy(text)
        time.sleep(0.05)
        modifiers = self._paste_modifiers(target_profile)
        for modifier in modifiers:
            self._keyboard.press(modifier)
        self._keyboard.press("v")
        self._keyboard.release("v")
        for modifier in reversed(modifiers):
            self._keyboard.release(modifier)
        if self._original_clipboard is not None:
            time.sleep(0.1)
            try:
                pyperclip.copy(self._original_clipboard)
            except Exception:
                pass

    def _type_text_slowly(self, text: str) -> None:
        for char in text:
            self._keyboard.type(char)
            time.sleep(0.01)

    def _press_enter(self) -> None:
        self._keyboard.press(Key.enter)
        self._keyboard.release(Key.enter)

    def _paste_modifiers(self, target_profile: str | None) -> tuple[object, ...]:
        if sys.platform == "darwin":
            return (Key.cmd,)
        if is_terminal_target(target_profile):
            return (Key.ctrl, Key.shift)
        return (self._paste_modifier,)


def is_terminal_target(target_profile: str | None) -> bool:
    return str(target_profile or "").strip().lower() in {
        "claude_code",
        "codex_cli",
        "terminal_shell",
    }


__all__ = ["RawDesktopDriver", "is_terminal_target"]
