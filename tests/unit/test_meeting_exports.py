"""Unit tests for shared meeting export helpers."""

from __future__ import annotations

import json
from datetime import datetime
from types import SimpleNamespace

import pytest

from holdspeak.meeting_exports import write_meeting_export
from holdspeak.meeting_session import Bookmark, IntelSnapshot, MeetingState, TranscriptSegment


@pytest.fixture
def sample_meeting() -> MeetingState:
    """Create a representative meeting for export tests."""
    return MeetingState(
        id="export123456",
        started_at=datetime(2024, 1, 15, 10, 0, 0),
        ended_at=datetime(2024, 1, 15, 11, 0, 0),
        title="Export Test Meeting",
        tags=["important", "demo"],
        segments=[
            TranscriptSegment(
                text="First segment",
                speaker="Me",
                start_time=0.0,
                end_time=3.0,
                is_bookmarked=True,
            ),
            TranscriptSegment(
                text="Second segment",
                speaker="Remote",
                start_time=4.0,
                end_time=7.0,
            ),
        ],
        bookmarks=[Bookmark(timestamp=5.0, label="Key moment")],
        intel=IntelSnapshot(
            timestamp=60.0,
            topics=["Planning", "Timeline"],
            action_items=[
                {
                    "id": "action1",
                    "task": "Send follow-up",
                    "owner": "Me",
                    "due": "Friday",
                    "status": "done",
                    "review_state": "accepted",
                    "source_timestamp": 125.5,
                }
            ],
            summary="Discussed the project plan.",
        ),
        mic_label="Me",
        remote_label="Remote",
    )


def test_write_meeting_export_markdown_includes_shared_sections(
    sample_meeting: MeetingState, tmp_path
) -> None:
    """Markdown exports should include the richer shared meeting sections."""
    filepath = write_meeting_export(sample_meeting, "markdown", destination_dir=tmp_path)

    assert filepath.suffix == ".md"
    exported = filepath.read_text(encoding="utf-8")
    assert "# Export Test Meeting" in exported
    assert "## Summary" in exported
    assert "## Topics" in exported
    assert "- [x] Send follow-up (@Me) - due Friday; review accepted; source 02:05" in exported
    assert "## Tags" in exported
    assert "## Bookmarks" in exported
    assert "**[BOOKMARK]**" in exported


def test_write_meeting_export_markdown_includes_artifacts(
    sample_meeting: MeetingState, tmp_path
) -> None:
    """Markdown handoff exports should include synthesized artifact context."""
    artifact = SimpleNamespace(
        id="artifact-1",
        meeting_id=sample_meeting.id,
        artifact_type="requirements",
        title="API Requirements",
        body_markdown="### Requirements\n\n- Define acceptance criteria.",
        structured_json={"items": 1},
        confidence=0.82,
        status="needs_review",
        plugin_id="requirements_extractor",
        plugin_version="1.0",
        sources=[{"source_type": "window", "source_ref": "w-1"}],
        created_at=datetime(2024, 1, 15, 10, 30, 0),
        updated_at=datetime(2024, 1, 15, 10, 31, 0),
    )

    filepath = write_meeting_export(
        sample_meeting,
        "markdown",
        destination_dir=tmp_path,
        artifacts=[artifact],
    )

    exported = filepath.read_text(encoding="utf-8")
    assert "## Artifacts" in exported
    assert "### API Requirements" in exported
    assert "*requirements; needs_review; 82% confidence; 1 sources*" in exported
    assert "- Define acceptance criteria." in exported


def test_write_meeting_export_text_contains_transcript(
    sample_meeting: MeetingState, tmp_path
) -> None:
    """Text exports should contain the transcript-oriented plain-text format."""
    filepath = write_meeting_export(sample_meeting, "txt", destination_dir=tmp_path)

    assert filepath.suffix == ".txt"
    exported = filepath.read_text(encoding="utf-8")
    assert "Meeting: Export Test Meeting" in exported
    assert "Transcript:" in exported
    assert "[0s] Me: First segment *" in exported


def test_write_meeting_export_json_round_trips_state(
    sample_meeting: MeetingState, tmp_path
) -> None:
    """JSON exports should serialize the meeting state payload."""
    filepath = write_meeting_export(sample_meeting, "json", destination_dir=tmp_path)

    assert filepath.suffix == ".json"
    payload = json.loads(filepath.read_text(encoding="utf-8"))
    assert payload["id"] == sample_meeting.id
    assert payload["title"] == sample_meeting.title
    assert payload["intel"]["summary"] == "Discussed the project plan."


def test_write_meeting_export_json_can_include_artifacts(
    sample_meeting: MeetingState, tmp_path
) -> None:
    """JSON handoff exports should preserve artifact payloads without wrapping the meeting."""
    artifact = {
        "id": "artifact-1",
        "meeting_id": sample_meeting.id,
        "artifact_type": "requirements",
        "title": "API Requirements",
        "body_markdown": "body",
        "structured_json": {"items": 1},
        "confidence": 0.82,
        "status": "needs_review",
        "plugin_id": "requirements_extractor",
        "plugin_version": "1.0",
        "sources": [{"source_type": "window", "source_ref": "w-1"}],
        "created_at": "2024-01-15T10:30:00",
        "updated_at": "2024-01-15T10:31:00",
    }

    filepath = write_meeting_export(
        sample_meeting,
        "json",
        destination_dir=tmp_path,
        artifacts=[artifact],
    )

    payload = json.loads(filepath.read_text(encoding="utf-8"))
    assert payload["id"] == sample_meeting.id
    assert payload["artifacts"][0]["title"] == "API Requirements"
    assert payload["artifacts"][0]["sources"][0]["source_ref"] == "w-1"


def test_write_meeting_export_rejects_invalid_format(
    sample_meeting: MeetingState, tmp_path
) -> None:
    """Unsupported export formats should fail fast."""
    with pytest.raises(ValueError, match="Unsupported export format"):
        write_meeting_export(sample_meeting, "pdf", destination_dir=tmp_path)  # type: ignore[arg-type]
