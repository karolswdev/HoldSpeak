"""Action items screen."""

from ..services.action_items import list_action_items, update_action_item_status
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Label, ListItem, ListView


class ActionItemsScreen(ModalScreen[None]):
    """Modal screen showing action items across meetings."""

    BINDINGS = [("escape", "cancel", "Close")]

    def __init__(self, include_completed: bool = False) -> None:
        super().__init__()
        self._include_completed = include_completed

    def action_cancel(self) -> None:
        self.app.pop_screen()

    def compose(self) -> ComposeResult:
        with Container(id="actions_dialog"):
            yield Label("Action Items", id="actions_title")
            yield ListView(id="actions_list")
            with Horizontal(id="actions_actions"):
                yield Button("Close", id="actions_close")
                yield Button("Toggle Completed", id="actions_toggle")
                yield Button("Refresh", variant="primary", id="actions_refresh")

    def on_mount(self) -> None:
        self._load_action_items()

    def _load_action_items(self) -> None:
        """Load action items via the TUI service layer."""
        try:
            items = list_action_items(include_completed=self._include_completed)
        except Exception:
            items = []

        list_view = self.query_one("#actions_list", ListView)
        list_view.clear()

        if not items:
            msg = "No action items found." if self._include_completed else "No pending action items."
            list_view.mount(ListItem(Label(msg)))
        else:
            for item in items:
                # Status icon
                status_icon = {
                    "done": "[x]",
                    "dismissed": "[-]",
                    "pending": "[ ]",
                }.get(item.status, "[ ]")

                owner = item.owner or "-"
                if len(owner) > 10:
                    owner = owner[:8] + ".."

                task = item.task
                if len(task) > 40:
                    task = task[:37] + "..."

                date_str = item.meeting_date.strftime("%m/%d")
                text = f"{status_icon} {date_str} {owner:<10} {task}"
                list_view.mount(ListItem(Label(text, classes="action_line"), id=f"action_{item.id}"))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "actions_close":
            self.app.pop_screen()
        elif event.button.id == "actions_toggle":
            self._include_completed = not self._include_completed
            self._load_action_items()
            status = "showing all" if self._include_completed else "pending only"
            self.app.notify(f"Filter: {status}", timeout=1.0)
        elif event.button.id == "actions_refresh":
            self._load_action_items()
            self.app.notify("Action items refreshed", timeout=1.0)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Highlight selected item (don't toggle yet - wait for Enter/Space)."""
        # Selection is visual only - prevents accidental toggles during navigation
        pass

    def on_key(self, event) -> None:
        """Toggle action item on Enter/Space (explicit activation)."""
        if event.key in ("enter", "space"):
            list_view = self.query_one("#actions_list", ListView)
            item_widget = list_view.highlighted_child
            if item_widget and item_widget.id and item_widget.id.startswith("action_"):
                item_id = item_widget.id[7:]  # Remove "action_" prefix
                self._toggle_action_item(item_id)
                event.prevent_default()
                event.stop()

    def _toggle_action_item(self, item_id: str) -> None:
        """Toggle action item between pending and done."""
        try:
            # Find current status
            items = list_action_items(include_completed=True)
            current_item = None
            for item in items:
                if item.id == item_id:
                    current_item = item
                    break

            if current_item:
                new_status = "pending" if current_item.status == "done" else "done"
                update_action_item_status(item_id, new_status)
                self._load_action_items()
                self.app.notify(f"Marked as {new_status}", timeout=1.0)
        except Exception as e:
            self.app.notify(f"Error: {e}", severity="error", timeout=2.0)
