"""Meeting transcript screen."""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Label, ListItem, ListView

from ...meeting_session import Bookmark, TranscriptSegment


class MeetingTranscriptScreen(ModalScreen[None]):
    """Modal screen showing meeting transcript with bookmarks."""

    BINDINGS = [("escape", "cancel", "Close")]

    def __init__(
        self,
        segments: list[TranscriptSegment],
        bookmarks: list[Bookmark] = None,
    ) -> None:
        super().__init__()
        self._segments = segments
        self._bookmarks = bookmarks or []

    def action_cancel(self) -> None:
        self.app.pop_screen()

    def _format_time(self, seconds: float) -> str:
        """Format seconds as HH:MM:SS."""
        import time
        return time.strftime("%H:%M:%SS", time.gmtime(seconds))

    def compose(self) -> ComposeResult:
        with Container(id="transcript_dialog"):
            yield Label("Meeting Transcript", id="transcript_title")
            yield ListView(id="transcript_list")
            with Horizontal(id="transcript_actions"):
                yield Button("Close", id="transcript_close")
                yield Button("Copy All", variant="primary", id="transcript_copy")

    def on_mount(self) -> None:
        list_view = self.query_one("#transcript_list", ListView)

        if not self._segments and not self._bookmarks:
            list_view.mount(ListItem(Label("No transcript yet...")))
            return

        # Merge segments and bookmarks, sort by timestamp
        entries = []
        for seg in self._segments:
            entries.append(("segment", seg.start_time, seg))
        for bm in self._bookmarks:
            entries.append(("bookmark", bm.timestamp, bm))
        entries.sort(key=lambda x: x[1])

        for kind, ts, item in entries:
            if kind == "bookmark":
                label_text = item.label or "Bookmark"
                text = f"[bold yellow]🔖 {label_text}[/] [dim]@ {self._format_time(ts)}[/dim]"
                list_view.mount(ListItem(Label(text, classes="bookmark_marker", markup=True)))
            else:
                text = f"[{item.format_timestamp()}] {item.speaker}: {item.text}"
                list_view.mount(ListItem(Label(text, classes="transcript_line")))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "transcript_close":
            self.app.pop_screen()
        elif event.button.id == "transcript_copy":
            if self._segments:
                text = "\n".join(str(s) for s in self._segments)
                # Use app's unified clipboard method
                self.app.copy_to_clipboard(text)
                self.app.notify("Transcript copied!", timeout=1.5)
            self.app.pop_screen()
