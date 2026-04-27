"""Unit tests for the meeting database module."""

import ast
import pytest
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import shutil

from holdspeak.db import (
    MeetingDatabase,
    MeetingSummary,
    ActionItemSummary,
    IntelJob,
    IntentWindowSummary,
    PluginRunSummary,
    ArtifactSummary,
    ActivityRecord,
    ActivityImportCheckpoint,
    ActivityProjectRule,
    ActivityEnrichmentConnectorState,
    ActivityAnnotation,
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
        assert items[0].review_state == "pending"
        assert items[0].reviewed_at is None

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

    def test_update_action_item_review_state(self, db, sample_meeting):
        """Action items can be explicitly accepted during intel review."""
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

        assert db.update_action_item_review_state("action1", "accepted")
        item = db.get_action_item("action1")
        assert item is not None
        assert item.review_state == "accepted"
        assert item.reviewed_at is not None

    def test_update_action_item_review_state_rejects_invalid_value(self, db, sample_meeting):
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

        with pytest.raises(ValueError, match="Invalid action item review_state"):
            db.update_action_item_review_state("action1", "approved")

    def test_edit_action_item_auto_accepts(self, db, sample_meeting):
        """Editing an intel item should count as accepting it."""
        sample_meeting.intel = IntelSnapshot(
            timestamp=60.0,
            topics=[],
            action_items=[
                {
                    "id": "action1",
                    "task": "Original task",
                    "owner": "Me",
                    "status": "pending",
                    "created_at": datetime.now().isoformat(),
                },
            ],
        )
        db.save_meeting(sample_meeting)

        assert db.edit_action_item(
            "action1",
            task="Edited task",
            owner="Remote",
            due="Friday",
        )

        item = db.get_action_item("action1")
        assert item is not None
        assert item.task == "Edited task"
        assert item.owner == "Remote"
        assert item.due == "Friday"
        assert item.review_state == "accepted"
        assert item.reviewed_at is not None

    def test_edit_action_item_rejects_empty_task(self, db, sample_meeting):
        sample_meeting.intel = IntelSnapshot(
            timestamp=60.0,
            topics=[],
            action_items=[
                {
                    "id": "action1",
                    "task": "Original task",
                    "owner": "Me",
                    "status": "pending",
                    "created_at": datetime.now().isoformat(),
                },
            ],
        )
        db.save_meeting(sample_meeting)

        with pytest.raises(ValueError, match="cannot be empty"):
            db.edit_action_item("action1", task="   ", owner=None, due=None)

    def test_save_meeting_preserves_review_state_across_resave(self, db, sample_meeting):
        """A later extraction should not reset accepted review state to pending."""
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
        assert db.update_action_item_review_state("action1", "accepted")
        accepted = db.get_action_item("action1")
        assert accepted is not None
        accepted_reviewed_at = accepted.reviewed_at
        assert accepted_reviewed_at is not None

        sample_meeting.intel = IntelSnapshot(
            timestamp=120.0,
            topics=[],
            action_items=[
                {
                    "id": "action1",
                    "task": "Task one",
                    "owner": "Me",
                    "status": "pending",
                    "review_state": "pending",
                    "created_at": datetime.now().isoformat(),
                },
            ],
        )
        db.save_meeting(sample_meeting)

        resaved = db.get_action_item("action1")
        assert resaved is not None
        assert resaved.review_state == "accepted"
        assert resaved.reviewed_at == accepted_reviewed_at

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


class TestActivityLedgerPersistence:
    """Tests for local activity intelligence persistence."""

    def test_upsert_activity_record_persists_locally(self, db):
        seen = datetime(2026, 4, 26, 9, 30, 0)

        record = db.upsert_activity_record(
            source_browser="Safari",
            source_profile="default",
            source_path_hash="hash-safari",
            url="https://example.atlassian.net/browse/HS-123?b=2&a=1#comment",
            title="HS-123 work item",
            visit_count=3,
            first_seen_at=seen,
            last_seen_at=seen,
            last_visit_raw="799320600.0",
            entity_type="jira_ticket",
            entity_id="HS-123",
        )

        assert isinstance(record, ActivityRecord)
        assert record.source_browser == "safari"
        assert record.source_profile == "default"
        assert record.domain == "example.atlassian.net"
        assert record.normalized_url == "https://example.atlassian.net/browse/HS-123?a=1&b=2"
        assert record.last_visit_raw == "799320600.0"
        assert record.last_seen_at == seen

        listed = db.list_activity_records(source_browser="safari")
        assert len(listed) == 1
        assert listed[0].id == record.id

    def test_duplicate_activity_records_merge_by_normalized_url(self, db):
        first = datetime(2026, 4, 26, 9, 0, 0)
        last = datetime(2026, 4, 26, 11, 0, 0)

        created = db.upsert_activity_record(
            source_browser="firefox",
            source_profile="work",
            url="https://miro.com/app/board/uXjVMiro123/?utm_source=email",
            title="Miro board",
            visit_count=2,
            first_seen_at=last,
            last_seen_at=last,
            last_visit_raw="1745665200000000",
        )
        merged = db.upsert_activity_record(
            source_browser="firefox",
            source_profile="work",
            url="https://miro.com/app/board/uXjVMiro123?utm_source=email",
            title="Renamed Miro board",
            visit_count=5,
            first_seen_at=first,
            last_seen_at=last,
            last_visit_raw="1745672400000000",
        )

        assert merged.id == created.id
        assert merged.title == "Renamed Miro board"
        assert merged.visit_count == 5
        assert merged.first_seen_at == first
        assert merged.last_seen_at == last
        assert db.list_activity_records(source_browser="firefox", source_profile="work") == [merged]

    def test_duplicate_activity_records_merge_by_entity(self, db):
        first = datetime(2026, 4, 26, 9, 0, 0)
        second = datetime(2026, 4, 26, 10, 0, 0)

        created = db.upsert_activity_record(
            source_browser="safari",
            url="https://github.com/acme/app/pull/42",
            title="PR 42",
            first_seen_at=first,
            last_seen_at=first,
            entity_type="github_pull_request",
            entity_id="acme/app#42",
        )
        merged = db.upsert_activity_record(
            source_browser="safari",
            url="https://github.com/acme/app/pull/42/files",
            title="PR 42 files",
            first_seen_at=second,
            last_seen_at=second,
            entity_type="github_pull_request",
            entity_id="acme/app#42",
        )

        assert merged.id == created.id
        assert merged.normalized_url == "https://github.com/acme/app/pull/42/files"
        assert merged.first_seen_at == first
        assert merged.last_seen_at == second
        assert len(db.list_activity_records(entity_type="github_pull_request")) == 1

    def test_activity_import_checkpoint_round_trips_per_source_profile(self, db):
        imported_at = datetime(2026, 4, 26, 12, 0, 0)

        checkpoint = db.set_activity_import_checkpoint(
            source_browser="Safari",
            source_profile="default",
            source_path_hash="path-hash",
            last_visit_raw="799320600.0",
            last_imported_at=imported_at,
            enabled=True,
        )

        assert isinstance(checkpoint, ActivityImportCheckpoint)
        assert checkpoint.source_browser == "safari"
        assert checkpoint.source_profile == "default"
        assert checkpoint.source_path_hash == "path-hash"
        assert checkpoint.last_visit_raw == "799320600.0"
        assert checkpoint.last_imported_at == imported_at
        assert checkpoint.enabled is True

        db.set_activity_import_checkpoint(
            source_browser="safari",
            source_profile="default",
            source_path_hash="path-hash",
            last_visit_raw="799321000.0",
            last_imported_at=imported_at,
            last_error="temporary lock",
            enabled=False,
        )
        updated = db.get_activity_import_checkpoint(
            source_browser="safari",
            source_profile="default",
            source_path_hash="path-hash",
        )
        assert updated is not None
        assert updated.last_visit_raw == "799321000.0"
        assert updated.last_error == "temporary lock"
        assert updated.enabled is False

    def test_delete_activity_records_supports_retention_filters(self, db):
        old = datetime(2026, 4, 1, 9, 0, 0)
        recent = datetime(2026, 4, 26, 9, 0, 0)
        db.upsert_activity_record(
            source_browser="safari",
            url="https://old.example.com/ticket",
            domain="old.example.com",
            last_seen_at=old,
        )
        db.upsert_activity_record(
            source_browser="safari",
            url="https://recent.example.com/ticket",
            domain="recent.example.com",
            last_seen_at=recent,
        )

        deleted = db.delete_activity_records(older_than=datetime(2026, 4, 10))

        assert deleted == 1
        remaining = db.list_activity_records()
        assert len(remaining) == 1
        assert remaining[0].domain == "recent.example.com"

    def test_activity_privacy_settings_default_enabled_and_updateable(self, db):
        settings = db.get_activity_privacy_settings()
        assert settings["enabled"] is True
        assert settings["paused"] is False
        assert settings["retention_days"] == 30

        updated = db.update_activity_privacy_settings(
            enabled=False,
            retention_days=14,
        )

        assert updated["enabled"] is False
        assert updated["paused"] is True
        assert updated["retention_days"] == 14

    def test_activity_domain_rules_match_subdomains(self, db):
        rule = db.upsert_activity_domain_rule(domain="Example.COM", action="exclude")

        assert rule["domain"] == "example.com"
        assert db.is_activity_domain_excluded("example.com") is True
        assert db.is_activity_domain_excluded("docs.example.com") is True
        assert db.is_activity_domain_excluded("other.com") is False

        assert db.delete_activity_domain_rule("example.com") is True
        assert db.is_activity_domain_excluded("example.com") is False

    def test_activity_project_rules_preview_and_apply_records(self, db):
        db.create_project(project_id="holdspeak", name="HoldSpeak")
        db.create_project(project_id="other", name="Other")
        first_seen = datetime(2026, 4, 26, 9, 0, 0)
        db.upsert_activity_record(
            source_browser="safari",
            url="https://example.atlassian.net/browse/HS-123",
            title="HS-123 activity mapping",
            domain="example.atlassian.net",
            last_seen_at=first_seen,
            entity_type="jira_ticket",
            entity_id="HS-123",
        )
        db.upsert_activity_record(
            source_browser="safari",
            url="https://example.atlassian.net/browse/OTHER-1",
            title="OTHER-1 activity mapping",
            domain="example.atlassian.net",
            last_seen_at=first_seen,
            entity_type="jira_ticket",
            entity_id="OTHER-1",
        )

        low_priority = db.create_activity_project_rule(
            project_id="other",
            name="All Jira",
            match_type="entity_type",
            pattern="jira_ticket",
            priority=100,
        )
        high_priority = db.create_activity_project_rule(
            project_id="holdspeak",
            name="HoldSpeak tickets",
            match_type="entity_id_prefix",
            pattern="HS-",
            entity_type="jira_ticket",
            priority=200,
        )

        assert isinstance(high_priority, ActivityProjectRule)
        assert high_priority.project_name == "HoldSpeak"
        assert db.list_activity_project_rules() == [high_priority, low_priority]
        preview = db.preview_activity_project_rule(
            project_id="holdspeak",
            match_type="entity_id_prefix",
            pattern="HS-",
            entity_type="jira_ticket",
        )
        assert [record.entity_id for record in preview] == ["HS-123"]

        assert db.apply_activity_project_rules() == 2
        records = db.list_activity_records(limit=10)
        assert {record.entity_id: record.project_id for record in records} == {
            "HS-123": "holdspeak",
            "OTHER-1": "other",
        }

    def test_activity_project_rules_update_disable_and_delete(self, db):
        db.create_project(project_id="holdspeak", name="HoldSpeak")
        rule = db.create_activity_project_rule(
            project_id="holdspeak",
            match_type="domain",
            pattern="Example.COM",
        )

        updated = db.update_activity_project_rule(
            rule.id,
            name="Example",
            enabled=False,
            priority=300,
        )

        assert updated is not None
        assert updated.name == "Example"
        assert updated.enabled is False
        assert updated.priority == 300
        assert db.list_activity_project_rules() == []
        assert db.list_activity_project_rules(include_disabled=True) == [updated]
        assert db.delete_activity_project_rule(rule.id) is True
        assert db.list_activity_project_rules(include_disabled=True) == []

    def test_activity_enrichment_connector_state_round_trips(self, db):
        run_at = datetime(2026, 4, 27, 10, 30, 0)

        state = db.upsert_activity_enrichment_connector(
            connector_id="gh",
            enabled=True,
            settings={"timeout_seconds": 4, "max_bytes": 2048},
            last_error="not run yet",
        )

        assert isinstance(state, ActivityEnrichmentConnectorState)
        assert state.id == "gh"
        assert state.enabled is True
        assert state.settings == {"timeout_seconds": 4, "max_bytes": 2048}
        assert state.last_error == "not run yet"

        updated = db.record_activity_enrichment_run(
            connector_id="gh",
            last_run_at=run_at,
        )

        assert updated.enabled is True
        assert updated.settings == {"timeout_seconds": 4, "max_bytes": 2048}
        assert updated.last_run_at == run_at
        assert updated.last_error is None
        assert db.list_activity_enrichment_connectors() == [updated]

    def test_activity_annotations_attach_to_records_and_delete_by_connector(self, db):
        record = db.upsert_activity_record(
            source_browser="safari",
            url="https://github.com/openai/codex/pull/42",
            title="PR 42",
            domain="github.com",
            entity_type="github_pull_request",
            entity_id="openai/codex#42",
        )

        annotation = db.create_activity_annotation(
            activity_record_id=record.id,
            source_connector_id="gh",
            annotation_type="github_pr",
            title="Add enrichment substrate",
            value={"state": "OPEN", "labels": ["activity"]},
            confidence=1.5,
        )

        assert isinstance(annotation, ActivityAnnotation)
        assert annotation.activity_record_id == record.id
        assert annotation.source_connector_id == "gh"
        assert annotation.annotation_type == "github_pr"
        assert annotation.value == {"state": "OPEN", "labels": ["activity"]}
        assert annotation.confidence == 1.0
        assert db.list_activity_annotations(activity_record_id=record.id) == [annotation]
        assert db.list_activity_annotations(source_connector_id="gh") == [annotation]

        assert db.delete_activity_annotations(source_connector_id="gh") == 1
        assert db.list_activity_annotations(source_connector_id="gh") == []

    def test_activity_annotations_validate_record_reference(self, db):
        with pytest.raises(ValueError, match="activity record not found"):
            db.create_activity_annotation(
                activity_record_id=999,
                source_connector_id="gh",
                annotation_type="github_pr",
            )


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

    def test_claim_next_intel_job_skips_future_scheduled_jobs(self, db, sample_meeting):
        """Claim should ignore queued jobs that are not due yet."""
        db.save_meeting(sample_meeting)
        db.enqueue_intel_job(sample_meeting.id, transcript_hash=sample_meeting.transcript_hash())

        future = datetime.now() + timedelta(minutes=5)
        db.retry_intel_job(
            sample_meeting.id,
            "Deferred intel failed: temporary network issue",
            retry_at=future,
            attempt=1,
            max_attempts=6,
        )

        assert db.claim_next_intel_job() is None
        assert db.claim_next_intel_job(include_scheduled=True) is not None

    def test_retry_intel_job_requeues_and_updates_meeting_status(self, db, sample_meeting):
        """retry_intel_job should keep job queued with retry details."""
        db.save_meeting(sample_meeting)
        db.enqueue_intel_job(sample_meeting.id, transcript_hash=sample_meeting.transcript_hash())
        claimed = db.claim_next_intel_job()
        assert claimed is not None

        retry_at = datetime.now() + timedelta(seconds=30)
        db.retry_intel_job(
            sample_meeting.id,
            "Deferred intel failed: timeout",
            retry_at=retry_at,
            attempt=claimed.attempts,
            max_attempts=6,
        )

        queued = db.list_intel_jobs(status="queued")
        assert len(queued) == 1
        assert queued[0].meeting_id == sample_meeting.id
        assert queued[0].status == "queued"
        assert queued[0].last_error == "Deferred intel failed: timeout"
        assert queued[0].requested_at >= retry_at.replace(microsecond=0)

        meeting = db.get_meeting(sample_meeting.id)
        assert meeting is not None
        assert meeting.intel_status == "queued"
        assert "Retrying at" in (meeting.intel_status_detail or "")

    def test_get_intel_queue_summary_reports_aggregate_telemetry(self, db, sample_meeting):
        """Queue summary should report due/scheduled/retry telemetry accurately."""
        db.save_meeting(sample_meeting)
        db.enqueue_intel_job(sample_meeting.id, transcript_hash=sample_meeting.transcript_hash())

        summary = db.get_intel_queue_summary()
        assert summary.total_jobs == 1
        assert summary.queued_jobs == 1
        assert summary.queued_due_jobs == 1
        assert summary.scheduled_retry_jobs == 0
        assert summary.next_retry_at is None

        claimed = db.claim_next_intel_job()
        assert claimed is not None
        retry_at = datetime.now() + timedelta(minutes=2)
        db.retry_intel_job(
            sample_meeting.id,
            "Deferred intel failed: timeout",
            retry_at=retry_at,
            attempt=claimed.attempts,
            max_attempts=6,
        )

        scheduled = db.get_intel_queue_summary()
        assert scheduled.total_jobs == 1
        assert scheduled.queued_jobs == 1
        assert scheduled.queued_due_jobs == 0
        assert scheduled.scheduled_retry_jobs == 1
        assert scheduled.next_retry_at is not None

    def test_intel_job_attempt_history_round_trips(self, db, sample_meeting):
        """Attempt history should persist and return latest-first order."""
        db.save_meeting(sample_meeting)
        now = datetime.now()
        db.record_intel_job_attempt(
            sample_meeting.id,
            attempt=1,
            outcome="scheduled_retry",
            error="timeout",
            retry_at=now + timedelta(seconds=30),
        )
        db.record_intel_job_attempt(
            sample_meeting.id,
            attempt=2,
            outcome="terminal_failure",
            error="auth failure",
            retry_at=None,
        )

        attempts = db.list_intel_job_attempts(sample_meeting.id, limit=5)
        assert len(attempts) == 2
        assert attempts[0].attempt == 2
        assert attempts[0].outcome == "terminal_failure"
        assert attempts[1].attempt == 1
        assert attempts[1].retry_at is not None


class TestMirPersistence:
    """Tests for MIR intent-window and plugin-run persistence."""

    def test_record_and_list_intent_windows(self, db, sample_meeting):
        db.save_meeting(sample_meeting)

        db.record_intent_window(
            meeting_id=sample_meeting.id,
            window_id=f"{sample_meeting.id}:w0001",
            start_seconds=0.0,
            end_seconds=90.0,
            transcript_hash="abc123",
            transcript_excerpt="Architecture and delivery scope",
            profile="balanced",
            threshold=0.6,
            active_intents=["architecture", "delivery"],
            intent_scores={"architecture": 0.83, "delivery": 0.71},
            override_intents=[],
            tags=["design", "planning"],
            metadata={"source": "test"},
        )

        windows = db.list_intent_windows(sample_meeting.id)
        assert len(windows) == 1
        window = windows[0]
        assert isinstance(window, IntentWindowSummary)
        assert window.window_id == f"{sample_meeting.id}:w0001"
        assert window.active_intents == ["architecture", "delivery"]
        assert window.intent_scores["architecture"] == pytest.approx(0.83)
        assert window.intent_scores["delivery"] == pytest.approx(0.71)
        assert window.tags == ["design", "planning"]
        assert window.metadata["source"] == "test"

        # Upsert same window id should refresh values instead of duplicating rows.
        db.record_intent_window(
            meeting_id=sample_meeting.id,
            window_id=f"{sample_meeting.id}:w0001",
            start_seconds=30.0,
            end_seconds=120.0,
            transcript_hash="def456",
            transcript_excerpt="Incident handoff update",
            profile="incident_response",
            threshold=0.5,
            active_intents=["incident"],
            intent_scores={"incident": 0.92},
            override_intents=["incident"],
            tags=["incident"],
            metadata={"source": "refresh"},
        )

        refreshed = db.list_intent_windows(sample_meeting.id)
        assert len(refreshed) == 1
        row = refreshed[0]
        assert row.start_seconds == pytest.approx(30.0)
        assert row.end_seconds == pytest.approx(120.0)
        assert row.transcript_hash == "def456"
        assert row.profile == "incident_response"
        assert row.active_intents == ["incident"]
        assert row.intent_scores["incident"] == pytest.approx(0.92)
        assert row.override_intents == ["incident"]
        assert row.tags == ["incident"]
        assert row.metadata["source"] == "refresh"

    def test_record_and_list_plugin_runs(self, db, sample_meeting):
        db.save_meeting(sample_meeting)
        window_id = f"{sample_meeting.id}:w0001"

        db.record_intent_window(
            meeting_id=sample_meeting.id,
            window_id=window_id,
            start_seconds=0.0,
            end_seconds=90.0,
            transcript_hash="abc123",
            intent_scores={"architecture": 0.9},
        )

        db.record_plugin_run(
            meeting_id=sample_meeting.id,
            window_id=window_id,
            plugin_id="requirements_extractor",
            plugin_version="1.0.0",
            status="success",
            idempotency_key="idem-1",
            duration_ms=42.0,
            output={"items": 3},
            error=None,
            deduped=False,
        )

        # Same idempotency key should upsert, not duplicate.
        db.record_plugin_run(
            meeting_id=sample_meeting.id,
            window_id=window_id,
            plugin_id="requirements_extractor",
            plugin_version="1.0.1",
            status="deduped",
            idempotency_key="idem-1",
            duration_ms=0.0,
            output={"items": 3},
            error=None,
            deduped=True,
        )

        db.record_plugin_run(
            meeting_id=sample_meeting.id,
            window_id=window_id,
            plugin_id="risk_heatmap",
            plugin_version="2.0.0",
            status="error",
            idempotency_key=None,
            duration_ms=15.0,
            output=None,
            error="RuntimeError: boom",
            deduped=False,
        )

        runs = db.list_plugin_runs(sample_meeting.id)
        assert len(runs) == 2
        assert all(isinstance(run, PluginRunSummary) for run in runs)

        first = runs[0]
        second = runs[1]
        # Newest record first.
        assert first.plugin_id == "risk_heatmap"
        assert first.status == "error"
        assert first.error == "RuntimeError: boom"
        assert first.output is None

        assert second.plugin_id == "requirements_extractor"
        assert second.status == "deduped"
        assert second.plugin_version == "1.0.1"
        assert second.idempotency_key == "idem-1"
        assert second.deduped is True
        assert second.output == {"items": 3}

        filtered = db.list_plugin_runs(sample_meeting.id, window_id=window_id)
        assert len(filtered) == 2

    def test_record_and_list_artifacts_with_lineage(self, db, sample_meeting):
        db.save_meeting(sample_meeting)

        db.record_artifact(
            artifact_id="art-1",
            meeting_id=sample_meeting.id,
            artifact_type="requirements",
            title="Requirements Extractor",
            body_markdown="### Requirements\n\nDefine acceptance criteria.",
            structured_json={"plugin_run_ids": ["11"], "window_ids": [f"{sample_meeting.id}:w0001"]},
            confidence=0.82,
            status="draft",
            plugin_id="requirements_extractor",
            plugin_version="1.0.0",
            sources=[
                {"source_type": "intent_window", "source_ref": f"{sample_meeting.id}:w0001"},
                {"source_type": "plugin_run", "source_ref": "11"},
            ],
        )

        # Upsert should replace body + sources without duplicating record.
        db.record_artifact(
            artifact_id="art-1",
            meeting_id=sample_meeting.id,
            artifact_type="requirements",
            title="Requirements Extractor",
            body_markdown="### Requirements\n\nUpdated with rollout constraints.",
            structured_json={"plugin_run_ids": ["11", "12"], "window_ids": [f"{sample_meeting.id}:w0001", f"{sample_meeting.id}:w0002"]},
            confidence=0.74,
            status="needs_review",
            plugin_id="requirements_extractor",
            plugin_version="1.1.0",
            sources=[
                {"source_type": "intent_window", "source_ref": f"{sample_meeting.id}:w0002"},
                {"source_type": "plugin_run", "source_ref": "12"},
            ],
        )

        artifacts = db.list_artifacts(sample_meeting.id)
        assert len(artifacts) == 1
        artifact = artifacts[0]
        assert isinstance(artifact, ArtifactSummary)
        assert artifact.id == "art-1"
        assert artifact.status == "needs_review"
        assert artifact.plugin_version == "1.1.0"
        assert artifact.body_markdown.endswith("rollout constraints.")
        assert artifact.structured_json["plugin_run_ids"] == ["11", "12"]
        refs = {(src["source_type"], src["source_ref"]) for src in artifact.sources}
        assert ("intent_window", f"{sample_meeting.id}:w0002") in refs
        assert ("plugin_run", "12") in refs

    def test_plugin_run_job_queue_lifecycle(self, db, sample_meeting):
        db.save_meeting(sample_meeting)
        idempotency_key = "queue-key-1"

        inserted = db.enqueue_plugin_run_job(
            meeting_id=sample_meeting.id,
            window_id=f"{sample_meeting.id}:w0001",
            plugin_id="risk_heatmap",
            plugin_version="1.0.0",
            transcript_hash="hash-1",
            idempotency_key=idempotency_key,
            context={"active_intents": ["incident"]},
        )
        assert inserted is True

        inserted_again = db.enqueue_plugin_run_job(
            meeting_id=sample_meeting.id,
            window_id=f"{sample_meeting.id}:w0001",
            plugin_id="risk_heatmap",
            plugin_version="1.0.0",
            transcript_hash="hash-1",
            idempotency_key=idempotency_key,
            context={"active_intents": ["incident"]},
        )
        assert inserted_again is False

        queued = db.list_plugin_run_jobs(status="queued")
        assert len(queued) == 1
        assert queued[0].idempotency_key == idempotency_key
        loaded = db.get_plugin_run_job(queued[0].id)
        assert loaded is not None
        assert loaded.id == queued[0].id
        assert loaded.status == "queued"

        claimed = db.claim_next_plugin_run_job()
        assert claimed is not None
        assert claimed.idempotency_key == idempotency_key
        assert claimed.status == "running"
        assert claimed.attempts == 1

        db.retry_plugin_run_job(
            claimed.id,
            error="Transient failure",
            retry_at=datetime.now() - timedelta(seconds=1),
        )
        claimed_again = db.claim_next_plugin_run_job()
        assert claimed_again is not None
        assert claimed_again.id == claimed.id
        assert claimed_again.attempts == 2
        assert claimed_again.status == "running"

        db.complete_plugin_run_job(claimed_again.id)
        assert db.list_plugin_run_jobs(status="all") == []
        assert db.get_plugin_run_job(claimed_again.id) is None

    def test_plugin_run_job_fail_status(self, db, sample_meeting):
        db.save_meeting(sample_meeting)
        db.enqueue_plugin_run_job(
            meeting_id=sample_meeting.id,
            window_id=f"{sample_meeting.id}:w0002",
            plugin_id="incident_timeline",
            plugin_version="1.1.0",
            transcript_hash="hash-2",
            idempotency_key="queue-key-fail",
            context={"active_intents": ["incident"]},
        )
        claimed = db.claim_next_plugin_run_job()
        assert claimed is not None
        db.fail_plugin_run_job(claimed.id, error="Timed out repeatedly")

        failed = db.list_plugin_run_jobs(status="failed")
        assert len(failed) == 1
        assert failed[0].id == claimed.id
        assert failed[0].status == "failed"
        assert failed[0].last_error == "Timed out repeatedly"

    def test_plugin_run_job_summary_reports_queue_telemetry(self, db, sample_meeting):
        db.save_meeting(sample_meeting)
        for idx in range(1, 5):
            db.enqueue_plugin_run_job(
                meeting_id=sample_meeting.id,
                window_id=f"{sample_meeting.id}:w{idx:04d}",
                plugin_id=f"plugin-{idx}",
                plugin_version="1.0.0",
                transcript_hash=f"hash-{idx}",
                idempotency_key=f"summary-key-{idx}",
                context={"active_intents": ["incident"]},
            )

        running = db.claim_next_plugin_run_job()
        assert running is not None
        failed = db.claim_next_plugin_run_job()
        assert failed is not None
        db.fail_plugin_run_job(failed.id, error="Permanent failure")

        queued = db.list_plugin_run_jobs(status="queued")
        assert len(queued) == 2
        scheduled = queued[0]
        retry_at = datetime.now() + timedelta(minutes=5)
        db.retry_plugin_run_job(scheduled.id, error="Retry later", retry_at=retry_at)

        summary = db.get_plugin_run_job_summary()
        assert summary.total_jobs == 4
        assert summary.queued_jobs == 2
        assert summary.running_jobs == 1
        assert summary.failed_jobs == 1
        assert summary.queued_due_jobs == 1
        assert summary.scheduled_retry_jobs == 1
        assert summary.next_retry_at is not None

    def test_claim_next_plugin_run_job_can_include_scheduled(self, db, sample_meeting):
        db.save_meeting(sample_meeting)
        db.enqueue_plugin_run_job(
            meeting_id=sample_meeting.id,
            window_id=f"{sample_meeting.id}:w-scheduled",
            plugin_id="incident_timeline",
            plugin_version="1.0.0",
            transcript_hash="hash-scheduled",
            idempotency_key="queue-key-scheduled",
            context={"active_intents": ["incident"]},
        )

        queued = db.list_plugin_run_jobs(status="queued")
        assert len(queued) == 1
        retry_at = datetime.now() + timedelta(minutes=10)
        db.retry_plugin_run_job(queued[0].id, error="retry later", retry_at=retry_at)

        assert db.claim_next_plugin_run_job() is None
        claimed = db.claim_next_plugin_run_job(include_scheduled=True)
        assert claimed is not None
        assert claimed.id == queued[0].id
        assert claimed.status == "running"


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
