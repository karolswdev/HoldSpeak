"""Unit tests for the meeting database module."""

import ast
import pytest
from datetime import datetime
from pathlib import Path
import tempfile
import shutil

from holdspeak.db import (
    MeetingDatabase,
    MeetingSummary,
    ActionItemSummary,
    IntelJob,
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

    def test_update_action_item_status_dismissed_sets_completed_at(self, db, sample_meeting):
        """Dismissed action items are terminal and should get a completion timestamp."""
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

        result = db.update_action_item_status("action1", "dismissed")
        assert result is True

        items = db.list_action_items(include_completed=True)
        assert items[0].status == "dismissed"
        assert items[0].completed_at is not None

    def test_update_action_item_status_pending_clears_completed_at(self, db, sample_meeting):
        """Returning an action item to pending should clear any terminal timestamp."""
        sample_meeting.intel = IntelSnapshot(
            timestamp=60.0,
            topics=[],
            action_items=[
                {
                    "id": "action1",
                    "task": "Task one",
                    "owner": "Me",
                    "status": "done",
                    "created_at": datetime.now().isoformat(),
                    "completed_at": datetime.now().isoformat(),
                },
            ],
        )
        db.save_meeting(sample_meeting)

        result = db.update_action_item_status("action1", "pending")
        assert result is True

        items = db.list_action_items(include_completed=True)
        assert items[0].status == "pending"
        assert items[0].completed_at is None

    def test_update_nonexistent_action_item(self, db):
        """Test updating an action item that doesn't exist."""
        result = db.update_action_item_status("nonexistent", "done")
        assert result is False

    def test_update_action_item_status_rejects_invalid_status(self, db, sample_meeting):
        """The DB layer should reject statuses outside the supported contract."""
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

        with pytest.raises(ValueError, match="Invalid action item status"):
            db.update_action_item_status("action1", "archived")

    def test_save_meeting_preserves_terminal_action_item_status_across_resave(self, db, sample_meeting):
        """A later re-save should not reset a completed item back to pending."""
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

        result = db.update_action_item_status("action1", "done")
        assert result is True

        completed_item = db.list_action_items(include_completed=True)[0]
        original_completed_at = completed_item.completed_at
        assert original_completed_at is not None

        # Simulate a subsequent intel extraction for the same action item.
        sample_meeting.intel = IntelSnapshot(
            timestamp=120.0,
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

        resaved_item = db.list_action_items(include_completed=True)[0]
        assert resaved_item.status == "done"
        assert resaved_item.completed_at == original_completed_at

    def test_save_meeting_rejects_invalid_action_item_status(self, db, sample_meeting):
        """Meeting saves should fail fast on unsupported persisted action-item states."""
        sample_meeting.intel = IntelSnapshot(
            timestamp=60.0,
            topics=[],
            action_items=[
                {
                    "id": "action1",
                    "task": "Task one",
                    "owner": "Me",
                    "status": "archived",
                    "created_at": datetime.now().isoformat(),
                },
            ],
        )

        with pytest.raises(ValueError, match="Invalid action item status"):
            db.save_meeting(sample_meeting)


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


class TestDeferredIntelQueue:
    """Tests for deferred meeting-intelligence queue persistence."""

    def test_enqueue_and_claim_intel_job(self, db, sample_meeting):
        """Queued intel jobs should be claimable for later processing."""
        sample_meeting.intel_status = "queued"
        sample_meeting.intel_status_detail = "Queued for later processing."
        sample_meeting.intel_requested_at = datetime.now()
        db.save_meeting(sample_meeting)

        transcript_hash = sample_meeting.transcript_hash()
        db.enqueue_intel_job(sample_meeting.id, transcript_hash=transcript_hash)

        claimed = db.claim_next_intel_job()
        assert isinstance(claimed, IntelJob)
        assert claimed.meeting_id == sample_meeting.id
        assert claimed.status == "running"
        assert claimed.transcript_hash == transcript_hash

    def test_complete_intel_job_removes_queue_entry(self, db, sample_meeting):
        """Completed jobs should be removed from the queue."""
        db.save_meeting(sample_meeting)
        db.enqueue_intel_job(sample_meeting.id, transcript_hash=sample_meeting.transcript_hash())

        claimed = db.claim_next_intel_job()
        assert claimed is not None

        db.complete_intel_job(sample_meeting.id)
        assert db.claim_next_intel_job() is None

    def test_fail_intel_job_updates_meeting_status(self, db, sample_meeting):
        """Failed jobs should surface as meeting intel errors."""
        db.save_meeting(sample_meeting)
        db.enqueue_intel_job(sample_meeting.id, transcript_hash=sample_meeting.transcript_hash())

        claimed = db.claim_next_intel_job()
        assert claimed is not None

        db.fail_intel_job(sample_meeting.id, "Deferred intel failed")
        updated = db.get_meeting(sample_meeting.id)
        assert updated is not None
        assert updated.intel_status == "error"
        assert updated.intel_status_detail == "Deferred intel failed"

    def test_list_intel_jobs_includes_meeting_context(self, db, sample_meeting):
        """Queued jobs should include meeting metadata for CLI display."""
        db.save_meeting(sample_meeting)
        db.enqueue_intel_job(sample_meeting.id, transcript_hash=sample_meeting.transcript_hash())

        jobs = db.list_intel_jobs()
        assert len(jobs) == 1
        job = jobs[0]
        assert job.meeting_id == sample_meeting.id
        assert job.meeting_title == sample_meeting.title
        assert job.started_at == sample_meeting.started_at

    def test_requeue_intel_job_refreshes_failed_job(self, db, sample_meeting):
        """Failed jobs should be requeueable for manual retry."""
        db.save_meeting(sample_meeting)
        db.enqueue_intel_job(sample_meeting.id, transcript_hash=sample_meeting.transcript_hash())
        db.claim_next_intel_job()
        db.fail_intel_job(sample_meeting.id, "Deferred intel failed")

        assert db.requeue_intel_job(sample_meeting.id, reason="Manual retry requested.")

        jobs = db.list_intel_jobs(status="queued")
        assert len(jobs) == 1
        assert jobs[0].meeting_id == sample_meeting.id
        assert jobs[0].status == "queued"
        assert jobs[0].last_error == "Manual retry requested."


class TestDatabaseShape:
    """Tests for structural invariants in the DB layer."""

    def test_meeting_database_has_no_duplicate_method_definitions(self, project_root: Path):
        """Public DB methods should have one canonical implementation each."""
        db_path = project_root / "holdspeak" / "db.py"
        module = ast.parse(db_path.read_text())

        methods: dict[str, list[int]] = {}
        for node in module.body:
            if isinstance(node, ast.ClassDef) and node.name == "MeetingDatabase":
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        methods.setdefault(item.name, []).append(item.lineno)

        duplicates = {
            name: lines
            for name, lines in methods.items()
            if len(lines) > 1 and not name.startswith("_")
        }
        assert duplicates == {}
