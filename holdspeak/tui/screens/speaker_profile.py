"""Speaker profile screen - view all segments from a speaker across meetings."""

from datetime import datetime, timedelta
from typing import Optional

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static

from .meeting_detail import SpeakerRenameScreen, SpeakerUpdate
from ..services.speakers import get_speaker_profile_data, update_speaker_identity


class SpeakerProfileScreen(ModalScreen[None]):
    """Full profile view showing a speaker's history across all meetings."""

    BINDINGS = [
        ("escape", "cancel", "Close"),
        ("e", "edit", "Edit"),
    ]

    def __init__(self, speaker_id: str) -> None:
        super().__init__()
        self._speaker_id = speaker_id
        self._speaker = None
        self._stats: dict = {}
        self._meeting_groups: list[dict] = []

    def action_cancel(self) -> None:
        self.app.pop_screen()

    def action_edit(self) -> None:
        """Open edit dialog for speaker."""
        if self._speaker:
            self._show_edit_dialog()

    def compose(self) -> ComposeResult:
        with Container(id="speaker_profile_dialog"):
            # Header - will be populated on mount
            with Container(id="speaker_profile_header"):
                yield Static("", id="profile_avatar")
                yield Label("Loading...", id="profile_name")
                yield Label("", id="profile_stats_line")
                yield Label("", id="profile_dates_line")
                with Horizontal(id="profile_actions"):
                    yield Button("Edit", id="profile_edit")
                    yield Button("Close", id="profile_close")

            # Body - scrollable meeting groups
            with VerticalScroll(id="speaker_profile_body"):
                yield Static(
                    "Loading speaker history...",
                    id="profile_loading",
                )

    def on_mount(self) -> None:
        """Load speaker data after mount."""
        self._load_speaker_data()

    def _load_speaker_data(self) -> None:
        """Load speaker info, stats, and segments via the TUI service layer."""
        try:
            profile = get_speaker_profile_data(self._speaker_id)
            if not profile:
                self._show_error("Speaker not found")
                return

            self._speaker = profile.speaker
            self._stats = profile.stats
            self._meeting_groups = profile.meeting_groups

            # Update UI
            self._render_header()
            self._render_body()

        except Exception as e:
            self._show_error(f"Failed to load speaker: {e}")

    def _render_header(self) -> None:
        """Update header with speaker info."""
        if not self._speaker:
            return

        # Avatar
        avatar = self._speaker.avatar or "👤"
        self.query_one("#profile_avatar", Static).update(avatar)

        # Name
        self.query_one("#profile_name", Label).update(self._speaker.name)

        # Stats line
        stats = self._stats
        segments = stats.get("total_segments", 0)
        meetings = stats.get("meeting_count", 0)
        speaking_time = self._format_duration(stats.get("total_speaking_time", 0))
        stats_text = f"{meetings} meetings  •  {segments} segments  •  {speaking_time} speaking"
        self.query_one("#profile_stats_line", Label).update(stats_text)

        # Dates line
        first_seen = stats.get("first_seen")
        last_seen = stats.get("last_seen")
        if first_seen and last_seen:
            first_str = first_seen.strftime("%b %d, %Y")
            last_str = self._format_relative_date(last_seen)
            dates_text = f"First seen: {first_str}  •  Last seen: {last_str}"
        else:
            dates_text = ""
        self.query_one("#profile_dates_line", Label).update(dates_text)

    def _render_body(self) -> None:
        """Render meeting groups with segments."""
        body = self.query_one("#speaker_profile_body", VerticalScroll)

        # Remove loading indicator
        loading = self.query_one("#profile_loading", Static)
        loading.display = False

        if not self._meeting_groups:
            body.mount(
                Static(
                    "No segments found for this speaker.",
                    classes="profile_empty",
                )
            )
            return

        # Render each meeting group
        for group in self._meeting_groups:
            body.mount(self._create_meeting_group(group))

    def _create_meeting_group(self, group: dict) -> Container:
        """Create a meeting group card with segments."""
        meeting_id = group["meeting_id"]
        title = group["meeting_title"] or "(Untitled Meeting)"
        date = group["meeting_date"]
        segments = group["segments"]

        container = Container(classes="meeting_group_card", id=f"group_{meeting_id}")

        # We'll mount children after creating the container
        container._group_data = {
            "meeting_id": meeting_id,
            "title": title,
            "date": date,
            "segments": segments,
        }

        return container

    def on_mount_meeting_groups(self) -> None:
        """Called after body is rendered to populate meeting group cards."""
        for container in self.query(".meeting_group_card"):
            if hasattr(container, "_group_data"):
                data = container._group_data
                self._populate_meeting_group(container, data)

    def _populate_meeting_group(self, container: Container, data: dict) -> None:
        """Populate a meeting group card with content."""
        title = data["title"]
        date = data["date"]
        segments = data["segments"]
        meeting_id = data["meeting_id"]

        # Header
        date_str = self._format_relative_date(date)
        header = Horizontal(classes="meeting_group_header")
        container.mount(header)
        header.mount(Label(f"{title}", classes="meeting_group_title"))
        header.mount(Label(f"({date_str})", classes="meeting_group_date"))

        # Segments (show first 5, with expand option if more)
        segments_container = Vertical(classes="meeting_group_segments")
        container.mount(segments_container)

        display_segments = segments[:5]
        for seg in display_segments:
            time_str = self._format_timestamp(seg["start_time"])
            text = seg["text"]
            # Truncate long text
            if len(text) > 100:
                text = text[:97] + "..."

            row = Horizontal(classes="profile_segment_row")
            segments_container.mount(row)
            row.mount(Static(f"[{time_str}]", classes="profile_segment_time"))
            row.mount(Static(f'"{text}"', classes="profile_segment_text"))

        # Show count if more segments
        if len(segments) > 5:
            remaining = len(segments) - 5
            segments_container.mount(
                Label(
                    f"... and {remaining} more segment{'s' if remaining > 1 else ''}",
                    classes="profile_segment_more",
                )
            )

        # View meeting button
        footer = Horizontal(classes="meeting_group_footer")
        container.mount(footer)
        footer.mount(
            Button(
                "View Full Meeting →",
                id=f"view_meeting_{meeting_id}",
                classes="meeting_group_view_btn",
            )
        )

    async def _on_mount(self) -> None:
        """Handle async mount tasks."""
        # Populate meeting groups after initial render
        await self._populate_all_groups()

    async def _populate_all_groups(self) -> None:
        """Populate all meeting group cards."""
        for container in self.query(".meeting_group_card"):
            if hasattr(container, "_group_data"):
                data = container._group_data
                self._populate_meeting_group(container, data)
                delattr(container, "_group_data")

    def watch_is_mounted(self, mounted: bool) -> None:
        """Called when mount status changes."""
        if mounted:
            self.call_later(self._populate_all_groups)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id or ""

        if button_id == "profile_close":
            self.app.pop_screen()
        elif button_id == "profile_edit":
            self._show_edit_dialog()
        elif button_id.startswith("view_meeting_"):
            meeting_id = button_id[13:]  # Remove "view_meeting_" prefix
            self._open_meeting(meeting_id)

    def _show_edit_dialog(self) -> None:
        """Show the speaker edit modal."""
        if not self._speaker:
            return

        def handle_update(result: Optional[SpeakerUpdate]) -> None:
            if result:
                self._do_update_speaker(result.name, result.avatar)

        self.app.push_screen(
            SpeakerRenameScreen(
                self._speaker_id,
                self._speaker.name,
                self._speaker.avatar,
            ),
            handle_update,
        )

    def _do_update_speaker(self, new_name: str, new_avatar: str) -> None:
        """Persist speaker update via the TUI service layer and refresh UI."""
        try:
            update_speaker_identity(self._speaker_id, new_name, new_avatar)

            # Update local state
            if self._speaker:
                self._speaker.name = new_name
                self._speaker.avatar = new_avatar

            # Refresh header
            self._render_header()
            self.app.notify(f"Updated {new_avatar} {new_name}", timeout=1.5)

        except Exception as e:
            self.app.notify(f"Update failed: {e}", severity="error", timeout=2.0)

    def _open_meeting(self, meeting_id: str) -> None:
        """Open the full meeting detail screen."""
        from ..messages import SavedMeetingOpenDetail

        self.post_message(SavedMeetingOpenDetail(meeting_id))

    def _show_error(self, message: str) -> None:
        """Show an error message in the body."""
        try:
            loading = self.query_one("#profile_loading", Static)
            loading.update(f"[red]{message}[/red]")
        except Exception:
            pass

    def _format_duration(self, seconds: float) -> str:
        """Format duration as human-readable string."""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            mins = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{mins}m {secs}s"
        else:
            hours = int(seconds // 3600)
            mins = int((seconds % 3600) // 60)
            return f"{hours}h {mins}m"

    def _format_timestamp(self, seconds: float) -> str:
        """Format timestamp as HH:MM:SS or MM:SS."""
        hours = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        if hours > 0:
            return f"{hours:02d}:{mins:02d}:{secs:02d}"
        return f"{mins:02d}:{secs:02d}"

    def _format_relative_date(self, dt: datetime) -> str:
        """Format date as relative string (Today, Yesterday, or date)."""
        today = datetime.now().date()
        date = dt.date()

        if date == today:
            return "Today"
        elif date == today - timedelta(days=1):
            return "Yesterday"
        else:
            return dt.strftime("%b %d, %Y")
