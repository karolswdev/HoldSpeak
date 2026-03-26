"""Meeting detail screen - comprehensive view of a saved meeting."""

from dataclasses import dataclass
from typing import Optional

from textual.app import ComposeResult
from textual.containers import Container, Grid, Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Checkbox, Input, Label, Static, TabbedContent, TabPane

from ...meeting_session import MeetingState
from ...speaker_intel import SPEAKER_AVATARS


@dataclass
class SpeakerUpdate:
    """Result of speaker edit modal."""

    name: str
    avatar: str


class SpeakerRenameScreen(ModalScreen[Optional[SpeakerUpdate]]):
    """Modal for renaming a speaker and picking their avatar."""

    BINDINGS = [("escape", "cancel", "Cancel")]

    # Subset of fun avatars for the picker
    AVATAR_CHOICES = [
        # Row 1: Animals
        "🐶", "🐱", "🐼", "🦊", "🐻", "🦁", "🐸", "🐵",
        # Row 2: More animals
        "🐰", "🦄", "🐲", "🦉", "🐙", "🦋", "🐳", "🦩",
        # Row 3: Expressive
        "😎", "🤓", "🧐", "🤠", "👻", "🤖", "👽", "🥷",
        # Row 4: Nature/Objects
        "🌵", "🍄", "⭐", "🔮", "🎭", "🌈", "🔥", "💎",
    ]

    def __init__(
        self, speaker_id: str, current_name: str, current_avatar: Optional[str] = None
    ) -> None:
        super().__init__()
        self._speaker_id = speaker_id
        self._current_name = current_name
        self._current_avatar = current_avatar or "👤"
        self._selected_avatar = self._current_avatar

    def action_cancel(self) -> None:
        self.dismiss(None)

    def compose(self) -> ComposeResult:
        with Container(id="speaker_rename_dialog"):
            yield Label("Edit Speaker", id="speaker_rename_title")

            # Current avatar display
            with Horizontal(id="avatar_preview_row"):
                yield Static(self._selected_avatar, id="avatar_preview")
                yield Label(self._current_name, id="avatar_preview_name")

            # Avatar picker grid
            yield Label("Choose an avatar:", classes="speaker_rename_hint_label")
            with Grid(id="avatar_grid"):
                for emoji in self.AVATAR_CHOICES:
                    is_selected = emoji == self._selected_avatar
                    classes = "avatar_btn selected" if is_selected else "avatar_btn"
                    yield Button(emoji, id=f"avatar_{emoji}", classes=classes)

            # Name input
            yield Label("Name:", classes="speaker_rename_hint_label")
            yield Input(
                value=self._current_name,
                placeholder="e.g., Sarah, John, Project Manager",
                id="speaker_rename_input",
            )

            with Horizontal(id="speaker_rename_actions"):
                yield Button("Cancel", id="rename_cancel")
                yield Button("Save", variant="primary", id="rename_save")

    def on_mount(self) -> None:
        self.query_one("#speaker_rename_input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id or ""

        if button_id == "rename_cancel":
            self.dismiss(None)
        elif button_id == "rename_save":
            self._save()
        elif button_id.startswith("avatar_"):
            # Avatar selection
            emoji = button_id[7:]  # Remove "avatar_" prefix
            self._select_avatar(emoji)

    def _select_avatar(self, emoji: str) -> None:
        """Update the selected avatar."""
        self._selected_avatar = emoji

        # Update preview
        preview = self.query_one("#avatar_preview", Static)
        preview.update(emoji)

        # Update button styles
        for btn in self.query(".avatar_btn"):
            btn_emoji = (btn.id or "")[7:]  # Remove "avatar_" prefix
            if btn_emoji == emoji:
                btn.add_class("selected")
            else:
                btn.remove_class("selected")

    def _save(self) -> None:
        """Save the speaker update."""
        new_name = self.query_one("#speaker_rename_input", Input).value.strip()
        if not new_name:
            self.app.notify("Name cannot be empty", severity="warning")
            return
        self.dismiss(SpeakerUpdate(name=new_name, avatar=self._selected_avatar))

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self._save()


class MeetingDetailScreen(ModalScreen[None]):
    """Full-screen modal showing meeting details with summary, actions, transcript."""

    BINDINGS = [("escape", "cancel", "Close"), ("e", "edit", "Edit")]

    def __init__(self, meeting: MeetingState) -> None:
        super().__init__()
        self._meeting = meeting
        self._action_checkboxes: dict[str, Checkbox] = {}

    @property
    def meeting_id(self) -> str:
        return self._meeting.id

    def action_cancel(self) -> None:
        self.app.pop_screen()

    def action_edit(self) -> None:
        """Open metadata editor."""
        from .metadata import MeetingMetadataScreen

        # Route metadata save to the persisted meeting (not the active-meeting controller).
        if hasattr(self.app, "_set_saved_meeting_metadata_context"):
            self.app._set_saved_meeting_metadata_context(self._meeting.id)  # type: ignore[attr-defined]
        self.app.push_screen(MeetingMetadataScreen(self._meeting.title or "", self._meeting.tags or []))

    def apply_metadata(self, title: str, tags: list[str]) -> None:
        """Update the in-memory meeting and refresh visible header bits."""
        self._meeting.title = title or None
        self._meeting.tags = tags
        try:
            title_label = self.query_one("#detail_title", Label)
            title_label.update(title or "(Untitled Meeting)")
        except Exception:
            pass

        async def _update_tags() -> None:
            header = self.query_one("#meeting_detail_header", Container)

            # Remove existing tags row if tags were cleared.
            try:
                existing_row = self.query_one("#detail_tags", Horizontal)
            except Exception:
                existing_row = None

            if not tags:
                if existing_row is not None:
                    await existing_row.remove()
                return

            # Ensure tags row exists.
            if existing_row is None:
                existing_row = Horizontal(id="detail_tags")
                await header.mount(existing_row)

            await existing_row.remove_children()
            for tag in tags:
                await existing_row.mount(Static(f"#{tag}", classes="detail_tag"))

        # Run async UI updates safely.
        self.run_worker(_update_tags(), exclusive=True, group="meeting_detail_tags", exit_on_error=False)

    def compose(self) -> ComposeResult:
        m = self._meeting

        with Container(id="meeting_detail_dialog"):
            # Header
            yield from self._compose_header()

            # Main content with tabs
            with TabbedContent(id="meeting_detail_tabs"):
                with TabPane("Overview", id="tab_overview"):
                    yield from self._compose_overview()
                with TabPane("Actions", id="tab_actions"):
                    yield from self._compose_actions()
                with TabPane("Speakers", id="tab_speakers"):
                    yield from self._compose_speakers()
                with TabPane("Transcript", id="tab_transcript"):
                    yield from self._compose_transcript()

            # Footer actions
            with Horizontal(id="meeting_detail_footer"):
                yield Button("Close", id="detail_close")
                yield Button("Export", id="detail_export")
                yield Button("Edit", id="detail_edit", variant="primary")

    def _compose_header(self) -> ComposeResult:
        m = self._meeting
        title = m.title or "(Untitled Meeting)"
        date_str = m.started_at.strftime("%A, %B %d, %Y at %H:%M")
        duration = m.format_duration()

        with Container(id="meeting_detail_header"):
            yield Label(title, id="detail_title")
            with Horizontal(id="detail_meta"):
                yield Label(f"📅 {date_str}", classes="detail_meta_item")
                yield Label(f"⏱ {duration}", classes="detail_meta_item")
                yield Label(f"📝 {len(m.segments)} segments", classes="detail_meta_item")
            if m.tags:
                with Horizontal(id="detail_tags"):
                    for tag in m.tags:
                        yield Static(f"#{tag}", classes="detail_tag")

    def _compose_overview(self) -> ComposeResult:
        m = self._meeting
        intel = m.intel

        with VerticalScroll(id="overview_scroll"):
            # Summary
            with Container(classes="detail_section"):
                yield Label("Summary", classes="detail_section_title")
                if intel and intel.summary:
                    yield Static(intel.summary, classes="detail_summary_text")
                else:
                    yield Static(
                        "[dim]No summary available. AI summary is generated during longer meetings.[/dim]",
                        classes="detail_empty",
                        markup=True,
                    )

            # Topics
            with Container(classes="detail_section"):
                yield Label("Topics Discussed", classes="detail_section_title")
                if intel and intel.topics:
                    for topic in intel.topics:
                        yield Static(f"• {topic}", classes="detail_topic")
                else:
                    yield Static(
                        "[dim]No topics extracted.[/dim]",
                        classes="detail_empty",
                        markup=True,
                    )

            # Quick action items summary
            with Container(classes="detail_section"):
                yield Label("Action Items", classes="detail_section_title")
                if intel and intel.action_items:
                    pending = sum(
                        1
                        for a in intel.action_items
                        if self._get_status(a) == "pending"
                    )
                    done = sum(
                        1 for a in intel.action_items if self._get_status(a) == "done"
                    )
                    yield Static(
                        f"{pending} pending, {done} completed",
                        classes="detail_action_summary",
                    )
                    # Show first 3 pending
                    for item in intel.action_items[:3]:
                        if self._get_status(item) == "pending":
                            task = self._get_task(item)
                            owner = self._get_owner(item)
                            owner_str = f" (@{owner})" if owner else ""
                            yield Static(
                                f"☐ {task}{owner_str}", classes="detail_action_preview"
                            )
                else:
                    yield Static(
                        "[dim]No action items captured.[/dim]",
                        classes="detail_empty",
                        markup=True,
                    )

    def _compose_actions(self) -> ComposeResult:
        m = self._meeting
        intel = m.intel

        with VerticalScroll(id="actions_scroll"):
            if not intel or not intel.action_items:
                yield Static(
                    "No action items were captured in this meeting.\n\n"
                    "Action items are extracted automatically when discussing tasks, "
                    "assignments, or follow-ups during longer meetings.",
                    classes="detail_empty_full",
                )
                return

            # Group by status
            pending = [
                a for a in intel.action_items if self._get_status(a) == "pending"
            ]
            done = [a for a in intel.action_items if self._get_status(a) == "done"]
            dismissed = [
                a for a in intel.action_items if self._get_status(a) == "dismissed"
            ]

            if pending:
                yield Label(
                    f"Pending ({len(pending)})", classes="detail_action_group_title"
                )
                for item in pending:
                    yield self._action_item_widget(item)

            if done:
                yield Label(
                    f"Completed ({len(done)})", classes="detail_action_group_title"
                )
                for item in done:
                    yield self._action_item_widget(item)

            if dismissed:
                yield Label(
                    f"Dismissed ({len(dismissed)})", classes="detail_action_group_title"
                )
                for item in dismissed:
                    yield self._action_item_widget(item)

    def _action_item_widget(self, item) -> Container:
        """Create a widget for a single action item."""
        task = self._get_task(item)
        owner = self._get_owner(item)
        due = self._get_due(item)
        status = self._get_status(item)
        item_id = self._get_id(item)

        container = Container(classes="action_item_row")

        # Build the content manually in on_mount
        container._action_data = {
            "task": task,
            "owner": owner,
            "due": due,
            "status": status,
            "id": item_id,
        }
        return container

    def on_mount(self) -> None:
        """Populate action item rows after mount."""
        for container in self.query(".action_item_row"):
            if hasattr(container, "_action_data"):
                data = container._action_data
                is_done = data["status"] == "done"

                checkbox = Checkbox(
                    data["task"][:50] + ("..." if len(data["task"]) > 50 else ""),
                    value=is_done,
                    id=f"action_{data['id']}",
                )
                self._action_checkboxes[data["id"]] = checkbox
                container.mount(checkbox)

                meta_parts = []
                if data["owner"]:
                    meta_parts.append(f"@{data['owner']}")
                if data["due"]:
                    meta_parts.append(f"due: {data['due']}")
                if meta_parts:
                    container.mount(
                        Label(" | ".join(meta_parts), classes="action_item_meta")
                    )

    def _compose_speakers(self) -> ComposeResult:
        m = self._meeting

        # Load speaker avatars from database
        db_speakers: dict[str, dict] = {}
        try:
            from ...db import get_database

            db = get_database()
            for s in db.get_all_speakers():
                db_speakers[s.id] = {"avatar": s.avatar, "name": s.name}
        except Exception:
            pass  # Gracefully handle database errors

        # Fallback avatars for non-diarized speakers
        FALLBACK_AVATARS = ["🎙️", "👤", "🗣️", "💬", "📢", "🔊"]

        with VerticalScroll(id="speakers_scroll"):
            # Collect speaker stats from segments
            speakers: dict[str, dict] = {}
            for seg in m.segments:
                speaker_id = getattr(seg, "speaker_id", None)
                speaker_name = seg.speaker
                key = speaker_id or speaker_name

                if key not in speakers:
                    speakers[key] = {
                        "id": speaker_id,
                        "name": speaker_name,
                        "segment_count": 0,
                        "total_duration": 0.0,
                        "first_seen": seg.start_time,
                        "avatar": None,
                    }
                speakers[key]["segment_count"] += 1
                speakers[key]["total_duration"] += seg.duration

            if not speakers:
                yield Static(
                    "No speakers detected in this meeting.",
                    classes="detail_empty_full",
                )
                return

            # Enrich with database info (avatars, possibly updated names)
            for key, speaker in speakers.items():
                if speaker["id"] and speaker["id"] in db_speakers:
                    db_info = db_speakers[speaker["id"]]
                    speaker["avatar"] = db_info.get("avatar")
                    # Use the database name (may have been renamed)
                    if db_info.get("name"):
                        speaker["name"] = db_info["name"]

            # Check if any speakers have diarization IDs
            has_diarized = any(s["id"] is not None for s in speakers.values())

            if not has_diarized:
                yield Static(
                    "[dim]Speaker diarization was not enabled for this meeting.\n"
                    "Enable it in Settings to identify multiple speakers.[/dim]",
                    classes="speaker_diarization_hint",
                    markup=True,
                )

            # Sort: "Me" first, then diarized speakers by segment count
            sorted_speakers = sorted(
                speakers.values(),
                key=lambda s: (s["id"] is not None, -s["segment_count"]),
            )

            for idx, speaker in enumerate(sorted_speakers):
                is_mic = speaker["id"] is None and speaker["name"] in (
                    m.mic_label,
                    "Me",
                )
                is_renamable = speaker["id"] is not None

                # Get avatar: from database, or fallback
                if speaker["avatar"]:
                    avatar = speaker["avatar"]
                elif is_mic:
                    avatar = "🎙️"
                else:
                    avatar = FALLBACK_AVATARS[idx % len(FALLBACK_AVATARS)]

                with Container(
                    classes="speaker_card",
                    id=f"speaker_card_{speaker['id'] or speaker['name']}",
                ):
                    # Top row: avatar + name + segment count
                    with Horizontal(classes="speaker_card_header"):
                        yield Static(avatar, classes="speaker_avatar")
                        yield Label(speaker["name"], classes="speaker_name")
                        if is_renamable:
                            yield Static("✎", classes="speaker_edit_icon")
                        yield Label(
                            f"{speaker['segment_count']} segments",
                            classes="speaker_stat_badge",
                        )

                    # Bottom row: metadata
                    duration_str = self._format_speaking_time(speaker["total_duration"])
                    first_at = self._format_time(speaker["first_seen"])

                    if is_mic:
                        meta_text = f"Local microphone  •  {duration_str} speaking"
                    else:
                        meta_text = f"First spoke at {first_at}  •  {duration_str} speaking"

                    yield Label(meta_text, classes="speaker_meta")

                    # Rename hint for auto-labeled speakers
                    if is_renamable and speaker["name"].startswith("Speaker "):
                        yield Label(
                            "Click to rename this speaker",
                            classes="speaker_rename_hint",
                        )

                # Store data for click handling
                self._speaker_data = getattr(self, "_speaker_data", {})
                self._speaker_data[speaker["id"] or speaker["name"]] = speaker

    def _format_speaking_time(self, seconds: float) -> str:
        """Format duration as Xm Ys or Xh Ym."""
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

    def _compose_transcript(self) -> ComposeResult:
        m = self._meeting

        with VerticalScroll(id="transcript_scroll"):
            if not m.segments:
                yield Static(
                    "No transcript segments recorded.\n\n"
                    "Transcripts are captured when audio is detected during the meeting.",
                    classes="detail_empty_full",
                )
                return

            # Merge segments and bookmarks
            entries = []
            for seg in m.segments:
                entries.append(("segment", seg.start_time, seg))
            for bm in m.bookmarks:
                entries.append(("bookmark", bm.timestamp, bm))
            entries.sort(key=lambda x: x[1])

            for kind, ts, item in entries:
                if kind == "bookmark":
                    label_text = item.label or "Bookmark"
                    yield Static(
                        f"🔖 {label_text} @ {self._format_time(ts)}",
                        classes="transcript_bookmark",
                    )
                else:
                    yield Static(
                        f"[{item.format_timestamp()}] {item.speaker}",
                        classes="transcript_speaker",
                    )
                    yield Static(item.text, classes="transcript_text")

    def _format_time(self, seconds: float) -> str:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"

    # Helper methods for accessing action item data (handles both dict and object)
    def _get_task(self, item) -> str:
        return item.get("task", "") if isinstance(item, dict) else getattr(item, "task", "")

    def _get_owner(self, item) -> str:
        return item.get("owner", "") if isinstance(item, dict) else getattr(item, "owner", "")

    def _get_due(self, item) -> str:
        return item.get("due", "") if isinstance(item, dict) else getattr(item, "due", "")

    def _get_status(self, item) -> str:
        return item.get("status", "pending") if isinstance(item, dict) else getattr(item, "status", "pending")

    def _get_id(self, item) -> str:
        return item.get("id", "") if isinstance(item, dict) else getattr(item, "id", "")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "detail_close":
            self.app.pop_screen()
        elif event.button.id == "detail_edit":
            self.action_edit()
        elif event.button.id == "detail_export":
            self._export_meeting()

    def on_click(self, event) -> None:
        """Handle clicks on speaker cards."""
        # Walk up from the click target to find a speaker_card
        widget = event.widget if hasattr(event, "widget") else None
        if widget is None:
            return

        # Check if click was on the edit icon
        clicked_on_edit = False
        if hasattr(widget, "classes") and "speaker_edit_icon" in widget.classes:
            clicked_on_edit = True

        # Find the speaker card container
        card = None
        current = widget
        while current is not None:
            if hasattr(current, "classes") and "speaker_card" in current.classes:
                card = current
                break
            current = getattr(current, "parent", None)

        if card is None or card.id is None:
            return

        # Extract speaker ID from card ID (format: speaker_card_{id})
        card_id = card.id
        if not card_id.startswith("speaker_card_"):
            return

        key = card_id[13:]  # Remove "speaker_card_" prefix
        speaker_data = getattr(self, "_speaker_data", {}).get(key)

        if speaker_data and speaker_data.get("id"):
            speaker_id = speaker_data["id"]
            if clicked_on_edit:
                # Edit icon clicked - show rename dialog
                self._show_rename_dialog(
                    speaker_id,
                    speaker_data["name"],
                    speaker_data.get("avatar"),
                )
            else:
                # Card clicked - open speaker profile
                self._show_speaker_profile(speaker_id)

    def _show_speaker_profile(self, speaker_id: str) -> None:
        """Open the speaker profile screen."""
        from ..messages import SpeakerOpenProfile

        self.post_message(SpeakerOpenProfile(speaker_id))

    def _show_rename_dialog(
        self, speaker_id: str, current_name: str, current_avatar: str | None
    ) -> None:
        """Show the speaker rename modal."""

        def handle_update(result: SpeakerUpdate | None) -> None:
            if result:
                self._do_update_speaker(speaker_id, result.name, result.avatar)

        self.app.push_screen(
            SpeakerRenameScreen(speaker_id, current_name, current_avatar), handle_update
        )

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Handle action item checkbox toggle."""
        checkbox_id = event.checkbox.id or ""
        if checkbox_id.startswith("action_"):
            action_id = checkbox_id[7:]  # Remove "action_" prefix
            new_status = "done" if event.value else "pending"
            self._update_action_status(action_id, new_status)

    def _update_action_status(self, action_id: str, status: str) -> None:
        """Update action item status in database."""
        try:
            from ...db import get_database

            db = get_database()
            db.update_action_item_status(action_id, status)
            self.app.notify(
                "Marked complete" if status == "done" else "Marked pending",
                timeout=1.0,
            )
        except Exception as e:
            self.app.notify(f"Error: {e}", severity="error", timeout=2.0)

    def _do_update_speaker(
        self, speaker_id: str, new_name: str, new_avatar: str
    ) -> None:
        """Persist speaker update to database and update UI."""
        try:
            from ...db import get_database

            db = get_database()
            name_success = db.update_speaker_name(speaker_id, new_name)
            avatar_success = db.update_speaker_avatar(speaker_id, new_avatar)

            if name_success or avatar_success:
                self.app.notify(f"Updated {new_avatar} {new_name}", timeout=1.5)
                # Update the UI in the card
                try:
                    card = self.query_one(f"#speaker_card_{speaker_id}", Container)
                    # Update name
                    name_label = card.query_one(".speaker_name", Label)
                    name_label.update(new_name)
                    # Update avatar
                    avatar_label = card.query_one(".speaker_avatar", Static)
                    avatar_label.update(new_avatar)
                    # Hide the rename hint if it exists
                    for hint in card.query(".speaker_rename_hint"):
                        hint.display = False
                except Exception:
                    pass  # UI update is optional
            else:
                self.app.notify(
                    "Speaker not found in database", severity="warning", timeout=1.5
                )
        except Exception as e:
            self.app.notify(f"Update failed: {e}", severity="error", timeout=2.0)

    def _export_meeting(self) -> None:
        """Export meeting to markdown file."""
        try:
            from pathlib import Path

            m = self._meeting
            timestamp = m.started_at.strftime("%Y%m%d_%H%M%S")
            filename = f"meeting_{m.id[:8]}_{timestamp}.md"
            filepath = Path.home() / "Documents" / filename

            lines = [
                f"# {m.title or 'Meeting Transcript'}",
                "",
                f"**Date:** {m.started_at.strftime('%Y-%m-%d %H:%M')}",
                f"**Duration:** {m.format_duration()}",
                "",
            ]

            if m.intel:
                if m.intel.summary:
                    lines.extend(["## Summary", "", m.intel.summary, ""])
                if m.intel.topics:
                    lines.extend(["## Topics", ""])
                    for topic in m.intel.topics:
                        lines.append(f"- {topic}")
                    lines.append("")
                if m.intel.action_items:
                    lines.extend(["## Action Items", ""])
                    for item in m.intel.action_items:
                        task = self._get_task(item)
                        owner = self._get_owner(item)
                        status = self._get_status(item)
                        check = "x" if status == "done" else " "
                        owner_str = f" (@{owner})" if owner else ""
                        lines.append(f"- [{check}] {task}{owner_str}")
                    lines.append("")

            if m.tags:
                lines.extend(["## Tags", "", ", ".join(m.tags), ""])

            lines.append("## Transcript")
            lines.append("")
            for seg in m.segments:
                lines.append(f"**{seg.speaker}** [{seg.start_time:.0f}s]: {seg.text}")
                lines.append("")

            filepath.write_text("\n".join(lines))
            self.app.notify(f"Exported to {filepath.name}", timeout=2.0)
        except Exception as e:
            self.app.notify(f"Export failed: {e}", severity="error", timeout=2.0)
