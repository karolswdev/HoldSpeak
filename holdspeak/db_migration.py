"""Migration utility to import existing JSON meetings into SQLite."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from .db import MeetingDatabase, get_database
from .meeting_session import (
    MeetingState, TranscriptSegment, Bookmark, IntelSnapshot
)
from .logging_config import get_logger

log = get_logger("db_migration")

DEFAULT_JSON_DIR = Path.home() / ".local" / "share" / "holdspeak" / "meetings"


def migrate_json_meetings(
    json_dir: Optional[Path] = None,
    db: Optional[MeetingDatabase] = None,
    dry_run: bool = False,
) -> tuple[int, int, list[str]]:
    """
    Migrate all JSON meeting files to SQLite database.

    Args:
        json_dir: Directory containing JSON meeting files.
        db: Database instance to use (defaults to singleton).
        dry_run: If True, only report what would be migrated.

    Returns:
        Tuple of (migrated_count, skipped_count, error_messages)
    """
    json_dir = json_dir or DEFAULT_JSON_DIR
    db = db or get_database()

    if not json_dir.exists():
        log.info(f"No JSON directory found at {json_dir}")
        return 0, 0, []

    json_files = list(json_dir.glob("meeting_*.json"))
    log.info(f"Found {len(json_files)} JSON meeting files to migrate")

    migrated = 0
    skipped = 0
    errors: list[str] = []

    for json_file in json_files:
        try:
            meeting_state = load_json_meeting(json_file)

            if dry_run:
                log.info(f"[DRY RUN] Would migrate: {meeting_state.id}")
                migrated += 1
                continue

            # Check if already exists
            existing = db.get_meeting(meeting_state.id)
            if existing:
                log.debug(f"Meeting {meeting_state.id} already exists, skipping")
                skipped += 1
                continue

            db.save_meeting(meeting_state)
            migrated += 1
            log.info(f"Migrated meeting: {meeting_state.id}")

        except Exception as e:
            error_msg = f"Failed to migrate {json_file.name}: {e}"
            log.error(error_msg)
            errors.append(error_msg)

    return migrated, skipped, errors


def load_json_meeting(json_file: Path) -> MeetingState:
    """Load a meeting from JSON file.

    Args:
        json_file: Path to JSON meeting file.

    Returns:
        MeetingState object.
    """
    with open(json_file) as f:
        data = json.load(f)

    # Parse segments
    segments = [
        TranscriptSegment(
            text=s['text'],
            speaker=s['speaker'],
            start_time=s['start_time'],
            end_time=s['end_time'],
            is_bookmarked=s.get('is_bookmarked', False),
        )
        for s in data.get('segments', [])
    ]

    # Parse bookmarks
    bookmarks = [
        Bookmark(
            timestamp=b['timestamp'],
            label=b.get('label', ''),
            created_at=_parse_datetime(b.get('created_at')) or datetime.now(),
        )
        for b in data.get('bookmarks', [])
    ]

    # Parse intel
    intel = None
    if data.get('intel'):
        intel_data = data['intel']
        action_items = []
        for a in intel_data.get('action_items', []):
            # Store as dict with all fields
            action_items.append({
                'id': a.get('id', ''),
                'task': a.get('task', ''),
                'owner': a.get('owner'),
                'due': a.get('due'),
                'status': a.get('status', 'pending'),
                'source_timestamp': a.get('source_timestamp'),
                'created_at': a.get('created_at', datetime.now().isoformat()),
                'completed_at': a.get('completed_at'),
            })

        intel = IntelSnapshot(
            timestamp=intel_data.get('timestamp', 0),
            topics=intel_data.get('topics', []),
            action_items=action_items,
            summary=intel_data.get('summary', ''),
        )

    return MeetingState(
        id=data['id'],
        started_at=_parse_datetime(data['started_at']) or datetime.now(),
        ended_at=_parse_datetime(data.get('ended_at')),
        title=data.get('title'),
        tags=data.get('tags', []),
        segments=segments,
        bookmarks=bookmarks,
        intel=intel,
        mic_label=data.get('mic_label', 'Me'),
        remote_label=data.get('remote_label', 'Remote'),
        web_url=data.get('web_url'),
    )


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    """Parse ISO datetime string, returning None on failure."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None


def list_json_meetings(json_dir: Optional[Path] = None) -> list[tuple[Path, str, datetime]]:
    """List all JSON meeting files with basic info.

    Args:
        json_dir: Directory to scan (defaults to standard location).

    Returns:
        List of (file_path, meeting_id, started_at) tuples.
    """
    json_dir = json_dir or DEFAULT_JSON_DIR

    if not json_dir.exists():
        return []

    results = []
    for json_file in json_dir.glob("meeting_*.json"):
        try:
            with open(json_file) as f:
                data = json.load(f)
            meeting_id = data.get('id', 'unknown')
            started_at = _parse_datetime(data.get('started_at')) or datetime.now()
            results.append((json_file, meeting_id, started_at))
        except Exception:
            continue

    return sorted(results, key=lambda x: x[2], reverse=True)
