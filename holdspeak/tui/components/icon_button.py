"""Icon button component."""

from textual.message import Message
from textual.widgets import Static


class IconButton(Static):
    """Clickable icon used in the title bar."""

    class Pressed(Message):
        def __init__(self, icon_id: str) -> None:
            super().__init__()
            self.icon_id = icon_id

    def __init__(self, text: str, *, icon_id: str, tooltip: str = "") -> None:
        super().__init__(text)
        self._icon_id = icon_id
        self._tooltip = tooltip

    def on_click(self) -> None:
        self.post_message(self.Pressed(self._icon_id))
