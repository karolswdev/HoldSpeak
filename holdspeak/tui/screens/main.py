"""Main (non-meeting) screen for HoldSpeak.

This screen owns the primary widget tree (chrome, tabs, panes, footer).
Keeping it as a Screen avoids brittle `App.query_one(...)` calls that break
when another Screen is on top (e.g. the meeting cockpit).
"""

from __future__ import annotations

import time

from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import ContentSwitcher, Input

from ..components import (
    AudioMeterWidget,
    CrtOverlay,
    FooterHintsWidget,
    HistoryWidget,
    HotkeyHintWidget,
    IconButton,
    MeetingBarWidget,
    MeetingsHubPane,
    StatusWidget,
    TabBarWidget,
    VoiceTypingPane,
)
from ..messages import (
    MeetingBookmark,
    MeetingEditMetadata,
    MeetingOpenWeb,
    MeetingShowTranscript,
    MeetingToggle,
    VoiceTypingStartRecording,
    VoiceTypingStopRecording,
)
from .help import HelpScreen
from .diagnostics import DiagnosticsScreen
from .settings import SettingsScreen


class MainScreen(Screen[None]):
    """Primary HoldSpeak UI screen (tabs + panes)."""

    _FOCUSED_HOLD_TO_TALK_RELEASE_GAP_S = 0.25
    _FOCUSED_HOLD_TO_TALK_NO_REPEAT_STOP_S = 1.25

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("s", "settings", "Settings"),
        ("c", "copy_last", "Copy last"),
        ("m", "toggle_meeting", "Toggle meeting"),
        ("b", "add_bookmark", "Add bookmark"),
        ("t", "show_transcript", "Show transcript"),
        ("e", "edit_meeting", "Edit meeting"),
        ("w", "open_web", "Open web UI"),
        ("d", "diagnostics", "Diagnostics"),
        ("r", "refresh_meetings", "Refresh"),
        ("slash", "focus_search", "Search"),
        ("1", "switch_tab('voice_typing')", "Voice"),
        ("2", "switch_tab('meetings')", "Meetings"),
        ("tab", "cycle_tab", "Switch tab"),
        ("question_mark", "help", "Help"),
    ]

    def compose(self) -> ComposeResult:
        with Container(id="chrome"):
            yield CrtOverlay(id="crt_overlay")
            yield MeetingBarWidget(id="meeting_bar")
            yield TabBarWidget(id="tab_bar")

            with ContentSwitcher(id="main_content", initial="voice_typing_pane"):
                yield VoiceTypingPane(self.app.config.hotkey.display, id="voice_typing_pane")
                yield MeetingsHubPane(id="meetings_pane")

            yield FooterHintsWidget(self.app.config.hotkey.display, id="footer")

    def on_mount(self) -> None:
        self._focused_hold_to_talk_active = False
        self._focused_hold_to_talk_started_at = 0.0
        self._focused_hold_to_talk_last_event_at = 0.0
        self._focused_hold_to_talk_seen_repeat = False
        self._focused_hold_to_talk_timer = self.set_interval(
            0.05,
            self._check_focused_hold_to_talk_release,
            pause=True,
            name="focused_hold_to_talk_release",
        )

        # Apply any state that may have been set before mount.
        try:
            self.set_state(self.app.ui_state.status)
            self.set_audio_level(self.app.ui_state.audio_level)
            self.update_hotkey_display(self.app.ui_state.hotkey_display)
            self.set_active_tab(self.app.ui_state.active_tab)
            self.set_global_hotkey_enabled(
                self.app.ui_state.global_hotkey_enabled,
                self.app.ui_state.global_hotkey_disabled_reason,
            )
            self.set_focused_hold_to_talk_key(self.app.ui_state.focused_hold_to_talk_key)

            meeting = self.app.ui_state.meeting
            self.set_meeting_active(meeting.active)
            self.set_meeting_has_system_audio(meeting.has_system_audio)
            self.set_meeting_duration(meeting.duration)
            self.set_meeting_segment_count(meeting.segment_count)
            self.set_meeting_mic_level(meeting.mic_level)
            self.set_meeting_system_level(meeting.system_level)
            self.set_meeting_title(meeting.title)
            self.set_meeting_web_url(meeting.web_url)
        except Exception:
            # Don't let UI init failures crash the app; they'll show up elsewhere.
            pass

    # ===== Imperative update API (called by App/controller) =====
    def set_state(self, state: str) -> None:
        self.query_one("#status", StatusWidget).set_state(state)

    def set_audio_level(self, level: float) -> None:
        self.query_one("#meter", AudioMeterWidget).set_level(level)

    def add_transcription(self, text: str) -> None:
        self.query_one("#history", HistoryWidget).add_transcription(text)

    def update_hotkey_display(self, display: str) -> None:
        self.query_one("#hotkey_hint", HotkeyHintWidget).set_hotkey_display(display)
        self.query_one("#footer", FooterHintsWidget).set_hotkey_display(display)
        self._update_history_empty_state_hint()

    def set_global_hotkey_enabled(self, enabled: bool, reason: str = "") -> None:
        self.query_one("#hotkey_hint", HotkeyHintWidget).set_global_hotkey_enabled(enabled)
        self.query_one("#footer", FooterHintsWidget).set_global_hotkey_enabled(enabled)
        self._update_history_empty_state_hint()

    def set_focused_hold_to_talk_key(self, key: str) -> None:
        self.query_one("#hotkey_hint", HotkeyHintWidget).set_focused_hold_to_talk_key(key)
        self.query_one("#footer", FooterHintsWidget).set_focused_hold_to_talk_key(key)
        self._update_history_empty_state_hint()

    def _update_history_empty_state_hint(self) -> None:
        try:
            self.query_one("#history", HistoryWidget).set_empty_state_hint(
                global_hotkey_enabled=self.app.ui_state.global_hotkey_enabled,
                hotkey_display=self.app.ui_state.hotkey_display,
                focused_hold_key=self.app.ui_state.focused_hold_to_talk_key,
            )
        except Exception:
            pass

    def set_active_tab(self, tab_id: str) -> None:
        self.query_one("#tab_bar", TabBarWidget).switch_to(tab_id)
        self.query_one("#main_content", ContentSwitcher).current = f"{tab_id}_pane"
        self.query_one("#footer", FooterHintsWidget).set_active_tab(tab_id)

    def set_meeting_active(self, active: bool) -> None:
        self.query_one("#meeting_bar", MeetingBarWidget).set_active(active)
        self.query_one("#footer", FooterHintsWidget).set_meeting_active(active)

    def set_meeting_duration(self, duration: str) -> None:
        self.query_one("#meeting_bar", MeetingBarWidget).set_duration(duration)

    def set_meeting_segment_count(self, count: int) -> None:
        self.query_one("#meeting_bar", MeetingBarWidget).set_segment_count(count)

    def set_meeting_has_system_audio(self, has: bool) -> None:
        self.query_one("#meeting_bar", MeetingBarWidget).set_has_system_audio(has)

    def set_meeting_web_url(self, url: str) -> None:
        self.query_one("#meeting_bar", MeetingBarWidget).set_web_url(url)

    def set_meeting_mic_level(self, level: float) -> None:
        self.query_one("#meeting_bar", MeetingBarWidget).set_mic_level(level)

    def set_meeting_system_level(self, level: float) -> None:
        self.query_one("#meeting_bar", MeetingBarWidget).set_system_level(level)

    def set_meeting_title(self, title: str) -> None:
        self.query_one("#meeting_bar", MeetingBarWidget).set_title(title)

    # ===== Handlers / actions (user input) =====
    def on_tab_bar_widget_tab_changed(self, event: TabBarWidget.TabChanged) -> None:
        self.set_active_tab(event.tab_id)
        self.app.ui_state.active_tab = event.tab_id

    def on_icon_button_pressed(self, message: IconButton.Pressed) -> None:
        # HUD buttons live in the tab bar.
        if message.icon_id == "settings":
            self.action_settings()
        elif message.icon_id == "help":
            self.action_help()

    def on_history_widget_copied(self, message: HistoryWidget.Copied) -> None:
        self.app.copy_to_clipboard(message.text)
        self.app.notify("Copied", timeout=1.0)

    def action_switch_tab(self, tab_id: str) -> None:
        self.set_active_tab(tab_id)
        self.app.ui_state.active_tab = tab_id

    def action_cycle_tab(self) -> None:
        tab_bar = self.query_one("#tab_bar", TabBarWidget)
        current = tab_bar.active_tab
        next_tab = "meetings" if current == "voice_typing" else "voice_typing"
        self.action_switch_tab(next_tab)

    def action_refresh_meetings(self) -> None:
        self.query_one("#meetings_pane", MeetingsHubPane).refresh_meetings()

    def action_focus_search(self) -> None:
        try:
            search_input = self.query_one("#meetings_search_input", Input)
            search_input.focus()
        except Exception:
            self.app.bell()

    def action_settings(self) -> None:
        self.app.push_screen(SettingsScreen(self.app.config))

    def action_help(self) -> None:
        self.app.push_screen(HelpScreen())

    def action_diagnostics(self) -> None:
        self.app.push_screen(DiagnosticsScreen())

    def action_copy_last(self) -> None:
        last = self.query_one("#history", HistoryWidget).get_last()
        if not last:
            self.app.bell()
            return
        self.app.copy_to_clipboard(last)
        self.app.notify("Copied last transcription", timeout=1.5)

    def action_toggle_meeting(self) -> None:
        self.post_message(MeetingToggle())

    def action_add_bookmark(self) -> None:
        self.post_message(MeetingBookmark())

    def action_show_transcript(self) -> None:
        self.post_message(MeetingShowTranscript())

    def action_edit_meeting(self) -> None:
        self.post_message(MeetingEditMetadata())

    def action_open_web(self) -> None:
        self.post_message(MeetingOpenWeb())

    def on_key(self, event) -> None:
        focused_hold_key = getattr(self.app.ui_state, "focused_hold_to_talk_key", "v")
        if event.key != focused_hold_key:
            return

        if self.app.ui_state.active_tab != "voice_typing":
            return

        # Don't steal text input from focused widgets.
        if isinstance(self.app.focused, Input):
            return

        now = time.monotonic()
        if not self._focused_hold_to_talk_active:
            # Avoid overlapping voice typing with active meeting capture.
            if self.app.ui_state.meeting.active:
                self.app.notify("Stop the meeting to use voice typing recording", timeout=2.0)
                event.prevent_default()
                event.stop()
                return

            self._focused_hold_to_talk_active = True
            self._focused_hold_to_talk_started_at = now
            self._focused_hold_to_talk_last_event_at = now
            self._focused_hold_to_talk_seen_repeat = False
            self._focused_hold_to_talk_timer.resume()
            self.post_message(VoiceTypingStartRecording())
        else:
            self._focused_hold_to_talk_last_event_at = now
            if now - self._focused_hold_to_talk_started_at > 0.05:
                self._focused_hold_to_talk_seen_repeat = True

        event.prevent_default()
        event.stop()

    def _check_focused_hold_to_talk_release(self) -> None:
        if not self._focused_hold_to_talk_active:
            return

        now = time.monotonic()
        if self._focused_hold_to_talk_seen_repeat:
            should_stop = (now - self._focused_hold_to_talk_last_event_at) > self._FOCUSED_HOLD_TO_TALK_RELEASE_GAP_S
        else:
            should_stop = (now - self._focused_hold_to_talk_started_at) > self._FOCUSED_HOLD_TO_TALK_NO_REPEAT_STOP_S

        if not should_stop:
            return

        self._focused_hold_to_talk_active = False
        self._focused_hold_to_talk_timer.pause()
        self.post_message(VoiceTypingStopRecording())

    def refresh_meetings_list(self) -> None:
        """Refresh the Meetings Hub list if present."""
        try:
            self.query_one("#meetings_pane", MeetingsHubPane).refresh_meetings()
        except Exception:
            pass
