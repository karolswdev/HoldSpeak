"""Voice typing pane - the original main content (HUD chrome lives above)."""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal

from .audio_meter import AudioMeterWidget
from .footer import HotkeyHintWidget
from .history import HistoryWidget
from .status import StatusWidget


class VoiceTypingPane(Container):
    """Contains the voice typing interface (status bar, history)."""

    def __init__(self, hotkey_display: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self._hotkey_display = hotkey_display

    def compose(self) -> ComposeResult:
        with Horizontal(id="statusbar"):
            yield StatusWidget(id="status")
            yield AudioMeterWidget(id="meter")
            yield HotkeyHintWidget(self._hotkey_display, id="hotkey_hint")

        yield HistoryWidget(id="history")
