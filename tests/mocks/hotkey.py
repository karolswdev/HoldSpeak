"""Mock hotkey components for testing."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional, Any


@dataclass
class FakeKey:
    """Fake pynput Key object for testing.

    Usage:
        key = FakeKey("alt_r")
        assert key.name == "alt_r"
    """

    name: str

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, FakeKey):
            return self.name == other.name
        if hasattr(other, "name"):
            return self.name == other.name
        return False

    def __hash__(self) -> int:
        return hash(self.name)

    def __repr__(self) -> str:
        return f"FakeKey({self.name!r})"


# Pre-defined fake keys matching pynput.keyboard.Key
class FakeKeys:
    """Collection of fake keys for testing."""

    alt_r = FakeKey("alt_r")
    alt_l = FakeKey("alt_l")
    ctrl_r = FakeKey("ctrl_r")
    ctrl_l = FakeKey("ctrl_l")
    shift_r = FakeKey("shift_r")
    shift_l = FakeKey("shift_l")
    cmd = FakeKey("cmd")
    cmd_r = FakeKey("cmd_r")
    caps_lock = FakeKey("caps_lock")
    f1 = FakeKey("f1")
    f2 = FakeKey("f2")
    f3 = FakeKey("f3")
    f4 = FakeKey("f4")
    f5 = FakeKey("f5")
    f6 = FakeKey("f6")
    f7 = FakeKey("f7")
    f8 = FakeKey("f8")
    f9 = FakeKey("f9")
    f10 = FakeKey("f10")
    f11 = FakeKey("f11")
    f12 = FakeKey("f12")


@dataclass
class MockHotkeyListener:
    """Mock HotkeyListener for testing without pynput.

    Usage:
        listener = MockHotkeyListener(
            on_press=my_press_handler,
            on_release=my_release_handler,
        )
        listener.start()
        listener.simulate_press()  # Triggers on_press
        listener.simulate_release()  # Triggers on_release
    """

    on_press: Optional[Callable[[], None]] = None
    on_release: Optional[Callable[[], None]] = None

    _running: bool = field(default=False, init=False)
    _current_key: str = field(default="alt_r", init=False)
    _pressed: bool = field(default=False, init=False)

    # Call tracking
    start_count: int = field(default=0, init=False)
    stop_count: int = field(default=0, init=False)
    press_count: int = field(default=0, init=False)
    release_count: int = field(default=0, init=False)

    def start(self) -> None:
        """Start the mock listener."""
        self._running = True
        self.start_count += 1

    def stop(self) -> None:
        """Stop the mock listener."""
        self._running = False
        self.stop_count += 1

    def set_key(self, key_name: str) -> None:
        """Change the hotkey being listened for."""
        self._current_key = key_name

    def simulate_press(self) -> None:
        """Simulate hotkey press for testing."""
        if not self._pressed:
            self._pressed = True
            self.press_count += 1
            if self.on_press:
                self.on_press()

    def simulate_release(self) -> None:
        """Simulate hotkey release for testing."""
        if self._pressed:
            self._pressed = False
            self.release_count += 1
            if self.on_release:
                self.on_release()

    def simulate_press_release(self) -> None:
        """Simulate a complete press-release cycle."""
        self.simulate_press()
        self.simulate_release()

    @property
    def is_pressed(self) -> bool:
        """Check if hotkey is currently pressed."""
        return self._pressed

    @property
    def is_running(self) -> bool:
        """Check if listener is running."""
        return self._running

    def reset(self) -> None:
        """Reset all counters and state."""
        self.start_count = 0
        self.stop_count = 0
        self.press_count = 0
        self.release_count = 0
        self._pressed = False
        self._running = False
