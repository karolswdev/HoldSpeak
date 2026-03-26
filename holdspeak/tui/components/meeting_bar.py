"""Meeting bar widget component."""

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widgets import Label, Static

from ..utils import clamp01


class MeetingBarWidget(Horizontal):
    """Shows meeting status when active - persistent bar at top."""

    active: reactive[bool] = reactive(False)
    _blink_on: reactive[bool] = reactive(True)
    duration: reactive[str] = reactive("00:00")
    segment_count: reactive[int] = reactive(0)
    has_system_audio: reactive[bool] = reactive(False)
    web_url: reactive[str] = reactive("")
    mic_level: reactive[float] = reactive(0.0)
    system_level: reactive[float] = reactive(0.0)
    title: reactive[str] = reactive("")

    def compose(self) -> ComposeResult:
        yield Static("⏺", id="meeting_indicator")
        yield Label("REC", id="meeting_label")
        yield Label("", id="meeting_title_display")
        yield Label("00:00", id="meeting_duration")
        yield Label("", id="meeting_levels")  # Mic/System level indicators
        yield Static("", id="meeting_spacer")
        yield Label("", id="meeting_info")
        yield Label("", id="meeting_url")

    def on_mount(self) -> None:
        self._update_display()
        self.set_interval(0.5, self._tick)

    def watch_active(self, active: bool) -> None:
        self._update_display()
        self._update_indicator()

    def watch__blink_on(self, _value: bool) -> None:
        self._update_indicator()

    def watch_duration(self, duration: str) -> None:
        self.query_one("#meeting_duration", Label).update(duration)

    def watch_segment_count(self, count: int) -> None:
        self._update_info()

    def watch_has_system_audio(self, has: bool) -> None:
        self._update_info()

    def watch_mic_level(self, level: float) -> None:
        self._update_levels()

    def watch_system_level(self, level: float) -> None:
        self._update_levels()

    def watch_web_url(self, url: str) -> None:
        label = self.query_one("#meeting_url", Label)
        if url:
            # Don't use Rich markup - URLs confuse the parser
            label.update(url)
        else:
            label.update("")

    def watch_title(self, title: str) -> None:
        label = self.query_one("#meeting_title_display", Label)
        if title:
            # Truncate if too long
            display = title if len(title) <= 30 else title[:27] + "..."
            label.update(f'"{display}"')
        else:
            label.update("")

    def _update_display(self) -> None:
        self.display = self.active
        if self.active:
            self.add_class("active")
        else:
            self.remove_class("active")
            self._blink_on = True

    def _tick(self) -> None:
        if self.active:
            self._blink_on = not self._blink_on
        else:
            self._blink_on = True

    def _update_indicator(self) -> None:
        indicator = self.query_one("#meeting_indicator", Static)
        if self.active and not self._blink_on:
            indicator.update(" ")
        else:
            indicator.update("⏺")

    def _update_info(self) -> None:
        parts = []
        if self.segment_count > 0:
            parts.append(f"{self.segment_count} segments")
        if self.has_system_audio:
            parts.append("dual-stream")
        else:
            parts.append("mic only")
        self.query_one("#meeting_info", Label).update(" │ ".join(parts))

    def _update_levels(self) -> None:
        """Update the level indicator display."""
        def level_bar(level: float, width: int = 10) -> str:
            level = clamp01(level)
            filled = int(round(level * width))
            filled = 0 if filled < 0 else width if filled > width else filled
            return "█" * filled + "░" * (width - filled)

        mic_bar = level_bar(self.mic_level)
        if self.has_system_audio:
            sys_bar = level_bar(self.system_level)
            sys_part = f"SYS {sys_bar}"
        else:
            sys_part = "SYS n/a"

        self.query_one("#meeting_levels", Label).update(f"MIC {mic_bar} │ {sys_part}")

    def set_active(self, active: bool) -> None:
        self.active = active

    def set_duration(self, duration: str) -> None:
        self.duration = duration

    def set_segment_count(self, count: int) -> None:
        self.segment_count = count

    def set_has_system_audio(self, has: bool) -> None:
        self.has_system_audio = has

    def set_web_url(self, url: str) -> None:
        self.web_url = url

    def set_mic_level(self, level: float) -> None:
        self.mic_level = clamp01(level)

    def set_system_level(self, level: float) -> None:
        self.system_level = clamp01(level)

    def set_title(self, title: str) -> None:
        self.title = title or ""
