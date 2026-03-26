"""Main TUI application for HoldSpeak."""

from __future__ import annotations

from pathlib import Path
import threading
from typing import Optional

import pyperclip
from textual.app import App
from textual.screen import Screen

from ..config import Config
from ..meeting_session import Bookmark, TranscriptSegment
from .state import AppUIState
from .messages import (
    MeetingBookmark,
    MeetingEditMetadata,
    MeetingMetadataSaved,
    MeetingOpenWeb,
    MeetingShowTranscript,
    MeetingToggle,
    SavedMeetingDelete,
    SavedMeetingEditMetadata,
    SavedMeetingExport,
    SavedMeetingOpenDetail,
    SpeakerOpenProfile,
)
from .screens import (
    ActionItemsScreen,
    MainScreen,
    MeetingHistoryScreen,
    MeetingMetadataScreen,
    MeetingScreen,
    MeetingTranscriptScreen,
    SettingsScreen,
)


# Get path to styles directory
STYLES_DIR = Path(__file__).parent / "styles"


class HoldSpeakApp(App):
    """Main Textual app for HoldSpeak; driven by external controller (main.py)."""

    CSS_PATH = STYLES_DIR / "app.tcss"
    BINDINGS = [
        ("ctrl+c", "quit", "Quit"),
        ("ctrl+q", "quit", "Quit"),
    ]

    # Re-export message classes for backward compatibility
    MeetingToggle = MeetingToggle
    MeetingBookmark = MeetingBookmark
    MeetingShowTranscript = MeetingShowTranscript
    MeetingEditMetadata = MeetingEditMetadata
    MeetingMetadataSaved = MeetingMetadataSaved
    MeetingOpenWeb = MeetingOpenWeb

    def __init__(self, config: Optional[Config] = None) -> None:
        super().__init__()
        self.config = config or Config.load()
        self._ui_thread_id: Optional[int] = None
        self._main_screen: Optional[MainScreen] = None
        self._saved_meeting_metadata_id: Optional[str] = None
        # Centralized UI state - single source of truth
        self._state = AppUIState(hotkey_display=self.config.hotkey.display)

    @property
    def ui_state(self) -> AppUIState:
        """Get the current UI state (read-only access for external code)."""
        return self._state

    def get_default_screen(self) -> Screen:
        """Use a custom default screen so widget ownership is explicit."""
        self._main_screen = MainScreen()
        return self._main_screen

    def on_mount(self) -> None:
        self._ui_thread_id = threading.get_ident()
        self.set_state("idle")
        self.update_hotkey_display(self.config.hotkey.display)

    def _on_ui_thread(self) -> bool:
        return self._ui_thread_id is not None and threading.get_ident() == self._ui_thread_id

    def _ui(self, callback, *args, **kwargs) -> None:
        if self._on_ui_thread():
            callback(*args, **kwargs)
        else:
            self.call_from_thread(callback, *args, **kwargs)

    # State management methods
    def set_state(self, state: str) -> None:
        """Update the status indicator (idle/recording/transcribing)."""
        # Update centralized state
        self._state.status = state
        # Update widget (only lives on MainScreen)
        def _apply() -> None:
            if self._main_screen is not None and self._main_screen.is_mounted:
                self._main_screen.set_state(state)
        self._ui(_apply)

    def set_audio_level(self, level: float) -> None:
        """Update the audio meter (0.0-1.0)."""
        # Update centralized state
        self._state.audio_level = level
        def _apply() -> None:
            if self._main_screen is not None and self._main_screen.is_mounted:
                self._main_screen.set_audio_level(level)
        self._ui(_apply)

    def add_transcription(self, text: str) -> None:
        """Add a transcription to history with timestamp."""
        def _apply() -> None:
            if self._main_screen is not None and self._main_screen.is_mounted:
                self._main_screen.add_transcription(text)
        self._ui(_apply)

    def update_hotkey_display(self, display: str) -> None:
        """Update the hotkey shown in the UI."""
        # Update centralized state
        self._state.hotkey_display = display
        def _apply() -> None:
            if self._main_screen is not None and self._main_screen.is_mounted:
                self._main_screen.update_hotkey_display(display)
        self._ui(_apply)

    def set_global_hotkey_status(self, enabled: bool, reason: str = "") -> None:
        """Update whether the global hotkey is available (and why if not)."""
        self._state.global_hotkey_enabled = enabled
        self._state.global_hotkey_disabled_reason = reason

        def _apply() -> None:
            if self._main_screen is not None and self._main_screen.is_mounted:
                self._main_screen.set_global_hotkey_enabled(enabled, reason)

        self._ui(_apply)

    def set_text_injection_status(self, enabled: bool, reason: str = "") -> None:
        """Update whether cross-app text injection is available (and why if not)."""
        self._state.text_injection_enabled = enabled
        self._state.text_injection_disabled_reason = reason

    def set_focused_hold_to_talk_key(self, key: str) -> None:
        """Update the focused-only hold-to-talk keybinding shown in the UI."""
        self._state.focused_hold_to_talk_key = key

        def _apply() -> None:
            if self._main_screen is not None and self._main_screen.is_mounted:
                self._main_screen.set_focused_hold_to_talk_key(key)

        self._ui(_apply)

    def action_copy_last(self) -> None:
        # Backward compatibility: delegate to main screen action.
        if self._main_screen is not None and self._main_screen.is_mounted:
            self._main_screen.action_copy_last()

    def copy_to_clipboard(self, text: str) -> bool:
        """Copy text to clipboard. Returns True on success."""
        try:
            pyperclip.copy(text)
            return True
        except Exception:
            self.bell()
            return False

    def _copy_to_clipboard(self, text: str) -> None:
        """Internal clipboard method for backward compatibility."""
        self.copy_to_clipboard(text)

    def show_settings(self) -> None:
        """Open the settings modal (utility helper)."""
        self._ui(lambda: self.push_screen(SettingsScreen(self.config)))

    def show_help(self) -> None:
        """Open the help modal (utility helper)."""
        from .screens import HelpScreen

        self._ui(lambda: self.push_screen(HelpScreen()))

    def on_settings_screen_applied(self, message: SettingsScreen.Applied) -> None:
        self.config = message.config
        self.update_hotkey_display(self.config.hotkey.display)
        self.notify("Settings saved", timeout=1.5)

    def _set_saved_meeting_metadata_context(self, meeting_id: str) -> None:
        """Route the next MeetingMetadataScreen save to a persisted meeting."""
        self._saved_meeting_metadata_id = meeting_id

    # === Saved meeting navigation/persistence intents (from any screen) ===
    def on_saved_meeting_open_detail(self, message: SavedMeetingOpenDetail) -> None:
        meeting_id = message.meeting_id

        def work() -> None:
            from ..db import get_database

            meeting = get_database().get_meeting(meeting_id)
            if meeting is None:
                self.call_from_thread(lambda: self.notify("Meeting not found", severity="warning", timeout=1.5))
                return

            from .screens import MeetingDetailScreen

            self.call_from_thread(lambda: self.push_screen(MeetingDetailScreen(meeting)))

        self.run_worker(work, thread=True, exclusive=True, group="saved_meeting_open", exit_on_error=False)

    def on_saved_meeting_edit_metadata(self, message: SavedMeetingEditMetadata) -> None:
        meeting_id = message.meeting_id

        def work() -> None:
            from ..db import get_database

            meeting = get_database().get_meeting(meeting_id)
            if meeting is None:
                self.call_from_thread(lambda: self.notify("Meeting not found", severity="warning", timeout=1.5))
                return

            def _open() -> None:
                self._set_saved_meeting_metadata_context(meeting_id)
                self.push_screen(MeetingMetadataScreen(meeting.title or "", meeting.tags or []))

            self.call_from_thread(_open)

        self.run_worker(work, thread=True, exclusive=True, group="saved_meeting_edit", exit_on_error=False)

    def on_saved_meeting_export(self, message: SavedMeetingExport) -> None:
        meeting_id = message.meeting_id

        def work() -> None:
            from pathlib import Path
            from ..db import get_database

            meeting = get_database().get_meeting(meeting_id)
            if meeting is None:
                self.call_from_thread(lambda: self.notify("Meeting not found", severity="warning", timeout=1.5))
                return

            timestamp = meeting.started_at.strftime("%Y%m%d_%H%M%S")
            filename = f"meeting_{meeting_id[:8]}_{timestamp}.md"
            filepath = Path.home() / "Documents" / filename

            lines = [
                f"# {meeting.title or 'Meeting Transcript'}",
                "",
                f"**Date:** {meeting.started_at.strftime('%Y-%m-%d %H:%M')}",
                f"**Duration:** {meeting.format_duration()}",
                "",
            ]
            if meeting.intel and meeting.intel.summary:
                lines.extend(["## Summary", "", meeting.intel.summary, ""])
            if meeting.tags:
                lines.extend(["## Tags", "", ", ".join(meeting.tags), ""])

            lines.append("## Transcript")
            lines.append("")
            for seg in meeting.segments:
                lines.append(f"**{seg.speaker}** [{seg.start_time:.0f}s]: {seg.text}")
                lines.append("")

            filepath.write_text("\n".join(lines))
            self.call_from_thread(lambda: self.notify(f"Exported to {filepath.name}", timeout=2.0))

        self.run_worker(work, thread=True, exclusive=True, group="saved_meeting_export", exit_on_error=False)

    def on_saved_meeting_delete(self, message: SavedMeetingDelete) -> None:
        meeting_id = message.meeting_id

        def work() -> None:
            from ..db import get_database

            deleted = get_database().delete_meeting(meeting_id)

            def _apply() -> None:
                if deleted:
                    if self._main_screen is not None and self._main_screen.is_mounted:
                        self._main_screen.refresh_meetings_list()
                    self.notify("Meeting deleted", timeout=1.5)
                else:
                    self.notify("Meeting not found", severity="warning", timeout=1.5)

            self.call_from_thread(_apply)

        self.run_worker(work, thread=True, exclusive=True, group="saved_meeting_delete", exit_on_error=False)

    def on_speaker_open_profile(self, message: SpeakerOpenProfile) -> None:
        from .screens import SpeakerProfileScreen

        self.push_screen(SpeakerProfileScreen(message.speaker_id))

    # Meeting mode methods
    def set_meeting_active(self, active: bool) -> None:
        """Update meeting bar visibility."""
        # Update centralized state
        self._state.meeting.active = active
        self._state.mode = "meeting" if active else "voice_typing"
        def _apply() -> None:
            if self._main_screen is not None and self._main_screen.is_mounted:
                self._main_screen.set_meeting_active(active)
        self._ui(_apply)

    def set_meeting_duration(self, duration: str) -> None:
        """Update meeting duration display."""
        # Update centralized state
        self._state.meeting.duration = duration
        def _apply() -> None:
            if self._main_screen is not None and self._main_screen.is_mounted:
                self._main_screen.set_meeting_duration(duration)
            # Also update cockpit if shown
            if hasattr(self, '_meeting_screen') and self._meeting_screen:
                self._meeting_screen.set_duration(duration)
        self._ui(_apply)

    def set_meeting_segment_count(self, count: int) -> None:
        """Update meeting segment count."""
        # Update centralized state
        self._state.meeting.segment_count = count
        def _apply() -> None:
            if self._main_screen is not None and self._main_screen.is_mounted:
                self._main_screen.set_meeting_segment_count(count)
            if hasattr(self, '_meeting_screen') and self._meeting_screen:
                self._meeting_screen.set_segment_count(count)
        self._ui(_apply)

    def set_meeting_has_system_audio(self, has: bool) -> None:
        """Update whether meeting has system audio."""
        # Update centralized state
        self._state.meeting.has_system_audio = has
        def _apply() -> None:
            if self._main_screen is not None and self._main_screen.is_mounted:
                self._main_screen.set_meeting_has_system_audio(has)
        self._ui(_apply)

    def set_meeting_web_url(self, url: str) -> None:
        """Update meeting web dashboard URL."""
        # Update centralized state
        self._state.meeting.web_url = url
        def _apply() -> None:
            if self._main_screen is not None and self._main_screen.is_mounted:
                self._main_screen.set_meeting_web_url(url)
        self._ui(_apply)

    def set_meeting_mic_level(self, level: float) -> None:
        """Update meeting mic level indicator."""
        # Update centralized state
        self._state.meeting.mic_level = level
        def _apply() -> None:
            if self._main_screen is not None and self._main_screen.is_mounted:
                self._main_screen.set_meeting_mic_level(level)
            if hasattr(self, '_meeting_screen') and self._meeting_screen:
                self._meeting_screen.set_mic_level(level)
        self._ui(_apply)

    def set_meeting_system_level(self, level: float) -> None:
        """Update meeting system audio level indicator."""
        # Update centralized state
        self._state.meeting.system_level = level
        def _apply() -> None:
            if self._main_screen is not None and self._main_screen.is_mounted:
                self._main_screen.set_meeting_system_level(level)
            if hasattr(self, '_meeting_screen') and self._meeting_screen:
                self._meeting_screen.set_system_level(level)
        self._ui(_apply)

    def show_meeting_transcript(
        self,
        segments: list[TranscriptSegment],
        bookmarks: list[Bookmark] = None,
    ) -> None:
        """Show meeting transcript modal with bookmarks."""
        self._ui(lambda: self.push_screen(MeetingTranscriptScreen(segments, bookmarks)))

    def action_toggle_meeting(self) -> None:
        """Toggle meeting mode - handled by controller."""
        self.post_message(MeetingToggle())

    def action_add_bookmark(self) -> None:
        """Add meeting bookmark - handled by controller."""
        self.post_message(MeetingBookmark())

    def action_show_transcript(self) -> None:
        """Show transcript - handled by controller."""
        self.post_message(MeetingShowTranscript())

    def action_show_history(self) -> None:
        """Show meeting history."""
        self._ui(lambda: self.push_screen(MeetingHistoryScreen()))

    def action_show_actions(self) -> None:
        """Show action items."""
        self._ui(lambda: self.push_screen(ActionItemsScreen()))

    def action_edit_meeting(self) -> None:
        """Edit meeting title/tags - handled by controller."""
        self.post_message(MeetingEditMetadata())

    def action_open_web(self) -> None:
        """Open meeting web dashboard - handled by controller."""
        self.post_message(MeetingOpenWeb())

    def set_meeting_title(self, title: str) -> None:
        """Update meeting title in bar."""
        # Update centralized state
        self._state.meeting.title = title
        def _apply() -> None:
            if self._main_screen is not None and self._main_screen.is_mounted:
                self._main_screen.set_meeting_title(title)
            if hasattr(self, '_meeting_screen') and self._meeting_screen:
                self._meeting_screen.set_title(title)
        self._ui(_apply)

    def show_meeting_metadata(self, title: str = "", tags: list[str] = None) -> None:
        """Show meeting metadata edit modal."""
        # Metadata edits initiated from an active meeting go to the controller path.
        self._saved_meeting_metadata_id = None
        self._ui(lambda: self.push_screen(MeetingMetadataScreen(title, tags)))

    def on_meeting_metadata_screen_saved(self, message: MeetingMetadataScreen.Saved) -> None:
        """Handle metadata save from modal."""
        # If the metadata modal was opened to edit a saved meeting, persist it here
        # and don't forward to the active-meeting controller path.
        meeting_id = self._saved_meeting_metadata_id
        if meeting_id:
            self._saved_meeting_metadata_id = None
            try:
                from ..db import get_database

                db = get_database()
                db.update_meeting_metadata(meeting_id, message.title, message.tags)
            except Exception as exc:
                self.notify(f"Update failed: {exc}", severity="error", timeout=2.0)
                return

            # Refresh meetings list on the main screen (if visible).
            if self._main_screen is not None and self._main_screen.is_mounted:
                try:
                    self._main_screen.refresh_meetings_list()
                except Exception:
                    pass

            # If a detail modal for this meeting is open, update it in-place.
            try:
                from .screens.meeting_detail import MeetingDetailScreen

                for screen in self.screen_stack:
                    if isinstance(screen, MeetingDetailScreen) and getattr(screen, "meeting_id", None) == meeting_id:
                        screen.apply_metadata(message.title, message.tags)
                        break
            except Exception:
                pass

            self.notify("Meeting updated", timeout=1.5)
            return

        self.post_message(MeetingMetadataSaved(message.title, message.tags))

    # Meeting cockpit methods
    def show_meeting_cockpit(self, title: str = "", has_system_audio: bool = False) -> None:
        """Show the full meeting cockpit screen."""
        self._meeting_screen = MeetingScreen(title=title, has_system_audio=has_system_audio)
        self._ui(lambda: self.push_screen(self._meeting_screen))

    def hide_meeting_cockpit(self) -> None:
        """Hide the meeting cockpit (return to main screen)."""
        if hasattr(self, '_meeting_screen') and self._meeting_screen:
            meeting_screen = self._meeting_screen

            def _apply() -> None:
                # Ensure we actually pop the cockpit even if a modal is on top.
                try:
                    while self.screen is not meeting_screen and len(self.screen_stack) > 1:
                        self.pop_screen()
                    if self.screen is meeting_screen:
                        self.pop_screen()
                finally:
                    self._meeting_screen = None

            self._ui(_apply)

    def update_meeting_cockpit_segment(self, segment: TranscriptSegment) -> None:
        """Add a segment to the meeting cockpit transcript."""
        if hasattr(self, '_meeting_screen') and self._meeting_screen:
            def _apply() -> None:
                self._meeting_screen.add_segment(segment)
            self._ui(_apply)

    def update_meeting_cockpit_bookmark(self, bookmark: Bookmark) -> None:
        """Add a bookmark to the meeting cockpit transcript."""
        if hasattr(self, '_meeting_screen') and self._meeting_screen:
            def _apply() -> None:
                self._meeting_screen.add_bookmark(bookmark)
            self._ui(_apply)

    def update_meeting_cockpit_intel(
        self,
        topics: list[str] = None,
        action_items: list[dict] = None,
        summary: str = None
    ) -> None:
        """Update the intel panel in the meeting cockpit."""
        if hasattr(self, '_meeting_screen') and self._meeting_screen:
            def _apply() -> None:
                self._meeting_screen.update_intel(topics, action_items, summary)
            self._ui(_apply)


def run_tui() -> None:
    """Convenience entry point for `python -m holdspeak.tui`."""
    HoldSpeakApp().run()
