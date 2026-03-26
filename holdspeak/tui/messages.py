"""TUI message classes for cross-component communication."""

from textual.message import Message


class MeetingToggle(Message):
    """Posted when user wants to toggle meeting."""
    pass


class MeetingBookmark(Message):
    """Posted when user wants to add bookmark."""
    pass


class MeetingShowTranscript(Message):
    """Posted when user wants to see transcript."""
    pass


class MeetingEditMetadata(Message):
    """Posted when user wants to edit meeting metadata."""
    pass


class MeetingMetadataSaved(Message):
    """Posted when metadata is saved from modal."""

    def __init__(self, title: str, tags: list[str]) -> None:
        super().__init__()
        self.title = title
        self.tags = tags


class MeetingOpenWeb(Message):
    """Posted when user wants to open the web dashboard."""
    pass


# === Voice typing intents (focused-only control path) ===


class VoiceTypingStartRecording(Message):
    """Start voice typing recording (focused-only control path)."""
    pass


class VoiceTypingStopRecording(Message):
    """Stop voice typing recording and transcribe (focused-only control path)."""
    pass


# === Navigation / persistence intents (saved meetings, speakers) ===


class SavedMeetingOpenDetail(Message):
    """Open the detail view for a saved meeting."""

    def __init__(self, meeting_id: str) -> None:
        super().__init__()
        self.meeting_id = meeting_id


class SavedMeetingEditMetadata(Message):
    """Edit metadata for a saved meeting."""

    def __init__(self, meeting_id: str) -> None:
        super().__init__()
        self.meeting_id = meeting_id


class SavedMeetingExport(Message):
    """Export a saved meeting to a file."""

    def __init__(self, meeting_id: str) -> None:
        super().__init__()
        self.meeting_id = meeting_id


class SavedMeetingDelete(Message):
    """Delete a saved meeting."""

    def __init__(self, meeting_id: str) -> None:
        super().__init__()
        self.meeting_id = meeting_id


class SpeakerOpenProfile(Message):
    """Open the profile view for a recognized speaker."""

    def __init__(self, speaker_id: str) -> None:
        super().__init__()
        self.speaker_id = speaker_id
