# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_meeting_state.py to restore.

# ruff: noqa


# --- TestTranscriptSegment::test_creation_from_fixture: P2: asserts the conftest fixture holds the values the fixture set
# (was a method of class TestTranscriptSegment)
def test_creation_from_fixture(self, sample_segments) -> None:
    """Sample segments fixture creates valid TranscriptSegments."""
    assert len(sample_segments) == 3
    assert sample_segments[0].speaker == "Me"
    assert sample_segments[1].speaker == "Remote"


# --- TestBookmark::test_creation_from_fixture: P2: asserts the conftest fixture holds the values the fixture set
# (was a method of class TestBookmark)
def test_creation_from_fixture(self, sample_bookmark) -> None:
    """Sample bookmark fixture creates valid Bookmark."""
    assert sample_bookmark.timestamp == 45.5
    assert sample_bookmark.label == "Important decision"


# --- TestMeetingState::test_creation_from_fixture: P2: asserts the conftest fixture holds the values the fixture set
# (was a method of class TestMeetingState)
def test_creation_from_fixture(self, sample_meeting_state) -> None:
    """Sample meeting state fixture creates valid MeetingState."""
    assert sample_meeting_state.id == "test-meeting-123"
    assert sample_meeting_state.mic_label == "Me"
    assert sample_meeting_state.remote_label == "Remote"


# --- TestTranscriptSegment::test_creation: P1/P3: constructs a dataclass from literals (or defaults) and reads the same literals back
# (was a method of class TestTranscriptSegment)
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


# --- TestTranscriptSegment::test_creation_with_bookmark: P1/P3: constructs a dataclass from literals (or defaults) and reads the same literals back
# (was a method of class TestTranscriptSegment)
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


# --- TestBookmark::test_creation_minimal: P1/P3: constructs a dataclass from literals (or defaults) and reads the same literals back
# (was a method of class TestBookmark)
def test_creation_minimal(self) -> None:
    """Bookmark can be created with just timestamp."""
    bookmark = Bookmark(timestamp=45.5)
    assert bookmark.timestamp == 45.5
    assert bookmark.label == ""
    assert bookmark.created_at is not None


# --- TestBookmark::test_creation_with_label: P1/P3: constructs a dataclass from literals (or defaults) and reads the same literals back
# (was a method of class TestBookmark)
def test_creation_with_label(self) -> None:
    """Bookmark can be created with label."""
    bookmark = Bookmark(timestamp=100.0, label="Important decision")
    assert bookmark.label == "Important decision"


# --- TestBookmark::test_creation_with_explicit_datetime: P1/P3: constructs a dataclass from literals (or defaults) and reads the same literals back
# (was a method of class TestBookmark)
def test_creation_with_explicit_datetime(self) -> None:
    """Bookmark can be created with explicit datetime."""
    dt = datetime(2024, 6, 15, 14, 30, 0)
    bookmark = Bookmark(timestamp=30.0, label="Test", created_at=dt)
    assert bookmark.created_at == dt


# --- TestBookmark::test_to_dict_empty_label: P1/P3: constructs a dataclass from literals (or defaults) and reads the same literals back
# (was a method of class TestBookmark)
def test_to_dict_empty_label(self) -> None:
    """to_dict handles empty label."""
    bookmark = Bookmark(timestamp=10.0)
    result = bookmark.to_dict()
    assert result["label"] == ""


# --- TestMeetingState::test_creation_minimal: P1/P3: constructs a dataclass from literals (or defaults) and reads the same literals back
# (was a method of class TestMeetingState)
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


# --- TestMeetingState::test_to_dict_includes_labels: P1/P3: constructs a dataclass from literals (or defaults) and reads the same literals back
# (was a method of class TestMeetingState)
def test_to_dict_includes_labels(self, sample_meeting_state) -> None:
    """to_dict includes mic_label and remote_label."""
    result = sample_meeting_state.to_dict()
    assert result["mic_label"] == "Me"
    assert result["remote_label"] == "Remote"


# --- TestMeetingState::test_to_dict_includes_web_url: P1/P3: constructs a dataclass from literals (or defaults) and reads the same literals back
# (was a method of class TestMeetingState)
def test_to_dict_includes_web_url(self) -> None:
    """to_dict includes web_url field."""
    state = MeetingState(
        id="test",
        started_at=datetime.now(),
        web_url="http://localhost:8765",
    )
    result = state.to_dict()
    assert result["web_url"] == "http://localhost:8765"


# --- TestMeetingState::test_devices_default_empty_list: P1/P3: constructs a dataclass from literals (or defaults) and reads the same literals back
# (was a method of class TestMeetingState)
def test_devices_default_empty_list(self) -> None:
    from datetime import datetime

    from holdspeak.meeting_session import MeetingState

    state = MeetingState(id="m", started_at=datetime.now())
    result = state.to_dict()
    assert result["devices"] == []


# --- TestIntelSnapshot::test_creation_minimal: P1/P3: constructs a dataclass from literals (or defaults) and reads the same literals back
# (was a method of class TestIntelSnapshot)
def test_creation_minimal(self) -> None:
    """IntelSnapshot can be created with just timestamp."""
    snapshot = IntelSnapshot(timestamp=120.0)
    assert snapshot.timestamp == 120.0
    assert snapshot.topics == []
    assert snapshot.action_items == []
    assert snapshot.summary == ""


# --- TestIntelSnapshot::test_creation_full: P1/P3: constructs a dataclass from literals (or defaults) and reads the same literals back
# (was a method of class TestIntelSnapshot)
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


# --- TestIntelSnapshot::test_to_dict_preserves_action_item_structure: P1/P3: constructs a dataclass from literals (or defaults) and reads the same literals back
# (was a method of class TestIntelSnapshot)
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


# --- TestTranscriptSegment::test_duration_zero: P5: the duration and timestamp tests above with zero instead of a number
# (was a method of class TestTranscriptSegment)
def test_duration_zero(self) -> None:
    """duration is zero when start_time equals end_time."""
    segment = TranscriptSegment(
        text="Test",
        speaker="Me",
        start_time=5.0,
        end_time=5.0,
    )
    assert segment.duration == 0.0


# --- TestTranscriptSegment::test_format_timestamp_zero: P5: the duration and timestamp tests above with zero instead of a number
# (was a method of class TestTranscriptSegment)
def test_format_timestamp_zero(self) -> None:
    """format_timestamp at start of meeting."""
    segment = TranscriptSegment(
        text="Test",
        speaker="Me",
        start_time=0.0,
        end_time=5.0,
    )
    assert segment.format_timestamp() == "00:00:00"
