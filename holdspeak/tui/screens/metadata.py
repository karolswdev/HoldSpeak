"""Meeting metadata screen."""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label


class MeetingMetadataScreen(ModalScreen[None]):
    """Modal screen for editing meeting title and tags."""

    BINDINGS = [("escape", "cancel", "Close")]

    class Saved(Message):
        """Posted when metadata is saved."""
        def __init__(self, title: str, tags: list[str]) -> None:
            super().__init__()
            self.title = title
            self.tags = tags

    def __init__(self, current_title: str = "", current_tags: list[str] = None) -> None:
        super().__init__()
        self._title = current_title or ""
        self._tags = current_tags or []

    def action_cancel(self) -> None:
        self.app.pop_screen()

    def compose(self) -> ComposeResult:
        with Container(id="metadata_dialog"):
            yield Label("Meeting Details", id="metadata_title")
            yield Label("Title", classes="field_label")
            yield Input(value=self._title, id="title_input", placeholder="Enter meeting title...")
            yield Label("Tags (comma-separated)", classes="field_label")
            yield Input(value=", ".join(self._tags), id="tags_input", placeholder="tag1, tag2, ...")
            with Horizontal(id="metadata_actions"):
                yield Button("Cancel", id="metadata_cancel")
                yield Button("Save", variant="primary", id="metadata_save")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "metadata_cancel":
            self.app.pop_screen()
        elif event.button.id == "metadata_save":
            title = self.query_one("#title_input", Input).value.strip()
            tags_str = self.query_one("#tags_input", Input).value
            # Parse comma-separated tags
            tags = [t.strip().lower() for t in tags_str.split(",") if t.strip()]
            self.post_message(self.Saved(title, tags))
            self.app.pop_screen()
