"""Unit tests for the meeting database module."""

import pytest
from datetime import datetime
from pathlib import Path
import tempfile
import shutil

from holdspeak.db import (
    MeetingDatabase,
    MeetingSummary,
    ActionItemSummary,
    reset_database,
)
from holdspeak.meeting_session import (
    MeetingState,
    TranscriptSegment,
    Bookmark,
    IntelSnapshot,
)


@pytest.fixture
def temp_db_path():
    """Create a temporary database path for testing."""
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test.db"
    yield db_path
    # Cleanup
    reset_database()
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def db(temp_db_path):
    """Create a test database instance."""
    return MeetingDatabase(temp_db_path)


@pytest.fixture
def sample_meeting():
    """Create a sample meeting state for testing."""
    return MeetingState(
        id="test123",
        started_at=datetime(2024, 1, 15, 10, 0, 0),
        ended_at=datetime(2024, 1, 15, 11, 0, 0),
        title="Test Meeting",
        tags=["important", "test"],
        segments=[
            TranscriptSegment(
                text="Hello, how are you?",
                speaker="Me",
                start_time=0.0,
                end_time=3.0,
            ),
            TranscriptSegment(
                text="I'm doing well, thanks!",
                speaker="Remote",
                start_time=4.0,
                end_time=7.0,
            ),
        ],
        bookmarks=[
            Bookmark(timestamp=5.0, label="Important point"),
        ],
        mic_label="Me",
        remote_label="Remote",
    )


class TestMeetingDatabase:
    """Tests for MeetingDatabase class."""

    def test_init_creates_schema(self, db, temp_db_path):
        """Test that database initialization creates the schema."""
        assert temp_db_path.exists()
        # Verify tables exist by attempting queries
        meetings = db.list_meetings()
        assert meetings == []

    def test_save_and_get_meeting(self, db, sample_meeting):
        """Test saving and retrieving a meeting."""
        db.save_meeting(sample_meeting)

        retrieved = db.get_meeting(sample_meeting.id)
        assert retrieved is not None
        assert retrieved.id == sample_meeting.id
        assert retrieved.title == sample_meeting.title
        assert len(retrieved.segments) == 2
        assert len(retrieved.bookmarks) == 1
        assert retrieved.mic_label == "Me"
        assert retrieved.remote_label == "Remote"

    def test_save_meeting_with_intel(self, db, sample_meeting):
        """Test saving a meeting with intel snapshot."""
        sample_meeting.intel = IntelSnapshot(
            timestamp=60.0,
            topics=["greeting", "wellbeing"],
            action_items=[
                {
                    "id": "action1",
                    "task": "Follow up on project",
                    "owner": "Me",
                    "due": "2024-01-20",
                    "status": "pending",
                    "created_at": datetime.now().isoformat(),
                }
            ],
            summary="A friendly conversation about wellbeing.",
        )

        db.save_meeting(sample_meeting)

        retrieved = db.get_meeting(sample_meeting.id)
        assert retrieved.intel is not None
        assert len(retrieved.intel.topics) == 2
        assert len(retrieved.intel.action_items) == 1
        assert retrieved.intel.summary == "A friendly conversation about wellbeing."

    def test_get_nonexistent_meeting(self, db):
        """Test getting a meeting that doesn't exist."""
        result = db.get_meeting("nonexistent")
        assert result is None

    def test_list_meetings(self, db, sample_meeting):
        """Test listing meetings."""
        # Save multiple meetings
        db.save_meeting(sample_meeting)

        meeting2 = MeetingState(
            id="test456",
            started_at=datetime(2024, 1, 16, 14, 0, 0),
            ended_at=datetime(2024, 1, 16, 15, 0, 0),
            title="Second Meeting",
            mic_label="Me",
            remote_label="Remote",
        )
        db.save_meeting(meeting2)

        meetings = db.list_meetings()
        assert len(meetings) == 2
        # Should be sorted by date descending
        assert meetings[0].id == "test456"
        assert meetings[1].id == "test123"

    def test_list_meetings_with_limit(self, db, sample_meeting):
        """Test listing meetings with limit."""
        db.save_meeting(sample_meeting)

        meeting2 = MeetingState(
            id="test456",
            started_at=datetime(2024, 1, 16, 14, 0, 0),
            mic_label="Me",
            remote_label="Remote",
        )
        db.save_meeting(meeting2)

        meetings = db.list_meetings(limit=1)
        assert len(meetings) == 1

    def test_list_meetings_date_filter(self, db, sample_meeting):
        """Test filtering meetings by date range."""
        db.save_meeting(sample_meeting)

        meeting2 = MeetingState(
            id="test456",
            started_at=datetime(2024, 2, 1, 14, 0, 0),
            mic_label="Me",
            remote_label="Remote",
        )
        db.save_meeting(meeting2)

        # Filter to January only
        meetings = db.list_meetings(
            date_from=datetime(2024, 1, 1),
            date_to=datetime(2024, 1, 31),
        )
        assert len(meetings) == 1
        assert meetings[0].id == "test123"

    def test_delete_meeting(self, db, sample_meeting):
        """Test deleting a meeting."""
        db.save_meeting(sample_meeting)

        result = db.delete_meeting(sample_meeting.id)
        assert result is True

        # Should be gone
        retrieved = db.get_meeting(sample_meeting.id)
        assert retrieved is None

    def test_delete_nonexistent_meeting(self, db):
        """Test deleting a meeting that doesn't exist."""
        result = db.delete_meeting("nonexistent")
        assert result is False

    def test_get_meeting_count(self, db, sample_meeting):
        """Test counting meetings."""
        assert db.get_meeting_count() == 0

        db.save_meeting(sample_meeting)
        assert db.get_meeting_count() == 1

        meeting2 = MeetingState(
            id="test456",
            started_at=datetime.now(),
            mic_label="Me",
            remote_label="Remote",
        )
        db.save_meeting(meeting2)
        assert db.get_meeting_count() == 2


class TestActionItems:
    """Tests for action item operations."""

    def test_list_action_items(self, db, sample_meeting):
        """Test listing action items across meetings."""
        sample_meeting.intel = IntelSnapshot(
            timestamp=60.0,
            topics=[],
            action_items=[
                {
                    "id": "action1",
                    "task": "Task one",
                    "owner": "Me",
                    "status": "pending",
                    "created_at": datetime.now().isoformat(),
                },
                {
                    "id": "action2",
                    "task": "Task two",
                    "owner": "Remote",
                    "status": "done",
                    "created_at": datetime.now().isoformat(),
                },
            ],
        )
        db.save_meeting(sample_meeting)

        # Pending only
        items = db.list_action_items(include_completed=False)
        assert len(items) == 1
        assert items[0].task == "Task one"

        # All items
        items = db.list_action_items(include_completed=True)
        assert len(items) == 2

    def test_list_action_items_by_owner(self, db, sample_meeting):
        """Test filtering action items by owner."""
        sample_meeting.intel = IntelSnapshot(
            timestamp=60.0,
            topics=[],
            action_items=[
                {
                    "id": "action1",
                    "task": "My task",
                    "owner": "Me",
                    "status": "pending",
                    "created_at": datetime.now().isoformat(),
                },
                {
                    "id": "action2",
                    "task": "Their task",
                    "owner": "Remote",
                    "status": "pending",
                    "created_at": datetime.now().isoformat(),
                },
            ],
        )
        db.save_meeting(sample_meeting)

        items = db.list_action_items(include_completed=True, owner="Me")
        assert len(items) == 1
        assert items[0].task == "My task"

    def test_update_action_item_status(self, db, sample_meeting):
        """Test updating action item status."""
        sample_meeting.intel = IntelSnapshot(
            timestamp=60.0,
            topics=[],
            action_items=[
                {
                    "id": "action1",
                    "task": "Task one",
                    "owner": "Me",
                    "status": "pending",
                    "created_at": datetime.now().isoformat(),
                },
            ],
        )
        db.save_meeting(sample_meeting)

        # Update to done
        result = db.update_action_item_status("action1", "done")
        assert result is True

        # Verify
        items = db.list_action_items(include_completed=True)
        assert items[0].status == "done"
        assert items[0].completed_at is not None

    def test_update_nonexistent_action_item(self, db):
        """Test updating an action item that doesn't exist."""
        result = db.update_action_item_status("nonexistent", "done")
        assert result is False


class TestTranscriptSearch:
    """Tests for full-text search functionality."""

    def test_search_transcripts(self, db, sample_meeting):
        """Test searching transcripts."""
        db.save_meeting(sample_meeting)

        # Search for "hello"
        results = db.search_transcripts("hello")
        assert len(results) == 1
        meeting_id, segment = results[0]
        assert meeting_id == "test123"
        assert "Hello" in segment.text

    def test_search_transcripts_no_results(self, db, sample_meeting):
        """Test search with no results."""
        db.save_meeting(sample_meeting)

        results = db.search_transcripts("nonexistent phrase")
        assert len(results) == 0

    def test_search_transcripts_multiple_results(self, db, sample_meeting):
        """Test search returning multiple results."""
        # Add more segments
        sample_meeting.segments.append(
            TranscriptSegment(
                text="Hello again, let's continue.",
                speaker="Me",
                start_time=10.0,
                end_time=13.0,
            )
        )
        db.save_meeting(sample_meeting)

        results = db.search_transcripts("hello")
        assert len(results) == 2


class TestMeetingSummary:
    """Tests for MeetingSummary dataclass."""

    def test_meeting_summary_in_list(self, db, sample_meeting):
        """Test that list_meetings returns proper MeetingSummary objects."""
        db.save_meeting(sample_meeting)

        meetings = db.list_meetings()
        assert len(meetings) == 1

        summary = meetings[0]
        assert isinstance(summary, MeetingSummary)
        assert summary.id == "test123"
        assert summary.title == "Test Meeting"
        assert summary.segment_count == 2
        assert summary.duration_seconds == 3600.0  # 1 hour


class TestUpsert:
    """Tests for upsert behavior."""

    def test_save_meeting_updates_existing(self, db, sample_meeting):
        """Test that saving a meeting again updates it."""
        db.save_meeting(sample_meeting)

        # Modify and save again
        sample_meeting.title = "Updated Title"
        sample_meeting.segments.append(
            TranscriptSegment(
                text="New segment",
                speaker="Me",
                start_time=20.0,
                end_time=23.0,
            )
        )
        db.save_meeting(sample_meeting)

        # Should still be one meeting
        assert db.get_meeting_count() == 1

        # Should have updated data
        retrieved = db.get_meeting(sample_meeting.id)
        assert retrieved.title == "Updated Title"
        assert len(retrieved.segments) == 3
