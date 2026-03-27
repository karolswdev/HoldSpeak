"""Meeting history screen."""

from ..services.meetings import list_saved_meetings
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Label, ListItem, ListView


class MeetingHistoryScreen(ModalScreen[None]):
    """Modal screen showing meeting history."""

    BINDINGS = [("escape", "cancel", "Close")]

    def action_cancel(self) -> None:
        self.app.pop_screen()

    def compose(self) -> ComposeResult:
        with Container(id="history_dialog"):
            yield Label("Meeting History", id="history_title")
            yield ListView(id="history_list")
            with Horizontal(id="history_actions"):
                yield Button("Close", id="history_close")
                yield Button("Refresh", variant="primary", id="history_refresh")

    def on_mount(self) -> None:
        self._load_meetings()

    def _load_meetings(self) -> None:
        """Load meetings via the TUI service layer."""
        try:
            meetings = list_saved_meetings(limit=50)
        except Exception:
            meetings = []

        list_view = self.query_one("#history_list", ListView)
        list_view.clear()

        if not meetings:
            list_view.mount(ListItem(Label("No meetings found. Start a meeting to see history.")))
        else:
            for m in meetings:
                # Format duration
                if m.duration_seconds:
                    mins = int(m.duration_seconds // 60)
                    secs = int(m.duration_seconds % 60)
                    duration = f"{mins:02d}:{secs:02d}"
                else:
                    duration = "--:--"

                title = m.title or "(untitled)"
                if len(title) > 25:
                    title = title[:22] + "..."

                date_str = m.started_at.strftime("%Y-%m-%d %H:%M")
                text = f"{date_str}  {duration}  {m.segment_count:>3} segs  {title}"
                list_view.mount(ListItem(Label(text, classes="history_line"), id=f"meeting_{m.id}"))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "history_close":
            self.app.pop_screen()
        elif event.button.id == "history_refresh":
            self._load_meetings()
            self.app.notify("History refreshed", timeout=1.0)
