"""Tab bar component for main navigation."""

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Label, Static

from .icon_button import IconButton


class TabBarWidget(Horizontal):
    """Horizontal tab bar for switching between Voice Typing and Meetings."""

    class TabChanged(Message):
        """Posted when active tab changes."""

        def __init__(self, tab_id: str) -> None:
            super().__init__()
            self.tab_id = tab_id

    active_tab: reactive[str] = reactive("voice_typing")

    TABS = [
        ("voice_typing", "VOICE", "1"),
        ("meetings", "MEETINGS", "2"),
    ]

    def compose(self) -> ComposeResult:
        yield Label("HOLDSPEAK", id="hud_title")
        yield Static("", id="hud_spacer_left")

        for tab_id, label, key in self.TABS:
            yield Static(f"[{key}] {label}", id=f"tab_{tab_id}", classes="tab_item")

        yield Static("", id="hud_spacer_right")
        yield IconButton("SET", icon_id="settings")
        yield IconButton("?", icon_id="help")

    def on_mount(self) -> None:
        self._update_tab_styles()

    def watch_active_tab(self, tab_id: str) -> None:
        self._update_tab_styles()
        self.post_message(self.TabChanged(tab_id))

    def _update_tab_styles(self) -> None:
        for tab_id, _, _ in self.TABS:
            widget = self.query_one(f"#tab_{tab_id}", Static)
            if tab_id == self.active_tab:
                widget.add_class("active")
            else:
                widget.remove_class("active")

    def on_click(self, event) -> None:
        """Handle tab clicks."""
        # NOTE: `event.x/y` are widget-relative; `region` is screen-relative.
        # Use `screen_x/screen_y` so hit-testing works correctly.
        for tab_id, _, _ in self.TABS:
            widget = self.query_one(f"#tab_{tab_id}", Static)
            if widget.region.contains(event.screen_x, event.screen_y):
                self.active_tab = tab_id
                break

    def switch_to(self, tab_id: str) -> None:
        """Programmatically switch tabs."""
        if tab_id in [t[0] for t in self.TABS]:
            self.active_tab = tab_id
