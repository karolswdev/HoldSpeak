"""Saved meeting service functions for the TUI layer."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from ... import db as db_module
from ...db import MeetingSummary
from ...meeting_exports import write_meeting_export
from ...meeting_session import MeetingState


def list_saved_meetings(
    *, limit: int = 50, offset: int = 0, date_from: Optional[datetime] = None
) -> list[MeetingSummary]:
    """List saved meeting summaries for TUI views."""
    db = db_module.get_database()
    try:
        return db.list_meetings(limit=limit, offset=offset, date_from=date_from)
    except TypeError:
        # Some tests use lightweight DB stubs that predate the offset parameter.
        return db.list_meetings(limit=limit, date_from=date_from)


def search_saved_meetings(
    search_query: str, *, limit: int = 100, date_from: Optional[datetime] = None
) -> list[MeetingSummary]:
    """Search saved meetings by transcript content and return matching summaries."""
    db = db_module.get_database()
    results = db.search_transcripts(search_query, limit=limit)
    meeting_ids = list(dict.fromkeys(r[0] for r in results))
    all_meetings = db.list_meetings(limit=limit, date_from=date_from)
    return [meeting for meeting in all_meetings if meeting.id in meeting_ids]


def get_saved_meeting(meeting_id: str) -> Optional[MeetingState]:
    """Load a saved meeting by id."""
    db = db_module.get_database()
    return db.get_meeting(meeting_id)


def update_saved_meeting_metadata(meeting_id: str, title: str, tags: list[str]) -> bool:
    """Update metadata for a saved meeting."""
    db = db_module.get_database()
    return db.update_meeting_metadata(meeting_id, title, tags)


def delete_saved_meeting(meeting_id: str) -> bool:
    """Delete a saved meeting."""
    db = db_module.get_database()
    return db.delete_meeting(meeting_id)


def export_saved_meeting_markdown(
    meeting_id: str, destination_dir: Optional[Path] = None
) -> Optional[Path]:
    """Export a saved meeting to markdown and return the written path."""
    meeting = get_saved_meeting(meeting_id)
    if meeting is None:
        return None

    return write_meeting_export(
        meeting,
        "markdown",
        destination_dir=destination_dir,
    )
