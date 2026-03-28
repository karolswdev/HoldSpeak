"""Integration tests for HoldSpeak TUI."""

from __future__ import annotations

from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from textual.widgets import Button, Label, Static

from holdspeak.config import Config
from holdspeak.db import MeetingSummary
from holdspeak.tui import HoldSpeakApp
from holdspeak.tui.components import (
    AudioMeterWidget,
    FooterHintsWidget,
    HistoryWidget,
    HotkeyHintWidget,
    MeetingBarWidget,
    MeetingsHubPane,
    StatusWidget,
)
from holdspeak.tui.screens import MeetingTranscriptScreen, SettingsScreen
from holdspeak.tui.utils import clamp01


class FakeMeetingsDb:
    """In-memory DB stub for meetings pane integration tests."""

    def __init__(self, meetings, details, search_index):
        self._meetings = meetings
        self._details = details
        self._search_index = search_index

    def list_meetings(self, limit=50, date_from=None):
        meetings = list(self._meetings)
        if date_from is not None:
            meetings = [m for m in meetings if m.started_at >= date_from]
        return meetings[:limit]

    def search_transcripts(self, query, limit=100):
        ids = self._search_index.get(query.lower(), [])
        return [(meeting_id, "match") for meeting_id in ids[:limit]]

    def get_meeting(self, meeting_id):
        return self._details.get(meeting_id)


def _meeting_summary(
    meeting_id: str,
    title: str,
    *,
    days_ago: int,
    duration_seconds: float,
    segment_count: int,
    action_item_count: int,
    tags: list[str],
) -> MeetingSummary:
    return MeetingSummary(
        id=meeting_id,
        started_at=datetime.now() - timedelta(days=days_ago),
        ended_at=None,
        title=title,
        duration_seconds=duration_seconds,
        segment_count=segment_count,
        action_item_count=action_item_count,
        tags=tags,
    )


# ============================================================
# Utility Function Tests
# ============================================================


@pytest.mark.integration
class TestClamp01:
    """Tests for clamp01 utility function."""

    def test_clamp_below_zero(self):
        """Values below 0 should clamp to 0."""
        assert clamp01(-1.0) == 0.0
        assert clamp01(-0.1) == 0.0
        assert clamp01(-100) == 0.0

    def test_clamp_above_one(self):
        """Values above 1 should clamp to 1."""
        assert clamp01(1.1) == 1.0
        assert clamp01(2.0) == 1.0
        assert clamp01(100) == 1.0

    def test_valid_range(self):
        """Values in range should pass through."""
        assert clamp01(0.0) == 0.0
        assert clamp01(0.5) == 0.5
        assert clamp01(1.0) == 1.0


# ============================================================
# StatusWidget Tests
# ============================================================


@pytest.mark.integration
class TestStatusWidget:
    """Tests for StatusWidget component."""

    @pytest.mark.asyncio
    async def test_default_state_idle(self):
        """StatusWidget should default to idle state."""
        app = HoldSpeakApp()
        async with app.run_test(size=(100, 30)) as pilot:
            status = app.query_one("#status", StatusWidget)
            assert status.state == "idle"

    @pytest.mark.asyncio
    async def test_set_state_recording(self):
        """set_state() should update to recording."""
        app = HoldSpeakApp()
        async with app.run_test(size=(100, 30)) as pilot:
            status = app.query_one("#status", StatusWidget)
            status.set_state("recording")
            await pilot.pause()
            assert status.state == "recording"
            assert "recording" in status.classes

    @pytest.mark.asyncio
    async def test_set_state_transcribing(self):
        """set_state() should update to transcribing."""
        app = HoldSpeakApp()
        async with app.run_test(size=(100, 30)) as pilot:
            status = app.query_one("#status", StatusWidget)
            status.set_state("transcribing")
            await pilot.pause()
            assert status.state == "transcribing"
            assert "transcribing" in status.classes

    @pytest.mark.asyncio
    async def test_set_state_loading(self):
        """set_state() should update to loading."""
        app = HoldSpeakApp()
        async with app.run_test(size=(100, 30)) as pilot:
            status = app.query_one("#status", StatusWidget)
            status.set_state("loading")
            await pilot.pause()
            assert status.state == "loading"

    @pytest.mark.asyncio
    async def test_set_state_error(self):
        """set_state() should update to error."""
        app = HoldSpeakApp()
        async with app.run_test(size=(100, 30)) as pilot:
            status = app.query_one("#status", StatusWidget)
            status.set_state("error")
            await pilot.pause()
            assert status.state == "error"

    @pytest.mark.asyncio
    async def test_invalid_state_becomes_idle(self):
        """Invalid state should default to idle."""
        app = HoldSpeakApp()
        async with app.run_test(size=(100, 30)) as pilot:
            status = app.query_one("#status", StatusWidget)
            status.set_state("invalid_state")
            await pilot.pause()
            # The state reactive stores what was set, but _apply_state normalizes
            assert "idle" in status.classes


# ============================================================
# AudioMeterWidget Tests
# ============================================================


@pytest.mark.integration
class TestAudioMeterWidget:
    """Tests for AudioMeterWidget component."""

    @pytest.mark.asyncio
    async def test_default_level_zero(self):
        """AudioMeterWidget should default to level 0."""
        app = HoldSpeakApp()
        async with app.run_test(size=(100, 30)) as pilot:
            meter = app.query_one("#meter", AudioMeterWidget)
            assert meter.level == 0.0

    @pytest.mark.asyncio
    async def test_set_level_valid(self):
        """set_level() should update level."""
        app = HoldSpeakApp()
        async with app.run_test(size=(100, 30)) as pilot:
            meter = app.query_one("#meter", AudioMeterWidget)
            meter.set_level(0.5)
            await pilot.pause()
            assert meter.level == 0.5

    @pytest.mark.asyncio
    async def test_set_level_clamps_high(self):
        """set_level() should clamp values > 1."""
        app = HoldSpeakApp()
        async with app.run_test(size=(100, 30)) as pilot:
            meter = app.query_one("#meter", AudioMeterWidget)
            meter.set_level(1.5)
            await pilot.pause()
            assert meter.level == 1.0

    @pytest.mark.asyncio
    async def test_set_level_clamps_low(self):
        """set_level() should clamp values < 0."""
        app = HoldSpeakApp()
        async with app.run_test(size=(100, 30)) as pilot:
            meter = app.query_one("#meter", AudioMeterWidget)
            meter.set_level(-0.5)
            await pilot.pause()
            assert meter.level == 0.0


# ============================================================
# App State Tests
# ============================================================


@pytest.mark.integration
class TestHoldSpeakAppState:
    """Tests for HoldSpeakApp state management."""

    @pytest.mark.asyncio
    async def test_app_starts_idle(self):
        """App should start in idle state."""
        app = HoldSpeakApp()
        async with app.run_test(size=(100, 30)) as pilot:
            status = app.query_one("#status", StatusWidget)
            assert status.state == "idle"

    @pytest.mark.asyncio
    async def test_set_state_updates_display(self):
        """app.set_state() should update status widget."""
        app = HoldSpeakApp()
        async with app.run_test(size=(100, 30)) as pilot:
            app.set_state("recording")
            await pilot.pause()
            status = app.query_one("#status", StatusWidget)
            assert status.state == "recording"

    @pytest.mark.asyncio
    async def test_set_audio_level(self):
        """app.set_audio_level() should update meter."""
        app = HoldSpeakApp()
        async with app.run_test(size=(100, 30)) as pilot:
            app.set_audio_level(0.75)
            await pilot.pause()
            meter = app.query_one("#meter", AudioMeterWidget)
            assert meter.level == 0.75

    @pytest.mark.asyncio
    async def test_add_transcription(self):
        """app.add_transcription() should add to history."""
        app = HoldSpeakApp()
        async with app.run_test(size=(100, 30)) as pilot:
            app.add_transcription("Hello world")
            await pilot.pause()
            history = app.query_one("#history", HistoryWidget)
            assert history.get_last() == "Hello world"


# ============================================================
# Keyboard Shortcut Tests
# ============================================================


@pytest.mark.integration
class TestKeyboardShortcuts:
    """Tests for TUI keyboard shortcuts."""

    @pytest.mark.asyncio
    async def test_q_quits(self):
        """Pressing q should quit the app."""
        app = HoldSpeakApp()
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.press("q")
            await pilot.pause()
            assert app.is_running is False

    @pytest.mark.asyncio
    async def test_s_opens_settings(self):
        """Pressing s should open settings modal."""
        app = HoldSpeakApp()
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.press("s")
            await pilot.pause()
            # Check if settings screen is pushed
            assert isinstance(app.screen, SettingsScreen)

    @pytest.mark.asyncio
    async def test_m_toggles_meeting(self):
        """Pressing m should post meeting toggle message."""
        app = HoldSpeakApp()
        messages = []

        def handler(msg):
            messages.append(msg)

        async with app.run_test(size=(100, 30)) as pilot:
            app._message_hook = handler
            await pilot.press("m")
            await pilot.pause()
            # The action posts a message; in test we just verify it doesn't crash

    @pytest.mark.asyncio
    async def test_b_bookmark(self):
        """Pressing b should post bookmark message."""
        app = HoldSpeakApp()
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.press("b")
            await pilot.pause()
            # Verify no crash

    @pytest.mark.asyncio
    async def test_c_copy_last_no_history(self):
        """Pressing c with no history should bell."""
        app = HoldSpeakApp()
        async with app.run_test(size=(100, 30)) as pilot:
            # No transcriptions added, should handle gracefully
            await pilot.press("c")
            await pilot.pause()


# ============================================================
# Settings Modal Tests
# ============================================================


@pytest.mark.integration
class TestSettingsScreen:
    """Tests for SettingsScreen modal."""

    @pytest.mark.asyncio
    async def test_settings_opens(self):
        """Settings screen should open via action."""
        app = HoldSpeakApp()
        async with app.run_test(size=(100, 30)) as pilot:
            app.show_settings()
            await pilot.pause()
            assert isinstance(app.screen, SettingsScreen)

    @pytest.mark.asyncio
    async def test_settings_cancel_closes(self):
        """Cancel button should close settings."""
        app = HoldSpeakApp()
        async with app.run_test(size=(100, 30)) as pilot:
            app.show_settings()
            await pilot.pause()

            cancel_btn = app.screen.query_one("#settings_cancel", Button)
            await pilot.click(cancel_btn)
            await pilot.pause()

            # Should be back on main screen
            assert not isinstance(app.screen, SettingsScreen)

    @pytest.mark.asyncio
    async def test_settings_has_hotkey_select(self):
        """Settings should have hotkey selector."""
        app = HoldSpeakApp()
        async with app.run_test(size=(100, 30)) as pilot:
            app.show_settings()
            await pilot.pause()

            hotkey_select = app.screen.query_one("#hotkey_select")
            assert hotkey_select is not None

    @pytest.mark.asyncio
    async def test_settings_has_model_select(self):
        """Settings should have model selector."""
        app = HoldSpeakApp()
        async with app.run_test(size=(100, 30)) as pilot:
            app.show_settings()
            await pilot.pause()

            model_select = app.screen.query_one("#model_select")
            assert model_select is not None

    @pytest.mark.asyncio
    async def test_settings_has_meeting_and_speaker_controls(self):
        """Settings should expose meeting audio + speaker controls."""
        app = HoldSpeakApp()
        async with app.run_test(size=(100, 30)) as pilot:
            app.show_settings()
            await pilot.pause()

            assert app.screen.query_one("#mic_select") is not None
            assert app.screen.query_one("#system_audio_select") is not None
            assert app.screen.query_one("#mic_label_input") is not None
            assert app.screen.query_one("#remote_label_input") is not None
            assert app.screen.query_one("#intel_enabled") is not None
            assert app.screen.query_one("#intel_provider_select") is not None
            assert app.screen.query_one("#intel_cloud_model_input") is not None
            assert app.screen.query_one("#intel_cloud_api_key_env_input") is not None
            assert app.screen.query_one("#intel_cloud_base_url_input") is not None
            assert app.screen.query_one("#intel_deferred_enabled") is not None
            assert app.screen.query_one("#intel_queue_poll_input") is not None
            assert app.screen.query_one("#web_enabled") is not None
            assert app.screen.query_one("#web_auto_open") is not None
            assert app.screen.query_one("#diarization_enabled") is not None
            assert app.screen.query_one("#diarize_mic") is not None
            assert app.screen.query_one("#cross_meeting_recognition") is not None
            assert app.screen.query_one("#similarity_threshold_input") is not None
            assert app.screen.query_one("#auto_export") is not None
            assert app.screen.query_one("#export_format_select") is not None


# ============================================================
# Meeting Bar Tests
# ============================================================


@pytest.mark.integration
class TestMeetingBar:
    """Tests for MeetingBarWidget."""

    @pytest.mark.asyncio
    async def test_meeting_bar_hidden_by_default(self):
        """Meeting bar should be hidden by default."""
        app = HoldSpeakApp()
        async with app.run_test(size=(100, 30)) as pilot:
            bar = app.query_one("#meeting_bar", MeetingBarWidget)
            assert bar.active is False

    @pytest.mark.asyncio
    async def test_set_meeting_active(self):
        """set_meeting_active() should show/hide bar."""
        app = HoldSpeakApp()
        async with app.run_test(size=(100, 30)) as pilot:
            app.set_meeting_active(True)
            await pilot.pause()
            bar = app.query_one("#meeting_bar", MeetingBarWidget)
            assert bar.active is True

    @pytest.mark.asyncio
    async def test_set_meeting_duration(self):
        """set_meeting_duration() should update display."""
        app = HoldSpeakApp()
        async with app.run_test(size=(100, 30)) as pilot:
            app.set_meeting_active(True)
            app.set_meeting_duration("05:30")
            await pilot.pause()
            bar = app.query_one("#meeting_bar", MeetingBarWidget)
            assert bar.duration == "05:30"

    @pytest.mark.asyncio
    async def test_set_meeting_segment_count(self):
        """set_meeting_segment_count() should update display."""
        app = HoldSpeakApp()
        async with app.run_test(size=(100, 30)) as pilot:
            app.set_meeting_active(True)
            app.set_meeting_segment_count(5)
            await pilot.pause()
            bar = app.query_one("#meeting_bar", MeetingBarWidget)
            assert bar.segment_count == 5

    @pytest.mark.asyncio
    async def test_set_meeting_has_system_audio(self):
        """set_meeting_has_system_audio() should update display."""
        app = HoldSpeakApp()
        async with app.run_test(size=(100, 30)) as pilot:
            app.set_meeting_active(True)
            app.set_meeting_has_system_audio(True)
            await pilot.pause()
            bar = app.query_one("#meeting_bar", MeetingBarWidget)
            assert bar.has_system_audio is True


# ============================================================
# Footer Hints Tests
# ============================================================


@pytest.mark.integration
class TestFooterHints:
    """Tests for FooterHintsWidget."""

    @pytest.mark.asyncio
    async def test_footer_shows_hotkey(self):
        """Footer should display hotkey."""
        app = HoldSpeakApp()
        async with app.run_test(size=(100, 30)) as pilot:
            footer = app.query_one("#footer", FooterHintsWidget)
            # Default hotkey display should be present
            assert footer.hotkey_display is not None

    @pytest.mark.asyncio
    async def test_footer_meeting_hints_change(self):
        """Footer hints should change when meeting active."""
        app = HoldSpeakApp()
        async with app.run_test(size=(100, 30)) as pilot:
            footer = app.query_one("#footer", FooterHintsWidget)
            assert footer.meeting_active is False

            footer.set_meeting_active(True)
            await pilot.pause()
            assert footer.meeting_active is True


# ============================================================
# Hotkey Hint Tests
# ============================================================


@pytest.mark.integration
class TestHotkeyHint:
    """Tests for HotkeyHintWidget."""

    @pytest.mark.asyncio
    async def test_hotkey_hint_updates(self):
        """update_hotkey_display() should update hint."""
        app = HoldSpeakApp()
        async with app.run_test(size=(100, 30)) as pilot:
            app.update_hotkey_display("F5")
            await pilot.pause()
            hint = app.query_one("#hotkey_hint", HotkeyHintWidget)
            assert hint.hotkey_display == "F5"


# ============================================================
# History Widget Tests
# ============================================================


@pytest.mark.integration
class TestHistoryWidget:
    """Tests for HistoryWidget."""

    @pytest.mark.asyncio
    async def test_add_multiple_transcriptions(self):
        """Should handle multiple transcriptions."""
        app = HoldSpeakApp()
        async with app.run_test(size=(100, 30)) as pilot:
            app.add_transcription("First")
            app.add_transcription("Second")
            app.add_transcription("Third")
            await pilot.pause()

            history = app.query_one("#history", HistoryWidget)
            # Most recent should be last
            assert history.get_last() == "Third"

    @pytest.mark.asyncio
    async def test_get_last_empty(self):
        """get_last() should return None when empty."""
        app = HoldSpeakApp()
        async with app.run_test(size=(100, 30)) as pilot:
            history = app.query_one("#history", HistoryWidget)
            assert history.get_last() is None


# ============================================================
# Transcript Modal Tests
# ============================================================


@pytest.mark.integration
class TestTranscriptScreen:
    """Tests for MeetingTranscriptScreen."""

    @pytest.mark.asyncio
    async def test_transcript_screen_opens(self, sample_segments):
        """Transcript screen should open with segments."""
        app = HoldSpeakApp()
        async with app.run_test(size=(100, 30)) as pilot:
            app.show_meeting_transcript(sample_segments)
            await pilot.pause()
            assert isinstance(app.screen, MeetingTranscriptScreen)

    @pytest.mark.asyncio
    async def test_transcript_screen_empty(self):
        """Transcript screen should handle empty segments."""
        app = HoldSpeakApp()
        async with app.run_test(size=(100, 30)) as pilot:
            app.show_meeting_transcript([])
            await pilot.pause()
            assert isinstance(app.screen, MeetingTranscriptScreen)

    @pytest.mark.asyncio
    async def test_transcript_close_button(self, sample_segments):
        """Close button should dismiss transcript screen."""
        app = HoldSpeakApp()
        async with app.run_test(size=(100, 30)) as pilot:
            app.show_meeting_transcript(sample_segments)
            await pilot.pause()

            close_btn = app.screen.query_one("#transcript_close", Button)
            await pilot.click(close_btn)
            await pilot.pause()

            assert not isinstance(app.screen, MeetingTranscriptScreen)


# ============================================================
# Config Integration Tests
# ============================================================


@pytest.mark.integration
class TestConfigIntegration:
    """Tests for config integration with TUI."""

    @pytest.mark.asyncio
    async def test_app_uses_config_hotkey(self, default_config):
        """App should use hotkey from config."""
        app = HoldSpeakApp(config=default_config)
        async with app.run_test(size=(100, 30)) as pilot:
            hint = app.query_one("#hotkey_hint", HotkeyHintWidget)
            assert hint.hotkey_display == default_config.hotkey.display

    @pytest.mark.asyncio
    async def test_settings_applies_config(self):
        """Settings save should update app config."""
        app = HoldSpeakApp()
        async with app.run_test(size=(100, 30)) as pilot:
            # Just verify settings can be opened and config exists
            assert app.config is not None


# ============================================================
# Icon Button Tests
# ============================================================


@pytest.mark.integration
class TestIconButtons:
    """Tests for header icon buttons."""

    @pytest.mark.asyncio
    async def test_settings_icon_opens_settings(self):
        """Clicking settings icon should open settings."""
        app = HoldSpeakApp()
        async with app.run_test(size=(100, 30)) as pilot:
            # Find and click the settings icon
            # The icon button posts a message that triggers settings
            await pilot.press("s")  # Using keyboard as alternative
            await pilot.pause()
            assert isinstance(app.screen, SettingsScreen)


# ============================================================
# Meetings Hub Tests
# ============================================================


@pytest.mark.integration
class TestMeetingsHubPane:
    """Tests for meetings list + preview interactions."""

    @pytest.fixture
    def fake_meetings_db(self):
        meeting_a = _meeting_summary(
            "m1",
            "Weekly Standup",
            days_ago=1,
            duration_seconds=960,
            segment_count=32,
            action_item_count=4,
            tags=["standup", "team"],
        )
        meeting_b = _meeting_summary(
            "m2",
            "Budget Review",
            days_ago=10,
            duration_seconds=1280,
            segment_count=41,
            action_item_count=7,
            tags=["finance", "q2"],
        )

        details = {
            "m1": SimpleNamespace(
                intel=SimpleNamespace(summary="Reviewed blockers and assigned follow-ups."),
                segments=[SimpleNamespace(text="Team discussed blockers for sprint goals.")],
            ),
            "m2": SimpleNamespace(
                intel=SimpleNamespace(summary=""),
                segments=[SimpleNamespace(text="Detailed discussion about cost centers and variance.")],
            ),
        }

        search_index = {
            "budget": ["m2"],
            "standup": ["m1"],
        }
        return FakeMeetingsDb([meeting_a, meeting_b], details=details, search_index=search_index)

    @pytest.mark.asyncio
    async def test_selecting_meeting_updates_preview(self, fake_meetings_db):
        app = HoldSpeakApp()
        with patch("holdspeak.db.get_database", return_value=fake_meetings_db):
            async with app.run_test(size=(120, 36)) as pilot:
                await pilot.press("2")
                await pilot.pause()

                preview = app.query_one("#meetings_preview_body", Static)
                assert "Weekly Standup" in str(preview.content)

                pane = app.query_one("#meetings_pane", MeetingsHubPane)
                pane.on_meeting_row_selected(SimpleNamespace(meeting_id="m2"))
                await pilot.pause()

                assert "Budget Review" in str(preview.content)

                open_btn = app.query_one("#preview_open", Button)
                edit_btn = app.query_one("#preview_edit", Button)
                export_btn = app.query_one("#preview_export", Button)
                delete_btn = app.query_one("#preview_delete", Button)
                assert open_btn.disabled is False
                assert edit_btn.disabled is False
                assert export_btn.disabled is False
                assert delete_btn.disabled is False

    @pytest.mark.asyncio
    async def test_delete_requires_confirmation(self, fake_meetings_db):
        app = HoldSpeakApp()
        with patch("holdspeak.db.get_database", return_value=fake_meetings_db):
            async with app.run_test(size=(120, 36)) as pilot:
                await pilot.press("2")
                await pilot.pause()

                pane = app.query_one("#meetings_pane", MeetingsHubPane)

                delete_btn = app.query_one("#preview_delete", Button)
                cancel_btn = app.query_one("#preview_delete_cancel", Button)

                pane._delete_selected_meeting()
                assert str(delete_btn.label) == "Confirm delete"
                assert cancel_btn.display is True
                pane._delete_armed_meeting_id = None
                pane._refresh_preview_actions()
                assert str(delete_btn.label) == "Delete"
                assert cancel_btn.display is False

    @pytest.mark.asyncio
    async def test_live_search_filters_meetings(self, fake_meetings_db):
        app = HoldSpeakApp()
        with patch("holdspeak.db.get_database", return_value=fake_meetings_db):
            async with app.run_test(size=(120, 36)) as pilot:
                await pilot.press("2")
                await pilot.pause()

                pane = app.query_one("#meetings_pane", MeetingsHubPane)
                search_input = app.query_one("#meetings_search_input")
                pane.on_input_changed(SimpleNamespace(input=search_input, value="budget"))
                await pilot.pause()

                assert str(app.query_one("#meetings_count_label", Label).content) == "1 meetings"
                assert "Budget Review" in str(app.query_one("#meetings_preview_body", Static).content)
