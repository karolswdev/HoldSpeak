"""History widget component."""

from datetime import datetime
from typing import Optional

from textual.app import ComposeResult
from textual.containers import Container
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Label, ListItem, ListView, Static


class TranscriptionItem(ListItem):
    """A single transcription entry in the history list."""

    def __init__(self, timestamp: str, text: str) -> None:
        super().__init__(Label(f"{timestamp}  {text}", classes="history_line"))
        self.timestamp = timestamp
        self.text = text


class HistoryWidget(Container):
    """Scrollable list of transcriptions; click an item to copy."""

    is_empty: reactive[bool] = reactive(True)

    class Copied(Message):
        def __init__(self, text: str) -> None:
            super().__init__()
            self.text = text

    def compose(self) -> ComposeResult:
        default_text = self._build_empty_state_hint(
            global_hotkey_enabled=True,
            hotkey_display="⌥R",
            focused_hold_key="v",
        )
        with Container(id="history_container"):
            yield Static(
                default_text,
                id="empty_state",
            )
            yield ListView(id="history_list")

    def set_empty_state_hint(
        self,
        *,
        global_hotkey_enabled: bool,
        hotkey_display: str,
        focused_hold_key: str,
    ) -> None:
        """Update the empty-state hint text."""
        self._set_empty_state_hint(
            global_hotkey_enabled=global_hotkey_enabled,
            hotkey_display=hotkey_display,
            focused_hold_key=focused_hold_key,
        )

    def _set_empty_state_hint(
        self,
        *,
        global_hotkey_enabled: bool,
        hotkey_display: str,
        focused_hold_key: str,
    ) -> None:
        try:
            self.query_one("#empty_state", Static).update(
                self._build_empty_state_hint(
                    global_hotkey_enabled=global_hotkey_enabled,
                    hotkey_display=hotkey_display,
                    focused_hold_key=focused_hold_key,
                )
            )
        except Exception:
            pass

    @staticmethod
    def _build_empty_state_hint(*, global_hotkey_enabled: bool, hotkey_display: str, focused_hold_key: str) -> str:
        if global_hotkey_enabled:
            record_hint = f"Hold [bold]{hotkey_display}[/bold] to record, release to transcribe."
        else:
            record_hint = f"Hold [bold]{focused_hold_key}[/bold] to record (focused), release to transcribe."

        return (
            "[dim]"
            f"{record_hint}\n\n"
            "Press [bold]m[/bold] to start meeting mode.\n"
            "Press [bold]d[/bold] for diagnostics.\n"
            "Press [bold]s[/bold] for settings."
            "[/dim]"
        )

    def watch_is_empty(self, empty: bool) -> None:
        """Toggle visibility of empty state vs history list."""
        try:
            self.query_one("#empty_state").display = empty
            self.query_one("#history_list").display = not empty
        except Exception:
            pass  # Widget not mounted yet

    def add_transcription(self, text: str, *, timestamp: Optional[str] = None) -> None:
        timestamp = timestamp or datetime.now().strftime("%H:%M")
        list_view = self.query_one("#history_list", ListView)
        item = TranscriptionItem(timestamp, text)
        list_view.mount(item, before=0)
        list_view.index = 0
        self.is_empty = False

    def get_last(self) -> Optional[str]:
        list_view = self.query_one("#history_list", ListView)
        if not list_view.children:
            return None
        item = next(iter(list_view.children), None)
        return item.text if isinstance(item, TranscriptionItem) else None

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Highlight selected item (don't copy yet - wait for Enter/Space)."""
        # Selection is visual only - prevents accidental copies during navigation
        pass

    def on_key(self, event) -> None:
        """Copy on Enter/Space (explicit activation)."""
        if event.key in ("enter", "space"):
            list_view = self.query_one("#history_list", ListView)
            selected = list_view.highlighted_child
            if isinstance(selected, TranscriptionItem):
                self.post_message(self.Copied(selected.text))
                event.prevent_default()
                event.stop()

    def on_click(self, event) -> None:
        """Copy on mouse click (explicit intent)."""
        list_view = self.query_one("#history_list", ListView)
        selected = list_view.highlighted_child
        if isinstance(selected, TranscriptionItem):
            self.post_message(self.Copied(selected.text))
