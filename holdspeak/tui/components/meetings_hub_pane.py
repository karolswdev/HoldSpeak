"""Meetings hub pane - browse and manage saved meetings."""

from datetime import datetime, timedelta
from typing import Optional

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Button, Input, Label, Static

from ..messages import (
    SavedMeetingEditMetadata,
    SavedMeetingExport,
    SavedMeetingOpenDetail,
    SavedMeetingDelete,
)
from ..services.meetings import get_saved_meeting, list_saved_meetings, search_saved_meetings


class MeetingRow(Horizontal):
    """A compact selectable meeting row with one primary action."""

    class Selected(Message):
        def __init__(self, meeting_id: str) -> None:
            super().__init__()
            self.meeting_id = meeting_id

    class OpenRequested(Message):
        def __init__(self, meeting_id: str) -> None:
            super().__init__()
            self.meeting_id = meeting_id

    def __init__(self, meeting_summary, *, active: bool = False, **kwargs) -> None:
        super().__init__(**kwargs)
        self.meeting_summary = meeting_summary
        self._active = active
        self.add_class("meeting_row")

    @staticmethod
    def _format_duration(seconds: float) -> str:
        if not seconds:
            return "--:--"
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"

    def compose(self) -> ComposeResult:
        m = self.meeting_summary
        title = m.title or "(Untitled meeting)"
        date_str = m.started_at.strftime("%b %d, %Y %H:%M")
        duration = self._format_duration(m.duration_seconds)
        meta = f"{date_str}  |  {duration}  |  {m.segment_count} segments  |  {m.action_item_count} actions"
        tags = " ".join(f"#{t}" for t in m.tags[:3]) if m.tags else "No tags"

        with Vertical(classes="meeting_row_body"):
            yield Label(title, classes="meeting_row_title")
            yield Label(meta, classes="meeting_row_meta")
            yield Label(tags, classes="meeting_row_tags")
        yield Button("Open", id=f"open_{m.id}", classes="meeting_row_open_btn")

    def on_mount(self) -> None:
        self.set_active(self._active)

    def set_active(self, active: bool) -> None:
        self._active = active
        if active:
            self.add_class("selected")
        else:
            self.remove_class("selected")

        try:
            button = self.query_one(".meeting_row_open_btn", Button)
            button.variant = "primary" if active else "default"
        except Exception:
            pass

    def on_click(self, _event) -> None:
        self.post_message(self.Selected(self.meeting_summary.id))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id or ""
        if button_id.startswith("open_"):
            self.post_message(self.Selected(self.meeting_summary.id))
            self.post_message(self.OpenRequested(self.meeting_summary.id))
            event.stop()


# Keep MeetingCard as alias for backward compatibility
MeetingCard = MeetingRow


class MeetingsHubPane(Container):
    """Meetings hub with searchable list + selected-meeting preview."""

    meetings_count: reactive[int] = reactive(0)
    search_query: reactive[str] = reactive("")
    active_filter: reactive[str] = reactive("all")

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._meetings_by_id: dict[str, object] = {}
        self._selected_meeting_id: Optional[str] = None
        self._delete_armed_meeting_id: Optional[str] = None

    def compose(self) -> ComposeResult:
        # Hub header with title and search
        with Horizontal(id="meetings_hub_header"):
            yield Label("Meetings", id="meetings_hub_title")
            yield Static("", id="meetings_hub_spacer")
            yield Input(placeholder="Search transcripts...", id="meetings_search_input")

        # Filter bar
        with Horizontal(id="meetings_filter_bar"):
            yield Button("All", id="filter_all", classes="filter_btn active")
            yield Button("This Week", id="filter_week", classes="filter_btn")
            yield Button("This Month", id="filter_month", classes="filter_btn")
            yield Static("", id="filter_spacer")
            yield Label("", id="meetings_count_label")
            yield Button("Refresh", id="meetings_refresh", variant="primary")

        with Horizontal(id="meetings_content"):
            # Meetings list
            with Container(id="meetings_list_panel"):
                with VerticalScroll(id="meetings_list_container"):
                    yield Container(id="meetings_list")

            # Preview + actions for selected meeting
            with Container(id="meetings_preview_panel"):
                yield Label("Selected Meeting", id="meetings_preview_title")
                yield Static("Pick a meeting from the list to preview details.", id="meetings_preview_body")
                with Horizontal(id="meetings_preview_actions"):
                    yield Button("Open", id="preview_open", variant="primary")
                    yield Button("Edit", id="preview_edit")
                    yield Button("Export", id="preview_export")
                    yield Button("Delete", id="preview_delete")
                    yield Button("Cancel", id="preview_delete_cancel")

        # Empty state (shown when no meetings)
        yield Container(
            Static(
                "No meetings found.\n\nStart a meeting with [bold]m[/] to begin recording.",
                markup=True,
            ),
            id="meetings_empty_state",
        )

    def on_mount(self) -> None:
        self._load_meetings()

    def _load_meetings(
        self,
        date_from: Optional[datetime] = None,
        search_query: Optional[str] = None,
    ) -> None:
        """Load meetings via the TUI service layer."""
        try:
            if search_query:
                meetings = search_saved_meetings(
                    search_query, limit=100, date_from=date_from
                )
            else:
                meetings = list_saved_meetings(limit=50, date_from=date_from)
        except Exception as e:
            meetings = []
            try:
                self.app.notify(f"Failed to load meetings: {e}", severity="error", timeout=2.5)
            except Exception:
                pass

        self.meetings_count = len(meetings)
        # Render deterministically and avoid overlapping async renders.
        self.run_worker(
            self._render_meetings(meetings),
            group="meetings_render",
            exclusive=True,
            exit_on_error=False,
        )

    async def _render_meetings(self, meetings) -> None:
        """Render meeting rows."""
        content = self.query_one("#meetings_content", Horizontal)
        meetings_list = self.query_one("#meetings_list", Container)
        empty_state = self.query_one("#meetings_empty_state", Container)
        count_label = self.query_one("#meetings_count_label", Label)

        # Clear existing cards and await completion
        await meetings_list.remove_children()
        self._meetings_by_id = {m.id: m for m in meetings}

        if not meetings:
            self._selected_meeting_id = None
            self._delete_armed_meeting_id = None
            content.display = False
            empty_state.display = True
            count_label.update("")
            self._update_preview()
        else:
            content.display = True
            empty_state.display = False
            count_label.update(f"{len(meetings)} meetings")

            if self._selected_meeting_id not in self._meetings_by_id:
                self._selected_meeting_id = meetings[0].id
                self._delete_armed_meeting_id = None

            for meeting in meetings:
                await meetings_list.mount(
                    MeetingRow(
                        meeting,
                        id=f"row_{meeting.id}",
                        active=meeting.id == self._selected_meeting_id,
                    )
                )
            self._update_preview()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "meetings_search_input":
            query = event.value.strip()
            if query != self.search_query:
                self.search_query = query
            self._apply_filter()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id != "meetings_search_input":
            return
        query = event.value.strip()
        if query == self.search_query:
            return
        self.search_query = query
        self._apply_filter()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id

        if button_id == "meetings_refresh":
            self._apply_filter()
            self.app.notify("Meetings refreshed", timeout=1.0)
        elif button_id == "filter_all":
            self._set_filter("all")
        elif button_id == "filter_week":
            self._set_filter("week")
        elif button_id == "filter_month":
            self._set_filter("month")
        elif button_id == "preview_open":
            self._open_selected_meeting()
        elif button_id == "preview_edit":
            self._edit_selected_meeting()
        elif button_id == "preview_export":
            self._export_selected_meeting()
        elif button_id == "preview_delete":
            self._delete_selected_meeting()
        elif button_id == "preview_delete_cancel":
            self._delete_armed_meeting_id = None
            self._refresh_preview_actions()

    def _refresh_row_selection(self) -> None:
        for row in self.query(MeetingRow):
            row.set_active(row.meeting_summary.id == self._selected_meeting_id)

    def _set_filter(self, filter_id: str) -> None:
        """Set active filter and reload."""
        self.active_filter = filter_id

        # Update button styles
        for btn_id in ["filter_all", "filter_week", "filter_month"]:
            btn = self.query_one(f"#{btn_id}", Button)
            if btn_id == f"filter_{filter_id}":
                btn.add_class("active")
            else:
                btn.remove_class("active")

        self._apply_filter()

    def _apply_filter(self) -> None:
        """Apply current filter and reload meetings."""
        date_from = None
        if self.active_filter == "week":
            date_from = datetime.now() - timedelta(days=7)
        elif self.active_filter == "month":
            date_from = datetime.now() - timedelta(days=30)

        search = self.search_query if self.search_query else None
        self._load_meetings(date_from=date_from, search_query=search)

    def on_meeting_row_selected(self, event: MeetingRow.Selected) -> None:
        self._selected_meeting_id = event.meeting_id
        self._delete_armed_meeting_id = None
        self._refresh_row_selection()
        self._update_preview()

    def on_meeting_row_open_requested(self, event: MeetingRow.OpenRequested) -> None:
        self._selected_meeting_id = event.meeting_id
        self._refresh_row_selection()
        self._open_selected_meeting()

    def _selected_summary(self):
        if not self._selected_meeting_id:
            return None
        return self._meetings_by_id.get(self._selected_meeting_id)

    @staticmethod
    def _format_duration(seconds: float) -> str:
        if not seconds:
            return "--:--"
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"

    def _refresh_preview_actions(self) -> None:
        summary = self._selected_summary()
        selected_id = summary.id if summary else None
        disable_actions = selected_id is None
        delete_armed = selected_id is not None and self._delete_armed_meeting_id == selected_id

        open_btn = self.query_one("#preview_open", Button)
        edit_btn = self.query_one("#preview_edit", Button)
        export_btn = self.query_one("#preview_export", Button)
        delete_btn = self.query_one("#preview_delete", Button)
        cancel_btn = self.query_one("#preview_delete_cancel", Button)

        open_btn.disabled = disable_actions
        edit_btn.disabled = disable_actions
        export_btn.disabled = disable_actions
        delete_btn.disabled = disable_actions

        delete_btn.label = "Confirm delete" if delete_armed else "Delete"
        delete_btn.variant = "error" if delete_armed else "default"
        cancel_btn.display = delete_armed
        cancel_btn.disabled = not delete_armed

    def _update_preview(self) -> None:
        preview_body = self.query_one("#meetings_preview_body", Static)
        summary = self._selected_summary()

        if summary is None:
            preview_body.update("Pick a meeting from the list to preview details.")
            self._refresh_preview_actions()
            return

        started = summary.started_at.strftime("%A, %b %d, %Y at %H:%M")
        duration = self._format_duration(summary.duration_seconds)
        tags = ", ".join(f"#{tag}" for tag in summary.tags) if summary.tags else "No tags"
        title = summary.title or "(Untitled meeting)"
        snippet = "No transcript preview available."

        try:
            detail = get_saved_meeting(summary.id)
            if detail and detail.intel and detail.intel.summary:
                snippet = detail.intel.summary.strip()
            elif detail and detail.segments:
                first_segment = (detail.segments[0].text or "").strip()
                if first_segment:
                    snippet = first_segment
        except Exception:
            pass

        if len(snippet) > 220:
            snippet = f"{snippet[:217].rstrip()}..."

        preview_body.update(
            "\n".join(
                [
                    title,
                    f"{started}",
                    "",
                    f"Duration: {duration}",
                    f"Segments: {summary.segment_count}",
                    f"Action items: {summary.action_item_count}",
                    f"Tags: {tags}",
                    "",
                    "Preview",
                    snippet,
                ]
            )
        )
        self._refresh_preview_actions()

    def _open_selected_meeting(self) -> None:
        summary = self._selected_summary()
        if summary is None:
            return
        self.post_message(SavedMeetingOpenDetail(summary.id))

    def _edit_selected_meeting(self) -> None:
        summary = self._selected_summary()
        if summary is None:
            return
        self.post_message(SavedMeetingEditMetadata(summary.id))

    def _export_selected_meeting(self) -> None:
        summary = self._selected_summary()
        if summary is None:
            return
        self.post_message(SavedMeetingExport(summary.id))

    def _delete_selected_meeting(self) -> None:
        summary = self._selected_summary()
        if summary is None:
            return
        meeting_id = summary.id
        if self._delete_armed_meeting_id != meeting_id:
            self._delete_armed_meeting_id = meeting_id
            self._refresh_preview_actions()
            self.app.notify("Press delete again to confirm", severity="warning", timeout=1.5)
            return

        self._delete_armed_meeting_id = None
        self.post_message(SavedMeetingDelete(meeting_id))

    def refresh_meetings(self) -> None:
        """Public method to refresh the meetings list."""
        self._apply_filter()
