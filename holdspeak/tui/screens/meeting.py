"""Dedicated meeting cockpit screen with live transcript and intel."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Label, ListItem, ListView, Static

from ..utils import clamp01
from ...meeting_session import Bookmark, TranscriptSegment


class MeetingHeader(Horizontal):
    """Meeting status bar at top of cockpit."""

    duration: reactive[str] = reactive("00:00")
    segment_count: reactive[int] = reactive(0)
    has_system_audio: reactive[bool] = reactive(False)
    title: reactive[str] = reactive("")
    mic_level: reactive[float] = reactive(0.0)
    system_level: reactive[float] = reactive(0.0)
    _blink_on: reactive[bool] = reactive(True)

    def compose(self) -> ComposeResult:
        yield Static("⏺", id="cockpit_indicator")
        yield Label("REC", id="cockpit_label")
        yield Label("", id="cockpit_title")
        yield Label("00:00", id="cockpit_duration")
        yield Label("", id="cockpit_levels")
        yield Static("", id="cockpit_spacer")
        yield Label("", id="cockpit_info")

    def on_mount(self) -> None:
        self.set_interval(0.5, self._tick)

    def watch_duration(self, duration: str) -> None:
        self.query_one("#cockpit_duration", Label).update(duration)

    def watch_segment_count(self, count: int) -> None:
        self._update_info()

    def watch_has_system_audio(self, has: bool) -> None:
        self._update_info()

    def watch_title(self, title: str) -> None:
        label = self.query_one("#cockpit_title", Label)
        if title:
            display = title if len(title) <= 30 else title[:27] + "..."
            label.update(f'"{display}"')
        else:
            label.update("")

    def watch_mic_level(self, level: float) -> None:
        self._update_levels()

    def watch_system_level(self, level: float) -> None:
        self._update_levels()

    def watch__blink_on(self, _value: bool) -> None:
        indicator = self.query_one("#cockpit_indicator", Static)
        indicator.update("⏺" if self._blink_on else " ")

    def _tick(self) -> None:
        self._blink_on = not self._blink_on

    def _update_info(self) -> None:
        parts = []
        if self.segment_count > 0:
            parts.append(f"{self.segment_count} segments")
        if self.has_system_audio:
            parts.append("dual-stream")
        else:
            parts.append("mic only")
        self.query_one("#cockpit_info", Label).update(" │ ".join(parts))

    def _update_levels(self) -> None:
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

        self.query_one("#cockpit_levels", Label).update(f"MIC {mic_bar} │ {sys_part}")


class TranscriptPanel(Container):
    """Live transcript panel showing segments and bookmarks."""

    def compose(self) -> ComposeResult:
        yield Label("Live Transcript", classes="panel_title")
        yield ListView(id="transcript_live")

    def add_segment(self, segment: TranscriptSegment) -> None:
        """Add a new transcript segment."""
        list_view = self.query_one("#transcript_live", ListView)
        text = f"[{segment.format_timestamp()}] {segment.speaker}: {segment.text}"
        list_view.mount(ListItem(Label(text, classes="transcript_line")))
        # Scroll to bottom
        list_view.scroll_end(animate=False)

    def add_bookmark(self, bookmark: Bookmark) -> None:
        """Add a bookmark marker."""
        import time
        list_view = self.query_one("#transcript_live", ListView)
        ts_str = time.strftime("%H:%M:%S", time.gmtime(bookmark.timestamp))
        label = bookmark.label or "Bookmark"
        text = f"[bold yellow]🔖 {label}[/] [dim]@ {ts_str}[/dim]"
        list_view.mount(ListItem(Label(text, classes="bookmark_marker", markup=True)))
        list_view.scroll_end(animate=False)

    def clear(self) -> None:
        """Clear all entries."""
        list_view = self.query_one("#transcript_live", ListView)
        list_view.clear()


class IntelPanel(Container):
    """Intelligence panel showing topics, action items, and summary."""

    def compose(self) -> ComposeResult:
        yield Label("Intelligence", classes="panel_title")
        with VerticalScroll(id="intel_scroll"):
            yield Static("[dim]Analyzing meeting...[/dim]", id="intel_content", markup=True)

    def set_topics(self, topics: list[str]) -> None:
        """Update the topics section."""
        self._update_content()

    def set_action_items(self, items: list[dict]) -> None:
        """Update action items section."""
        self._update_content()

    def set_summary(self, summary: str) -> None:
        """Update summary section."""
        self._update_content()

    def update_intel(self, topics: list[str] = None, action_items: list[dict] = None, summary: str = None) -> None:
        """Update all intel sections at once."""
        content_parts = []

        if topics:
            content_parts.append("[bold]Topics[/]")
            for topic in topics[:5]:  # Limit to top 5
                content_parts.append(f"  • {topic}")
            content_parts.append("")

        if action_items:
            content_parts.append("[bold]Action Items[/]")
            for item in action_items[:5]:  # Limit to top 5
                task = item.get("task", "")
                owner = item.get("owner", "")
                if owner:
                    content_parts.append(f"  ☐ {task} ({owner})")
                else:
                    content_parts.append(f"  ☐ {task}")
            content_parts.append("")

        if summary:
            content_parts.append("[bold]Summary[/]")
            # Truncate long summaries
            if len(summary) > 200:
                summary = summary[:197] + "..."
            content_parts.append(f"  {summary}")

        if content_parts:
            self.query_one("#intel_content", Static).update("\n".join(content_parts))
        else:
            self.query_one("#intel_content", Static).update("[dim]Analyzing meeting...[/dim]")

    def _update_content(self) -> None:
        # Individual setters call update_intel
        pass


class MeetingFooter(Static):
    """Footer with meeting-specific keybinding hints."""

    def render(self):
        from rich.text import Text
        parts = [
            "b Bookmark",
            "e Edit",
            "c Copy",
            "m Stop",
            "Escape minimize",
        ]
        return Text("  │  ".join(parts))


class MeetingScreen(Screen):
    """Full meeting cockpit with live updates."""

    BINDINGS = [
        ("b", "bookmark", "Bookmark"),
        ("e", "edit", "Edit"),
        ("c", "copy", "Copy"),
        ("m", "stop", "Stop meeting"),
        ("escape", "minimize", "Minimize"),
    ]

    def __init__(self, title: str = "", has_system_audio: bool = False) -> None:
        super().__init__()
        self._initial_title = title
        self._has_system_audio = has_system_audio

    def compose(self) -> ComposeResult:
        with Container(id="meeting_cockpit"):
            yield MeetingHeader(id="meeting_header")
            with Horizontal(id="meeting_content"):
                yield TranscriptPanel(id="transcript_panel")
                yield IntelPanel(id="intel_panel")
            yield MeetingFooter(id="meeting_footer")

    def on_mount(self) -> None:
        header = self.query_one("#meeting_header", MeetingHeader)
        header.title = self._initial_title
        header.has_system_audio = self._has_system_audio

    # Update methods called by controller via app
    def set_duration(self, duration: str) -> None:
        self.query_one("#meeting_header", MeetingHeader).duration = duration

    def set_segment_count(self, count: int) -> None:
        self.query_one("#meeting_header", MeetingHeader).segment_count = count

    def set_title(self, title: str) -> None:
        self.query_one("#meeting_header", MeetingHeader).title = title

    def set_mic_level(self, level: float) -> None:
        self.query_one("#meeting_header", MeetingHeader).mic_level = level

    def set_system_level(self, level: float) -> None:
        self.query_one("#meeting_header", MeetingHeader).system_level = level

    def add_segment(self, segment: TranscriptSegment) -> None:
        self.query_one("#transcript_panel", TranscriptPanel).add_segment(segment)

    def add_bookmark(self, bookmark: Bookmark) -> None:
        self.query_one("#transcript_panel", TranscriptPanel).add_bookmark(bookmark)

    def update_intel(self, topics: list[str] = None, action_items: list[dict] = None, summary: str = None) -> None:
        self.query_one("#intel_panel", IntelPanel).update_intel(topics, action_items, summary)

    # Action handlers - delegate to app
    def action_bookmark(self) -> None:
        from ..messages import MeetingBookmark
        self.app.post_message(MeetingBookmark())

    def action_edit(self) -> None:
        from ..messages import MeetingEditMetadata
        self.app.post_message(MeetingEditMetadata())

    def action_copy(self) -> None:
        # Copy last segment if available
        list_view = self.query_one("#transcript_live", ListView)
        if list_view.children:
            last = list_view.children[-1]
            label = last.query_one(Label)
            text = str(label.renderable)
            self.app.copy_to_clipboard(text)
            self.app.notify("Copied", timeout=1.0)
        else:
            self.app.bell()

    def action_stop(self) -> None:
        from ..messages import MeetingToggle
        self.app.post_message(MeetingToggle())

    def action_minimize(self) -> None:
        """Return to main screen without stopping meeting."""
        self.app.pop_screen()
