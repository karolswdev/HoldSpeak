"""Hotkey listener - detects hold/release of trigger key."""

from __future__ import annotations

import threading
from typing import Callable, Optional, Union

try:
    from pynput import keyboard
except Exception as exc:  # pragma: no cover
    keyboard = None  # type: ignore[assignment]
    _IMPORT_ERROR: Optional[BaseException] = exc
else:  # pragma: no cover
    _IMPORT_ERROR = None


def _require_keyboard():
    if keyboard is None:
        raise RuntimeError(
            "pynput is not available. On Linux, pynput requires an active GUI session."
        ) from _IMPORT_ERROR
    return keyboard


def _key_name_map():
    kb = _require_keyboard()
    return {
        "alt_r": kb.Key.alt_r,
        "alt_l": kb.Key.alt_l,
        "ctrl_r": kb.Key.ctrl_r,
        "ctrl_l": kb.Key.ctrl_l,
        "cmd_r": kb.Key.cmd_r,
        "cmd_l": kb.Key.cmd_l,
        "shift_r": kb.Key.shift_r,
        "shift_l": kb.Key.shift_l,
        "caps_lock": kb.Key.caps_lock,
        "f1": kb.Key.f1,
        "f2": kb.Key.f2,
        "f3": kb.Key.f3,
        "f4": kb.Key.f4,
        "f5": kb.Key.f5,
        "f6": kb.Key.f6,
        "f7": kb.Key.f7,
        "f8": kb.Key.f8,
        "f9": kb.Key.f9,
        "f10": kb.Key.f10,
        "f11": kb.Key.f11,
        "f12": kb.Key.f12,
    }


def key_from_name(name: str) -> keyboard.Key:
    """Convert a key name string to a pynput Key object."""
    key = _key_name_map().get(name.lower())
    if key is None:
        raise ValueError(f"Unknown key name: {name}. Available: {list(_key_name_map().keys())}")
    return key


class HotkeyListener:
    """Listens for a hotkey press/release to trigger recording.

    Default hotkey is Right Option (Alt_R) - easy to hold with thumb.
    Supports runtime hotkey changes.
    """

    def __init__(
        self,
        on_press: Optional[Callable[[], None]] = None,
        on_release: Optional[Callable[[], None]] = None,
        hotkey: Union[keyboard.Key, str] = "alt_r",
    ):
        """Initialize the hotkey listener.

        Args:
            on_press: Callback when hotkey is pressed
            on_release: Callback when hotkey is released
            hotkey: The key to listen for - can be pynput Key or string name
        """
        self.on_press_callback = on_press
        self.on_release_callback = on_release

        # Convert string to Key if needed
        if isinstance(hotkey, str):
            self._hotkey = key_from_name(hotkey)
        else:
            self._hotkey = hotkey

        self._is_pressed = False
        self._listener: Optional[keyboard.Listener] = None
        self._lock = threading.Lock()

    @property
    def hotkey(self) -> keyboard.Key:
        """Get the current hotkey."""
        with self._lock:
            return self._hotkey

    @hotkey.setter
    def hotkey(self, value: Union[keyboard.Key, str]) -> None:
        """Set a new hotkey (can be changed at runtime)."""
        with self._lock:
            if isinstance(value, str):
                self._hotkey = key_from_name(value)
            else:
                self._hotkey = value
            # Reset pressed state when changing hotkey
            self._is_pressed = False

    def _handle_press(self, key: keyboard.Key) -> None:
        """Handle key press events."""
        with self._lock:
            if key == self._hotkey and not self._is_pressed:
                self._is_pressed = True
                callback = self.on_press_callback

            else:
                callback = None

        # Call outside lock to avoid deadlocks
        if callback:
            callback()

    def _handle_release(self, key: keyboard.Key) -> None:
        """Handle key release events."""
        with self._lock:
            if key == self._hotkey and self._is_pressed:
                self._is_pressed = False
                callback = self.on_release_callback
            else:
                callback = None

        # Call outside lock to avoid deadlocks
        if callback:
            callback()

    def start(self) -> None:
        """Start listening for the hotkey."""
        if self._listener is not None:
            return

        kb = _require_keyboard()
        self._listener = kb.Listener(
            on_press=self._handle_press,
            on_release=self._handle_release,
        )
        self._listener.start()

    def stop(self) -> None:
        """Stop listening for the hotkey."""
        if self._listener is not None:
            self._listener.stop()
            self._listener = None

    def wait(self) -> None:
        """Block until the listener is stopped."""
        if self._listener is not None:
            self._listener.join()

    @property
    def is_pressed(self) -> bool:
        """Check if the hotkey is currently pressed."""
        with self._lock:
            return self._is_pressed
