"""Mock text typer for testing."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class MockTextTyper:
    """Mock TextTyper for testing without system keyboard/clipboard.

    Usage:
        typer = MockTextTyper()
        typer.type_text("Hello world")
        assert typer.typed_texts == ["Hello world"]
        assert typer.type_count == 1
    """

    should_fail: bool = False
    fail_message: str = "Mock typing error"

    # Capture what was typed
    typed_texts: list[str] = field(default_factory=list)
    type_count: int = field(default=0, init=False)
    last_text: Optional[str] = field(default=None, init=False)

    def type_text(self, text: str) -> None:
        """Mock type_text - captures text instead of typing it."""
        if self.should_fail:
            raise RuntimeError(self.fail_message)

        self.typed_texts.append(text)
        self.last_text = text
        self.type_count += 1

    def clear(self) -> None:
        """Reset captured texts."""
        self.typed_texts.clear()
        self.type_count = 0
        self.last_text = None

    def reset(self) -> None:
        """Alias for clear()."""
        self.clear()

    @property
    def all_typed_text(self) -> str:
        """Get all typed text concatenated."""
        return "".join(self.typed_texts)


@dataclass
class MockClipboard:
    """Mock clipboard for testing pyperclip operations.

    Usage:
        clipboard = MockClipboard(initial_content="original")
        clipboard.copy("new content")
        assert clipboard.paste() == "new content"
        assert clipboard.copy_count == 1
    """

    initial_content: str = ""

    _content: str = field(default="", init=False)
    copy_count: int = field(default=0, init=False)
    paste_count: int = field(default=0, init=False)
    copy_history: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._content = self.initial_content

    def copy(self, text: str) -> None:
        """Copy text to mock clipboard."""
        self._content = text
        self.copy_count += 1
        self.copy_history.append(text)

    def paste(self) -> str:
        """Paste from mock clipboard."""
        self.paste_count += 1
        return self._content

    @property
    def content(self) -> str:
        """Current clipboard content."""
        return self._content

    def reset(self) -> None:
        """Reset clipboard to initial state."""
        self._content = self.initial_content
        self.copy_count = 0
        self.paste_count = 0
        self.copy_history.clear()
