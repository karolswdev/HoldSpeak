"""Centralized UI state management for HoldSpeak TUI."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class MeetingUIState:
    """Meeting-specific UI state.

    Attributes:
        active: Whether a meeting is currently in progress.
        duration: Formatted duration string (MM:SS or HH:MM:SS).
        segment_count: Number of transcript segments.
        has_system_audio: Whether system audio capture is enabled.
        mic_level: Microphone audio level (0.0-1.0).
        system_level: System audio level (0.0-1.0).
        title: Meeting title.
        tags: List of meeting tags.
        web_url: Web dashboard URL if web server is running.
    """
    active: bool = False
    duration: str = "00:00"
    segment_count: int = 0
    has_system_audio: bool = False
    mic_level: float = 0.0
    system_level: float = 0.0
    title: str = ""
    tags: list[str] = field(default_factory=list)
    web_url: str = ""

    def reset(self) -> None:
        """Reset meeting state to defaults."""
        self.active = False
        self.duration = "00:00"
        self.segment_count = 0
        self.has_system_audio = False
        self.mic_level = 0.0
        self.system_level = 0.0
        self.title = ""
        self.tags = []
        self.web_url = ""


@dataclass
class AppUIState:
    """Complete application UI state.

    This is the single source of truth for all UI state. Widgets observe
    this state and update reactively when it changes.

    Attributes:
        mode: Current mode - 'voice_typing' or 'meeting'.
        status: Current status - 'idle', 'recording', 'transcribing', 'loading', 'error'.
        hotkey_display: Display string for the global hotkey (e.g., '⌥R').
        audio_level: Audio meter level (0.0-1.0).
        meeting: Nested meeting state.
        error_message: Error message to display, if any.
        active_tab: Currently active tab - 'voice_typing' or 'meetings'.
    """
    mode: str = "voice_typing"
    status: str = "idle"
    hotkey_display: str = "⌥R"
    audio_level: float = 0.0
    meeting: MeetingUIState = field(default_factory=MeetingUIState)
    error_message: Optional[str] = None
    active_tab: str = "voice_typing"
    global_hotkey_enabled: bool = True
    global_hotkey_disabled_reason: str = ""
    text_injection_enabled: bool = True
    text_injection_disabled_reason: str = ""
    focused_hold_to_talk_key: str = "v"

    @property
    def is_meeting_mode(self) -> bool:
        """Whether the app is in meeting mode."""
        return self.mode == "meeting"

    @property
    def is_idle(self) -> bool:
        """Whether the app is idle (not recording or transcribing)."""
        return self.status == "idle"

    @property
    def is_recording(self) -> bool:
        """Whether the app is currently recording."""
        return self.status == "recording"

    @property
    def is_transcribing(self) -> bool:
        """Whether the app is currently transcribing."""
        return self.status == "transcribing"

    def set_recording(self) -> None:
        """Set status to recording."""
        self.status = "recording"
        self.error_message = None

    def set_transcribing(self) -> None:
        """Set status to transcribing."""
        self.status = "transcribing"
        self.error_message = None

    def set_idle(self) -> None:
        """Set status to idle."""
        self.status = "idle"
        self.error_message = None

    def set_loading(self) -> None:
        """Set status to loading."""
        self.status = "loading"
        self.error_message = None

    def set_error(self, message: str) -> None:
        """Set status to error with message."""
        self.status = "error"
        self.error_message = message

    def start_meeting(self, has_system_audio: bool = False, web_url: str = "") -> None:
        """Transition to meeting mode."""
        self.mode = "meeting"
        self.meeting.active = True
        self.meeting.has_system_audio = has_system_audio
        self.meeting.web_url = web_url
        self.meeting.duration = "00:00"
        self.meeting.segment_count = 0

    def stop_meeting(self) -> None:
        """Transition out of meeting mode."""
        self.mode = "voice_typing"
        self.meeting.reset()
