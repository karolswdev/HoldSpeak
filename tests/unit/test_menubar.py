"""Comprehensive unit tests for the menubar module."""

from __future__ import annotations

import sys
import threading
from collections import deque
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest


# ============================================================
# Module-level mock setup
# ============================================================

# Create comprehensive mock for rumps module BEFORE any imports
mock_rumps_module = MagicMock()
mock_rumps_module.notification = MagicMock()
mock_rumps_module.quit_application = MagicMock()


# Create a proper base class for App that won't cause issues
class MockRumpsApp:
    """Mock base class for rumps.App."""

    def __init__(self, name="", title="", quit_button=None):
        self.name = name
        self.title = title
        self.quit_button = quit_button
        self.menu = []


# Set the mock App class
mock_rumps_module.App = MockRumpsApp
mock_rumps_module.MenuItem = MagicMock

# Install mock in sys.modules before importing menubar
sys.modules["rumps"] = mock_rumps_module


# Now we can safely import the menubar module
from holdspeak.menubar import (
    RecentTranscription,
    HoldSpeakMenuBar,
    TITLE_IDLE,
    TITLE_RECORDING,
    TITLE_PROCESSING,
    TITLE_MEETING,
    ICON_IDLE,
    ICON_RECORDING,
    ICON_PROCESSING,
)
from holdspeak.config import Config


# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def mock_config():
    """Create a default Config object."""
    return Config()


@pytest.fixture
def mock_app(mock_config):
    """Create a HoldSpeakMenuBar instance with mocked dependencies."""
    # Create instance by calling __new__ and manually initializing
    app = object.__new__(HoldSpeakMenuBar)

    # Initialize base class attributes
    app.name = "HoldSpeak"
    app.title = TITLE_IDLE
    app.quit_button = None
    app.menu = []

    # Initialize required attributes
    app.config = mock_config
    app._state = "idle"
    app._is_recording = False
    app._transcription_lock = threading.Lock()
    app._recent = deque(maxlen=10)
    app._meeting_session = None
    app._meeting_timer_thread = None
    app._meeting_stop_timer = threading.Event()

    # Mock UI components
    app._status_item = MagicMock()
    app._record_item = MagicMock()
    app._recent_menu = MagicMock()
    app._meeting_menu = MagicMock()
    app._meeting_start_item = MagicMock()
    app._meeting_stop_item = MagicMock()
    app._meeting_dashboard_item = MagicMock()

    # Mock core components
    app._transcriber = MagicMock()
    app._transcriber_model = "base"
    app._recorder = MagicMock()
    app._typer = MagicMock()
    app._hotkey_listener = MagicMock()

    return app


# ============================================================
# RecentTranscription Tests
# ============================================================


class TestRecentTranscription:
    """Tests for RecentTranscription dataclass."""

    def test_preview_short_text(self):
        """preview returns full text when under 40 chars."""
        transcription = RecentTranscription(
            text="Short text",
            timestamp=datetime.now(),
        )
        assert transcription.preview == "Short text"

    def test_preview_exact_40_chars(self):
        """preview returns full text when exactly 40 chars."""
        text = "A" * 40
        transcription = RecentTranscription(text=text, timestamp=datetime.now())
        assert transcription.preview == text
        assert len(transcription.preview) == 40

    def test_preview_truncates_long_text(self):
        """preview truncates text over 40 chars with ellipsis."""
        text = "A" * 50
        transcription = RecentTranscription(text=text, timestamp=datetime.now())
        assert transcription.preview == "A" * 40 + "..."
        assert len(transcription.preview) == 43

    def test_preview_strips_whitespace(self):
        """preview strips leading/trailing whitespace before truncating."""
        transcription = RecentTranscription(
            text="   Short text   ",
            timestamp=datetime.now(),
        )
        assert transcription.preview == "Short text"

    def test_preview_very_long_text(self):
        """preview handles very long text correctly."""
        text = "A" * 500
        transcription = RecentTranscription(text=text, timestamp=datetime.now())
        assert len(transcription.preview) == 43
        assert transcription.preview.endswith("...")

    def test_time_str_format(self):
        """time_str returns HH:MM format."""
        transcription = RecentTranscription(
            text="Test",
            timestamp=datetime(2024, 1, 15, 10, 30, 45),
        )
        assert transcription.time_str == "10:30"

    def test_time_str_midnight(self):
        """time_str handles midnight correctly."""
        transcription = RecentTranscription(
            text="Test",
            timestamp=datetime(2024, 1, 15, 0, 0, 0),
        )
        assert transcription.time_str == "00:00"

    def test_time_str_noon(self):
        """time_str handles noon correctly."""
        transcription = RecentTranscription(
            text="Test",
            timestamp=datetime(2024, 1, 15, 12, 0, 0),
        )
        assert transcription.time_str == "12:00"

    def test_time_str_single_digit_minutes(self):
        """time_str pads single digit minutes with zero."""
        transcription = RecentTranscription(
            text="Test",
            timestamp=datetime(2024, 1, 15, 9, 5, 0),
        )
        assert transcription.time_str == "09:05"

    def test_empty_text(self):
        """preview handles empty text."""
        transcription = RecentTranscription(text="", timestamp=datetime.now())
        assert transcription.preview == ""

    def test_whitespace_only_text(self):
        """preview handles whitespace-only text."""
        transcription = RecentTranscription(text="   \t\n   ", timestamp=datetime.now())
        assert transcription.preview == ""

    def test_newline_in_text(self):
        """preview handles text with newlines."""
        transcription = RecentTranscription(
            text="Line 1\nLine 2\nLine 3",
            timestamp=datetime.now(),
        )
        # Strip only removes leading/trailing whitespace
        assert transcription.preview == "Line 1\nLine 2\nLine 3"

    def test_unicode_text(self):
        """preview handles unicode characters."""
        transcription = RecentTranscription(
            text="Hello world! Cafe latte. Emoji test.",
            timestamp=datetime.now(),
        )
        assert len(transcription.preview) <= 43


# ============================================================
# HoldSpeakMenuBar Initialization Tests
# ============================================================


class TestHoldSpeakMenuBarInitialization:
    """Tests for HoldSpeakMenuBar initialization."""

    def test_initial_state(self, mock_app):
        """App starts in expected initial state."""
        assert mock_app._state == "idle"
        assert mock_app._is_recording is False
        assert len(mock_app._recent) == 0
        assert mock_app._meeting_session is None

    def test_recent_deque_max_size(self, mock_app):
        """_recent deque has maxlen of 10."""
        # Add 15 items
        for i in range(15):
            mock_app._recent.append(f"item_{i}")

        # Should only keep last 10
        assert len(mock_app._recent) == 10
        assert mock_app._recent[0] == "item_5"
        assert mock_app._recent[-1] == "item_14"

    def test_config_is_set(self, mock_app, mock_config):
        """App has config object set."""
        assert mock_app.config is not None
        assert isinstance(mock_app.config, Config)


# ============================================================
# State Transition Tests
# ============================================================


class TestStateTransitions:
    """Tests for HoldSpeakMenuBar state transitions."""

    def test_set_state_idle(self, mock_app):
        """_set_state('idle') updates title and status correctly."""
        mock_app._set_state("idle")

        assert mock_app._state == "idle"
        assert mock_app.title == TITLE_IDLE
        assert mock_app._status_item.title == "Status: Ready"

    def test_set_state_recording(self, mock_app):
        """_set_state('recording') updates title and status correctly."""
        mock_app._set_state("recording")

        assert mock_app._state == "recording"
        assert mock_app.title == TITLE_RECORDING
        assert mock_app._status_item.title == "Status: Recording..."
        assert mock_app._record_item.title == "Stop Recording"

    def test_set_state_processing(self, mock_app):
        """_set_state('processing') updates title and status correctly."""
        mock_app._set_state("processing")

        assert mock_app._state == "processing"
        assert mock_app.title == TITLE_PROCESSING
        assert mock_app._status_item.title == "Status: Processing..."
        assert mock_app._record_item.title == "Processing..."

    def test_set_state_meeting(self, mock_app):
        """_set_state('meeting') updates title and status correctly."""
        mock_app._set_state("meeting")

        assert mock_app._state == "meeting"
        assert mock_app.title == TITLE_MEETING
        assert mock_app._status_item.title == "Status: Meeting in progress"

    def test_state_transition_idle_to_recording(self, mock_app):
        """State transitions from idle to recording."""
        mock_app._set_state("idle")
        assert mock_app._state == "idle"

        mock_app._set_state("recording")
        assert mock_app._state == "recording"

    def test_state_transition_recording_to_processing(self, mock_app):
        """State transitions from recording to processing."""
        mock_app._set_state("recording")
        assert mock_app._state == "recording"

        mock_app._set_state("processing")
        assert mock_app._state == "processing"

    def test_state_transition_processing_to_idle(self, mock_app):
        """State transitions from processing back to idle."""
        mock_app._set_state("processing")
        assert mock_app._state == "processing"

        mock_app._set_state("idle")
        assert mock_app._state == "idle"

    def test_rapid_state_changes(self, mock_app):
        """Handle rapid state changes without errors."""
        for _ in range(50):
            mock_app._set_state("idle")
            mock_app._set_state("recording")
            mock_app._set_state("processing")
            mock_app._set_state("meeting")

        # Should end in meeting state without errors
        assert mock_app._state == "meeting"


# ============================================================
# Recent Transcriptions Tests
# ============================================================


class TestRecentTranscriptions:
    """Tests for recent transcriptions management."""

    def test_add_recent_to_empty_deque(self, mock_app):
        """Adding to empty deque works correctly."""
        entry = RecentTranscription(text="Test", timestamp=datetime.now())
        mock_app._recent.appendleft(entry)

        assert len(mock_app._recent) == 1
        assert mock_app._recent[0].text == "Test"

    def test_add_recent_preserves_order(self, mock_app):
        """New entries are added at the front (appendleft)."""
        entry1 = RecentTranscription(text="First", timestamp=datetime.now())
        entry2 = RecentTranscription(text="Second", timestamp=datetime.now())
        entry3 = RecentTranscription(text="Third", timestamp=datetime.now())

        mock_app._recent.appendleft(entry1)
        mock_app._recent.appendleft(entry2)
        mock_app._recent.appendleft(entry3)

        # Newest should be first
        assert mock_app._recent[0].text == "Third"
        assert mock_app._recent[1].text == "Second"
        assert mock_app._recent[2].text == "First"

    def test_add_recent_respects_max_size(self, mock_app):
        """Adding more than maxlen items drops oldest."""
        # Add 15 items (maxlen is 10)
        for i in range(15):
            entry = RecentTranscription(text=f"Entry {i}", timestamp=datetime.now())
            mock_app._recent.appendleft(entry)

        assert len(mock_app._recent) == 10
        # Newest should be Entry 14
        assert mock_app._recent[0].text == "Entry 14"
        # Oldest should be Entry 5 (0-4 were pushed out)
        assert mock_app._recent[-1].text == "Entry 5"

    def test_update_recent_menu_empty(self, mock_app):
        """_update_recent_menu handles empty deque."""
        mock_app._update_recent_menu()

        mock_app._recent_menu.clear.assert_called_once()
        mock_app._recent_menu.add.assert_called()

    def test_update_recent_menu_with_entries(self, mock_app):
        """_update_recent_menu builds menu items correctly."""
        # Add some entries
        mock_app._recent.appendleft(
            RecentTranscription(text="Test 1", timestamp=datetime(2024, 1, 15, 10, 30))
        )
        mock_app._recent.appendleft(
            RecentTranscription(text="Test 2", timestamp=datetime(2024, 1, 15, 10, 35))
        )

        mock_app._update_recent_menu()

        mock_app._recent_menu.clear.assert_called_once()
        # Should add menu items for each entry + separator + clear option
        assert mock_app._recent_menu.add.call_count >= 2

    def test_clear_recent_empties_deque(self, mock_app):
        """_clear_recent empties the recent deque."""
        # Add some entries
        mock_app._recent.append(
            RecentTranscription(text="Test", timestamp=datetime.now())
        )
        assert len(mock_app._recent) == 1

        mock_app._clear_recent(MagicMock())

        assert len(mock_app._recent) == 0


# ============================================================
# Copy to Clipboard Tests
# ============================================================


class TestCopyToClipboard:
    """Tests for clipboard copy functionality."""

    def test_make_copy_callback_returns_callable(self, mock_app):
        """_make_copy_callback returns a callable."""
        callback = mock_app._make_copy_callback("Test text")
        assert callable(callback)

    def test_make_copy_callback_copies_text(self, mock_app):
        """_make_copy_callback copies text to clipboard when called."""
        with patch("pyperclip.copy") as mock_copy:
            callback = mock_app._make_copy_callback("Test text")
            callback(MagicMock())

            mock_copy.assert_called_once_with("Test text")

    def test_make_copy_callback_shows_notification(self, mock_app):
        """_make_copy_callback shows notification after copying."""
        with patch("pyperclip.copy"):
            mock_rumps_module.notification.reset_mock()
            callback = mock_app._make_copy_callback("Test text")
            callback(MagicMock())

            mock_rumps_module.notification.assert_called_once()


# ============================================================
# Recording Tests
# ============================================================


class TestRecording:
    """Tests for recording functionality."""

    def test_start_recording_sets_is_recording(self, mock_app):
        """_start_recording sets _is_recording to True."""
        mock_app._start_recording()

        assert mock_app._is_recording is True
        mock_app._recorder.start_recording.assert_called_once()

    def test_start_recording_changes_state(self, mock_app):
        """_start_recording changes state to 'recording'."""
        mock_app._start_recording()

        assert mock_app._state == "recording"

    def test_start_recording_no_recorder(self, mock_app):
        """_start_recording does nothing if recorder is None."""
        mock_app._recorder = None
        mock_app._is_recording = False

        mock_app._start_recording()

        assert mock_app._is_recording is False

    def test_on_hotkey_press_idle_state(self, mock_app):
        """_on_hotkey_press starts recording in idle state."""
        mock_app._state = "idle"

        mock_app._on_hotkey_press()

        assert mock_app._is_recording is True

    def test_on_hotkey_press_processing_state(self, mock_app):
        """_on_hotkey_press does nothing in processing state."""
        mock_app._state = "processing"
        mock_app._is_recording = False

        mock_app._on_hotkey_press()

        assert mock_app._is_recording is False

    def test_on_hotkey_press_meeting_state(self, mock_app):
        """_on_hotkey_press starts recording in meeting state."""
        mock_app._state = "meeting"

        mock_app._on_hotkey_press()

        assert mock_app._is_recording is True

    def test_on_hotkey_press_recording_state(self, mock_app):
        """_on_hotkey_press does nothing in recording state."""
        mock_app._state = "recording"
        mock_app._is_recording = True

        # Reset the mock to track new calls
        mock_app._recorder.start_recording.reset_mock()

        mock_app._on_hotkey_press()

        # Should not call start_recording again
        mock_app._recorder.start_recording.assert_not_called()


# ============================================================
# Hotkey Release Tests
# ============================================================


class TestOnHotkeyRelease:
    """Tests for hotkey release functionality."""

    def test_on_hotkey_release_not_recording(self, mock_app):
        """_on_hotkey_release does nothing if not recording."""
        mock_app._is_recording = False

        with patch.object(mock_app, "_stop_recording_and_transcribe") as mock_stop:
            mock_app._on_hotkey_release()
            mock_stop.assert_not_called()

    def test_on_hotkey_release_while_recording(self, mock_app):
        """_on_hotkey_release calls stop when recording."""
        mock_app._is_recording = True

        with patch.object(mock_app, "_stop_recording_and_transcribe") as mock_stop:
            mock_app._on_hotkey_release()
            mock_stop.assert_called_once()


# ============================================================
# Toggle Recording Tests
# ============================================================


class TestToggleRecording:
    """Tests for toggle recording functionality."""

    def test_toggle_recording_from_idle(self, mock_app):
        """_toggle_recording starts recording from idle state."""
        mock_app._state = "idle"
        mock_app._is_recording = False

        mock_app._toggle_recording(MagicMock())

        assert mock_app._is_recording is True

    def test_toggle_recording_while_recording(self, mock_app):
        """_toggle_recording stops recording when already recording."""
        mock_app._state = "recording"
        mock_app._is_recording = True

        with patch.object(mock_app, "_stop_recording_and_transcribe") as mock_stop:
            mock_app._toggle_recording(MagicMock())
            mock_stop.assert_called_once()

    def test_toggle_recording_from_meeting(self, mock_app):
        """_toggle_recording starts recording from meeting state."""
        mock_app._state = "meeting"
        mock_app._is_recording = False

        mock_app._toggle_recording(MagicMock())

        assert mock_app._is_recording is True


# ============================================================
# Meeting Mode Tests
# ============================================================


class TestMeetingMode:
    """Tests for meeting mode functionality."""

    def test_start_meeting_without_transcriber(self, mock_app):
        """_start_meeting shows error if transcriber not ready."""
        mock_app._transcriber = None

        mock_rumps_module.notification.reset_mock()
        mock_app._start_meeting(MagicMock())

        mock_rumps_module.notification.assert_called_once()
        call_args = mock_rumps_module.notification.call_args
        assert "Error" in str(call_args)

    def test_stop_meeting_when_no_meeting(self, mock_app):
        """_stop_meeting does nothing if no meeting session."""
        mock_app._meeting_session = None

        mock_app._stop_meeting(MagicMock())

        # Should return early without error
        assert mock_app._meeting_session is None

    def test_open_dashboard_when_no_meeting(self, mock_app):
        """_open_dashboard does nothing if no meeting session."""
        mock_app._meeting_session = None

        with patch("webbrowser.open") as mock_open:
            mock_app._open_dashboard(MagicMock())
            mock_open.assert_not_called()

    def test_open_dashboard_with_meeting(self, mock_app):
        """_open_dashboard opens browser when meeting has URL."""
        mock_session = MagicMock()
        mock_state = MagicMock()
        mock_state.web_url = "http://localhost:8080"
        mock_session.state = mock_state
        mock_app._meeting_session = mock_session

        with patch("webbrowser.open") as mock_open:
            mock_app._open_dashboard(MagicMock())
            mock_open.assert_called_once_with("http://localhost:8080")

    def test_open_dashboard_with_no_url(self, mock_app):
        """_open_dashboard does nothing if meeting has no URL."""
        mock_session = MagicMock()
        mock_state = MagicMock()
        mock_state.web_url = None
        mock_session.state = mock_state
        mock_app._meeting_session = mock_session

        with patch("webbrowser.open") as mock_open:
            mock_app._open_dashboard(MagicMock())
            mock_open.assert_not_called()


# ============================================================
# Quit Functionality Tests
# ============================================================


class TestQuitFunctionality:
    """Tests for quit functionality."""

    def test_quit_stops_hotkey_listener(self, mock_app):
        """_quit stops the hotkey listener."""
        mock_rumps_module.quit_application.reset_mock()

        mock_app._quit(MagicMock())

        mock_app._hotkey_listener.stop.assert_called_once()
        mock_rumps_module.quit_application.assert_called_once()

    def test_quit_without_hotkey_listener(self, mock_app):
        """_quit handles missing hotkey listener gracefully."""
        mock_app._hotkey_listener = None
        mock_rumps_module.quit_application.reset_mock()

        mock_app._quit(MagicMock())

        mock_rumps_module.quit_application.assert_called_once()

    def test_quit_stops_active_meeting(self, mock_app):
        """_quit stops active meeting session."""
        mock_session = MagicMock()
        mock_session.is_active = True
        mock_app._meeting_session = mock_session
        mock_rumps_module.quit_application.reset_mock()

        mock_app._quit(MagicMock())

        mock_session.stop.assert_called_once()
        mock_rumps_module.quit_application.assert_called_once()


# ============================================================
# Update Status Tests
# ============================================================


class TestUpdateStatus:
    """Tests for status update functionality."""

    def test_update_status(self, mock_app):
        """_update_status updates status item title."""
        mock_app._update_status("Test Status")

        assert mock_app._status_item.title == "Status: Test Status"

    def test_update_status_ready(self, mock_app):
        """_update_status sets correct ready status."""
        mock_app._update_status("Ready")

        assert mock_app._status_item.title == "Status: Ready"

    def test_update_status_loading(self, mock_app):
        """_update_status sets correct loading status."""
        mock_app._update_status("Loading model...")

        assert mock_app._status_item.title == "Status: Loading model..."


# ============================================================
# Constants Tests
# ============================================================


class TestConstants:
    """Tests for module constants."""

    def test_title_constants(self):
        """Verify title constants have correct values."""
        assert TITLE_IDLE == "HoldSpeak"
        assert TITLE_RECORDING == "Recording..."
        assert TITLE_PROCESSING == "Processing..."
        assert TITLE_MEETING == "Meeting"

    def test_icon_constants(self):
        """Verify icon constants have correct values."""
        assert ICON_IDLE == "mic"
        assert ICON_RECORDING == "mic.fill"
        assert ICON_PROCESSING == "mic.badge.ellipsis"


# ============================================================
# Short Recording Edge Case Tests
# ============================================================


class TestShortRecordingHandling:
    """Tests for handling short/empty recordings."""

    def test_stop_recording_short_audio_ignored(self, mock_app):
        """Short recordings (< 0.1s) are ignored."""
        # Return very short audio (less than 1600 samples at 16kHz = 0.1s)
        mock_app._recorder.stop_recording.return_value = b"\x00" * 1000
        mock_app._is_recording = True
        mock_app._state = "recording"

        mock_app._stop_recording_and_transcribe()

        # Should return to idle state
        assert mock_app._state == "idle"

    def test_stop_recording_no_recorder(self, mock_app):
        """_stop_recording_and_transcribe handles missing recorder."""
        mock_app._recorder = None
        mock_app._is_recording = True

        # Should not raise
        mock_app._stop_recording_and_transcribe()


# ============================================================
# Open Settings Tests
# ============================================================


class TestOpenSettings:
    """Tests for settings functionality."""

    def test_open_settings_shows_notification(self, mock_app):
        """_open_settings shows notification about config location."""
        mock_rumps_module.notification.reset_mock()

        with patch("os.path.exists", return_value=False):
            mock_app._open_settings(MagicMock())

        mock_rumps_module.notification.assert_called_once()

    def test_open_settings_opens_config_file(self, mock_app):
        """_open_settings opens config file if it exists."""
        with patch("os.path.exists", return_value=True):
            with patch("subprocess.run") as mock_run:
                mock_app._open_settings(MagicMock())
                mock_run.assert_called_once()


# ============================================================
# Open TUI Tests
# ============================================================


class TestOpenTUI:
    """Tests for TUI launch functionality."""

    def test_open_tui_runs_osascript(self, mock_app):
        """_open_tui runs osascript to open Terminal."""
        with patch("subprocess.run") as mock_run:
            mock_app._open_tui(MagicMock())

            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert call_args[0] == "osascript"
            assert "-e" in call_args


# ============================================================
# Error Handling Tests
# ============================================================


class TestErrorHandling:
    """Tests for error handling in various operations."""

    def test_start_recording_handles_exception(self, mock_app):
        """_start_recording handles exceptions gracefully."""
        mock_app._recorder.start_recording.side_effect = Exception("Audio error")
        mock_rumps_module.notification.reset_mock()

        mock_app._start_recording()

        # Should show notification
        mock_rumps_module.notification.assert_called_once()
        # Should not set is_recording
        assert mock_app._is_recording is False
