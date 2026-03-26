"""Header components."""

from rich.text import Text
from textual.widgets import Static


class HeaderRule(Static):
    """A simple horizontal rule that uses box-drawing characters."""

    def render(self) -> Text:
        width = max(0, self.size.width)
        return Text("━" * width, style="dim")
