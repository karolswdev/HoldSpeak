"""Unit tests for meeting state data structures."""

from __future__ import annotations

from datetime import datetime
import pytest

from holdspeak.meeting_session import (
    TranscriptSegment,
    Bookmark,
    MeetingState,
    IntelSnapshot,
)


class TestTranscriptSegment:
    """Tests for TranscriptSegment dataclass."""

    # ============================================================
    # Creation Tests
    # ============================================================

    def test_creation(self) -> None:
        """TranscriptSegment can be created with required fields."""
        segment = TranscriptSegment(
            text="Hello world",
            speaker="Me",
            start_time=0.0,
            end_time=5.0,
        )
        assert segment.text == "Hello world"
        assert segment.speaker == "Me"
        assert segment.start_time == 0.0
        assert segment.end_time == 5.0
        assert segment.is_bookmarked is False

    def test_creation_with_bookmark(self) -> None:
        """TranscriptSegment can be created with bookmark flag."""
        segment = TranscriptSegment(
            text="Important point",
            speaker="Remote",
            start_time=10.0,
            end_time=15.0,
            is_bookmarked=True,
        )
        assert segment.is_bookmarked is True

    def test_creation_from_fixture(self, sample_segments) -> None:
        """Sample segments fixture creates valid TranscriptSegments."""
        assert len(sample_segments) == 3
        assert sample_segments[0].speaker == "Me"
        assert sample_segments[1].speaker == "Remote"

    # ============================================================
    # Properties Tests
    # ============================================================

    def test_duration_property(self) -> None:
        """duration property returns end_time - start_time."""
        segment = TranscriptSegment(
            text="Test",
            speaker="Me",
            start_time=5.0,
            end_time=12.5,
        )
        assert segment.duration == 7.5

    def test_duration_zero(self) -> None:
        """duration is zero when start_time equals end_time."""
        segment = TranscriptSegment(
            text="Test",
            speaker="Me",
            start_time=5.0,
            end_time=5.0,
        )
        assert segment.duration == 0.0

    # ============================================================
    # to_dict Tests
    # ============================================================

    def test_to_dict(self) -> None:
        """to_dict returns correct dictionary representation."""
        segment = TranscriptSegment(
            text="Let's discuss the project.",
            speaker="Me",
            start_time=0.0,
            end_time=5.2,
            is_bookmarked=False,
        )
        result = segment.to_dict()

        assert result == {
            "text": "Let's discuss the project.",
            "speaker": "Me",
            "speaker_id": None,
            "start_time": 0.0,
            "end_time": 5.2,
            "is_bookmarked": False,
        }

    def test_to_dict_with_bookmark(self) -> None:
        """to_dict includes is_bookmarked flag."""
        segment = TranscriptSegment(
            text="Key decision",
            speaker="Remote",
            start_time=10.0,
            end_time=15.0,
            is_bookmarked=True,
        )
        result = segment.to_dict()
        assert result["is_bookmarked"] is True

    # ============================================================
    # String Representation Tests
    # ============================================================

    def test_format_timestamp(self) -> None:
        """format_timestamp returns HH:MM:SS format."""
        segment = TranscriptSegment(
            text="Test",
            speaker="Me",
            start_time=3661.0,  # 1 hour, 1 minute, 1 second
            end_time=3665.0,
        )
        assert segment.format_timestamp() == "01:01:01"

    def test_format_timestamp_zero(self) -> None:
        """format_timestamp at start of meeting."""
        segment = TranscriptSegment(
            text="Test",
            speaker="Me",
            start_time=0.0,
            end_time=5.0,
        )
        assert segment.format_timestamp() == "00:00:00"

    def test_str_representation(self) -> None:
        """__str__ returns formatted string."""
        segment = TranscriptSegment(
            text="Hello everyone",
            speaker="Me",
            start_time=65.0,  # 1 minute, 5 seconds
            end_time=70.0,
        )
        result = str(segment)
        assert result == "[00:01:05] Me: Hello everyone"


class TestBookmark:
    """Tests for Bookmark dataclass."""

    # ============================================================
    # Creation Tests
    # ============================================================

    def test_creation_minimal(self) -> None:
        """Bookmark can be created with just timestamp."""
        bookmark = Bookmark(timestamp=45.5)
        assert bookmark.timestamp == 45.5
        assert bookmark.label == ""
        assert bookmark.created_at is not None

    def test_creation_with_label(self) -> None:
        """Bookmark can be created with label."""
        bookmark = Bookmark(timestamp=100.0, label="Important decision")
        assert bookmark.label == "Important decision"

    def test_creation_with_explicit_datetime(self) -> None:
        """Bookmark can be created with explicit datetime."""
        dt = datetime(2024, 6, 15, 14, 30, 0)
        bookmark = Bookmark(timestamp=30.0, label="Test", created_at=dt)
        assert bookmark.created_at == dt

    def test_creation_from_fixture(self, sample_bookmark) -> None:
        """Sample bookmark fixture creates valid Bookmark."""
        assert sample_bookmark.timestamp == 45.5
        assert sample_bookmark.label == "Important decision"

    # ============================================================
    # to_dict Tests
    # ============================================================

    def test_to_dict(self, sample_bookmark) -> None:
        """to_dict returns correct dictionary representation."""
        result = sample_bookmark.to_dict()

        assert result["timestamp"] == 45.5
        assert result["label"] == "Important decision"
        assert "created_at" in result
        # created_at should be ISO format string
        assert isinstance(result["created_at"], str)

    def test_to_dict_empty_label(self) -> None:
        """to_dict handles empty label."""
        bookmark = Bookmark(timestamp=10.0)
        result = bookmark.to_dict()
        assert result["label"] == ""

    def test_to_dict_created_at_iso_format(self) -> None:
        """to_dict serializes created_at as ISO format."""
        dt = datetime(2024, 1, 15, 10, 35, 45)
        bookmark = Bookmark(timestamp=30.0, created_at=dt)
        result = bookmark.to_dict()
        assert result["created_at"] == "2024-01-15T10:35:45"


class TestMeetingState:
    """Tests for MeetingState dataclass."""

    # ============================================================
    # Creation Tests
    # ============================================================

    def test_creation_minimal(self) -> None:
        """MeetingState can be created with required fields."""
        state = MeetingState(
            id="abc123",
            started_at=datetime.now(),
        )
        assert state.id == "abc123"
        assert state.ended_at is None
        assert state.title is None
        assert state.tags == []
        assert state.segments == []
        assert state.bookmarks == []
        assert state.intel is None

    def test_creation_from_fixture(self, sample_meeting_state) -> None:
        """Sample meeting state fixture creates valid MeetingState."""
        assert sample_meeting_state.id == "test-meeting-123"
        assert sample_meeting_state.mic_label == "Me"
        assert sample_meeting_state.remote_label == "Remote"

    # ============================================================
    # Properties Tests
    # ============================================================

    def test_is_active_true(self, sample_meeting_state) -> None:
        """is_active is True when ended_at is None."""
        assert sample_meeting_state.is_active is True

    def test_is_active_false(self, sample_meeting_state) -> None:
        """is_active is False when ended_at is set."""
        sample_meeting_state.ended_at = datetime.now()
        assert sample_meeting_state.is_active is False

    def test_duration_active_meeting(self) -> None:
        """duration calculates from started_at to now for active meeting."""
        # Create a meeting that started 10 seconds ago (approximately)
        start_time = datetime.now()
        state = MeetingState(id="test", started_at=start_time)
        # Duration should be very close to 0
        assert state.duration >= 0.0
        assert state.duration < 1.0  # Should be near-instant

    def test_duration_ended_meeting(self) -> None:
        """duration calculates from started_at to ended_at."""
        start = datetime(2024, 1, 15, 10, 0, 0)
        end = datetime(2024, 1, 15, 10, 30, 0)  # 30 minutes later
        state = MeetingState(id="test", started_at=start, ended_at=end)
        assert state.duration == 1800.0  # 30 minutes in seconds

    def test_format_duration_minutes(self) -> None:
        """format_duration shows MM:SS for short meetings."""
        start = datetime(2024, 1, 15, 10, 0, 0)
        end = datetime(2024, 1, 15, 10, 5, 30)  # 5 minutes 30 seconds
        state = MeetingState(id="test", started_at=start, ended_at=end)
        assert state.format_duration() == "05:30"

    def test_format_duration_hours(self) -> None:
        """format_duration shows HH:MM:SS for long meetings."""
        start = datetime(2024, 1, 15, 10, 0, 0)
        end = datetime(2024, 1, 15, 11, 15, 45)  # 1 hour 15 minutes 45 seconds
        state = MeetingState(id="test", started_at=start, ended_at=end)
        assert state.format_duration() == "01:15:45"

    # ============================================================
    # to_dict Tests
    # ============================================================

    def test_to_dict_minimal(self) -> None:
        """to_dict with minimal state."""
        start = datetime(2024, 1, 15, 10, 30, 0)
        state = MeetingState(id="test-123", started_at=start)
        result = state.to_dict()

        assert result["id"] == "test-123"
        assert result["started_at"] == "2024-01-15T10:30:00"
        assert result["ended_at"] is None
        assert result["title"] is None
        assert result["tags"] == []
        assert result["segments"] == []
        assert result["bookmarks"] == []
        assert result["intel"] is None

    def test_to_dict_with_segments(self, sample_segments) -> None:
        """to_dict includes serialized segments."""
        state = MeetingState(
            id="test",
            started_at=datetime(2024, 1, 15, 10, 0, 0),
            segments=sample_segments,
        )
        result = state.to_dict()

        assert len(result["segments"]) == 3
        assert result["segments"][0]["text"] == "Let's discuss the quarterly goals."
        assert result["segments"][0]["speaker"] == "Me"

    def test_to_dict_with_bookmarks(self, sample_bookmark) -> None:
        """to_dict includes serialized bookmarks."""
        state = MeetingState(
            id="test",
            started_at=datetime(2024, 1, 15, 10, 0, 0),
            bookmarks=[sample_bookmark],
        )
        result = state.to_dict()

        assert len(result["bookmarks"]) == 1
        assert result["bookmarks"][0]["timestamp"] == 45.5
        assert result["bookmarks"][0]["label"] == "Important decision"

    def test_to_dict_with_intel(self) -> None:
        """to_dict includes serialized intel snapshot."""
        intel = IntelSnapshot(
            timestamp=120.0,
            topics=["Budget", "Timeline"],
            action_items=[{"task": "Review budget", "owner": "Me", "due": "Friday"}],
            summary="Discussed project budget and timeline.",
        )
        state = MeetingState(
            id="test",
            started_at=datetime(2024, 1, 15, 10, 0, 0),
            intel=intel,
        )
        result = state.to_dict()

        assert result["intel"] is not None
        assert result["intel"]["topics"] == ["Budget", "Timeline"]

    def test_to_dict_includes_computed_fields(self) -> None:
        """to_dict includes duration and formatted_duration."""
        start = datetime(2024, 1, 15, 10, 0, 0)
        end = datetime(2024, 1, 15, 10, 10, 30)
        state = MeetingState(id="test", started_at=start, ended_at=end)
        result = state.to_dict()

        assert "duration" in result
        assert result["duration"] == 630.0  # 10 minutes 30 seconds
        assert "formatted_duration" in result
        assert result["formatted_duration"] == "10:30"

    def test_to_dict_includes_labels(self, sample_meeting_state) -> None:
        """to_dict includes mic_label and remote_label."""
        result = sample_meeting_state.to_dict()
        assert result["mic_label"] == "Me"
        assert result["remote_label"] == "Remote"

    def test_to_dict_includes_web_url(self) -> None:
        """to_dict includes web_url field."""
        state = MeetingState(
            id="test",
            started_at=datetime.now(),
            web_url="http://localhost:8765",
        )
        result = state.to_dict()
        assert result["web_url"] == "http://localhost:8765"


class TestIntelSnapshot:
    """Tests for IntelSnapshot dataclass."""

    # ============================================================
    # Creation Tests
    # ============================================================

    def test_creation_minimal(self) -> None:
        """IntelSnapshot can be created with just timestamp."""
        snapshot = IntelSnapshot(timestamp=120.0)
        assert snapshot.timestamp == 120.0
        assert snapshot.topics == []
        assert snapshot.action_items == []
        assert snapshot.summary == ""

    def test_creation_full(self) -> None:
        """IntelSnapshot can be created with all fields."""
        snapshot = IntelSnapshot(
            timestamp=300.0,
            topics=["Project timeline", "Budget review"],
            action_items=[
                {"task": "Send proposal", "owner": "Me", "due": "Tomorrow"},
                {"task": "Review docs", "owner": "Remote", "due": None},
            ],
            summary="Productive meeting about project planning.",
        )
        assert len(snapshot.topics) == 2
        assert len(snapshot.action_items) == 2
        assert snapshot.summary == "Productive meeting about project planning."

    # ============================================================
    # to_dict Tests
    # ============================================================

    def test_to_dict_minimal(self) -> None:
        """to_dict with minimal snapshot."""
        snapshot = IntelSnapshot(timestamp=60.0)
        result = snapshot.to_dict()

        assert result == {
            "timestamp": 60.0,
            "topics": [],
            "action_items": [],
            "summary": "",
        }

    def test_to_dict_full(self) -> None:
        """to_dict with full snapshot."""
        snapshot = IntelSnapshot(
            timestamp=180.0,
            topics=["API design", "Testing strategy"],
            action_items=[
                {"task": "Write API spec", "owner": "Me", "due": "Friday"},
            ],
            summary="Discussed API design and testing approach.",
        )
        result = snapshot.to_dict()

        assert result["timestamp"] == 180.0
        assert result["topics"] == ["API design", "Testing strategy"]
        assert len(result["action_items"]) == 1
        assert result["action_items"][0]["task"] == "Write API spec"
        assert result["summary"] == "Discussed API design and testing approach."

    def test_to_dict_preserves_action_item_structure(self) -> None:
        """to_dict preserves action item dictionary structure."""
        action_items = [
            {"task": "Task 1", "owner": "Alice", "due": "Monday"},
            {"task": "Task 2", "owner": "Bob", "due": None},
            {"task": "Task 3", "owner": None, "due": "Tuesday"},
        ]
        snapshot = IntelSnapshot(timestamp=0.0, action_items=action_items)
        result = snapshot.to_dict()

        assert result["action_items"] == action_items
