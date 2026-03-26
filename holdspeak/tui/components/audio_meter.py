"""Audio meter widget component."""

from rich.text import Text
from textual.reactive import reactive
from textual.widget import Widget

from ..utils import clamp01


class AudioMeterWidget(Widget):
    """Horizontal audio level meter (0-100)."""

    level: reactive[float] = reactive(0.0)

    def watch_level(self, level: float) -> None:
        self.refresh()

    def set_level(self, level: float) -> None:
        self.level = clamp01(level)

    def render(self) -> Text:
        width = max(10, self.size.width)
        bar_width = max(10, width)
        filled = int(bar_width * clamp01(self.level))
        empty = bar_width - filled

        text = Text()
        if filled:
            text.append("█" * filled, style="bold #22d3ee")
        if empty:
            text.append("░" * empty, style="#1f2937")
        return text
