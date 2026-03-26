"""SQLite database persistence for HoldSpeak meetings."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Iterator, Any

from .logging_config import get_logger

log = get_logger("db")

# Default database location
DEFAULT_DB_PATH = Path.home() / ".local" / "share" / "holdspeak" / "holdspeak.db"
SCHEMA_VERSION = 3

# SQL Schema
SCHEMA_SQL = """
-- Enable foreign keys
PRAGMA foreign_keys = ON;

-- Schema version for migrations
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Meetings table (core entity)
CREATE TABLE IF NOT EXISTS meetings (
    id TEXT PRIMARY KEY,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    title TEXT,
    duration_seconds REAL,
    mic_label TEXT NOT NULL DEFAULT 'Me',
    remote_label TEXT NOT NULL DEFAULT 'Remote',
    web_url TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Tags for meetings (many-to-many)
CREATE TABLE IF NOT EXISTS meeting_tags (
    meeting_id TEXT NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    tag TEXT NOT NULL,
    PRIMARY KEY (meeting_id, tag)
);

-- Transcript segments
CREATE TABLE IF NOT EXISTS segments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meeting_id TEXT NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    speaker TEXT NOT NULL,
    speaker_id TEXT REFERENCES speakers(id),
    start_time REAL NOT NULL,
    end_time REAL NOT NULL,
    is_bookmarked INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Bookmarks
CREATE TABLE IF NOT EXISTS bookmarks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meeting_id TEXT NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    timestamp REAL NOT NULL,
    label TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Action Items (first-class entity for cross-meeting tracking)
CREATE TABLE IF NOT EXISTS action_items (
    id TEXT PRIMARY KEY,
    meeting_id TEXT NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    task TEXT NOT NULL,
    owner TEXT,
    due TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    source_timestamp REAL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at TEXT
);

-- Topics extracted from meetings
CREATE TABLE IF NOT EXISTS topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meeting_id TEXT NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    topic TEXT NOT NULL,
    extracted_at REAL NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Intel snapshots (historical record of intel extractions)
CREATE TABLE IF NOT EXISTS intel_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meeting_id TEXT NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    timestamp REAL NOT NULL,
    summary TEXT NOT NULL DEFAULT '',
    raw_response TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Speaker identities for cross-meeting recognition
CREATE TABLE IF NOT EXISTS speakers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL DEFAULT 'Unknown',
    avatar TEXT,
    embedding BLOB NOT NULL,
    sample_count INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Full-text search for transcripts
CREATE VIRTUAL TABLE IF NOT EXISTS segments_fts USING fts5(
    text,
    speaker,
    content=segments,
    content_rowid=id
);

-- Triggers to keep FTS index in sync
CREATE TRIGGER IF NOT EXISTS segments_ai AFTER INSERT ON segments BEGIN
    INSERT INTO segments_fts(rowid, text, speaker)
    VALUES (NEW.id, NEW.text, NEW.speaker);
END;

CREATE TRIGGER IF NOT EXISTS segments_ad AFTER DELETE ON segments BEGIN
    INSERT INTO segments_fts(segments_fts, rowid, text, speaker)
    VALUES('delete', OLD.id, OLD.text, OLD.speaker);
END;

CREATE TRIGGER IF NOT EXISTS segments_au AFTER UPDATE ON segments BEGIN
    INSERT INTO segments_fts(segments_fts, rowid, text, speaker)
    VALUES('delete', OLD.id, OLD.text, OLD.speaker);
    INSERT INTO segments_fts(rowid, text, speaker)
    VALUES (NEW.id, NEW.text, NEW.speaker);
END;

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_segments_meeting ON segments(meeting_id);
CREATE INDEX IF NOT EXISTS idx_segments_speaker ON segments(speaker);
CREATE INDEX IF NOT EXISTS idx_segments_time ON segments(meeting_id, start_time);
CREATE INDEX IF NOT EXISTS idx_bookmarks_meeting ON bookmarks(meeting_id);
CREATE INDEX IF NOT EXISTS idx_action_items_meeting ON action_items(meeting_id);
CREATE INDEX IF NOT EXISTS idx_action_items_status ON action_items(status);
CREATE INDEX IF NOT EXISTS idx_action_items_owner ON action_items(owner);
CREATE INDEX IF NOT EXISTS idx_topics_meeting ON topics(meeting_id);
CREATE INDEX IF NOT EXISTS idx_meetings_date ON meetings(started_at);
CREATE INDEX IF NOT EXISTS idx_segments_speaker_id ON segments(speaker_id);
CREATE INDEX IF NOT EXISTS idx_speakers_name ON speakers(name);
"""


@dataclass
class MeetingSummary:
    """Lightweight meeting summary for list views."""
    id: str
    started_at: datetime
    ended_at: Optional[datetime]
    title: Optional[str]
    duration_seconds: float
    segment_count: int
    action_item_count: int
    tags: list[str]


@dataclass
class ActionItemSummary:
    """Action item with meeting context."""
    id: str
    task: str
    owner: Optional[str]
    due: Optional[str]
    status: str
    meeting_id: str
    meeting_title: Optional[str]
    meeting_date: datetime
    created_at: datetime
    completed_at: Optional[datetime]


class MeetingDatabase:
    """SQLite database manager for meeting persistence."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DEFAULT_DB_PATH
        self._ensure_schema()

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        """Context manager for database connections."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _ensure_schema(self) -> None:
        """Create or migrate database schema."""
        with self._connection() as conn:
            # Check current version
            try:
                row = conn.execute(
                    "SELECT MAX(version) FROM schema_version"
                ).fetchone()
                current_version = row[0] if row and row[0] else 0
            except sqlite3.OperationalError:
                current_version = 0

            if current_version < SCHEMA_VERSION:
                self._apply_schema(conn, current_version)

    def _apply_schema(self, conn: sqlite3.Connection, from_version: int) -> None:
        """Apply schema migrations."""
        # For existing databases, run migrations FIRST to add columns
        # before the schema script tries to create indexes on them
        if from_version >= 1:
            # Migration v1 -> v2: Add speaker_id column and speakers table
            if from_version < 2:
                try:
                    conn.execute("SELECT speaker_id FROM segments LIMIT 1")
                except sqlite3.OperationalError:
                    log.info("Migrating segments table: adding speaker_id column")
                    conn.execute("ALTER TABLE segments ADD COLUMN speaker_id TEXT")

                # Create speakers table if not exists
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS speakers (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL DEFAULT 'Unknown',
                        embedding BLOB NOT NULL,
                        sample_count INTEGER NOT NULL DEFAULT 1,
                        created_at TEXT NOT NULL DEFAULT (datetime('now')),
                        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
                    )
                """)

            # Migration v2 -> v3: Add avatar column to speakers
            if from_version < 3:
                try:
                    conn.execute("SELECT avatar FROM speakers LIMIT 1")
                except sqlite3.OperationalError:
                    log.info("Migrating speakers table: adding avatar column")
                    conn.execute("ALTER TABLE speakers ADD COLUMN avatar TEXT")

        # Now apply the full schema (creates tables/indexes that don't exist)
        conn.executescript(SCHEMA_SQL)

        conn.execute(
            "INSERT OR REPLACE INTO schema_version (version) VALUES (?)",
            (SCHEMA_VERSION,)
        )
        log.info(f"Database schema updated to version {SCHEMA_VERSION}")

    # === Meeting CRUD ===

    def save_meeting(self, state: "MeetingState") -> None:
        """Save or update a meeting and all related data."""
        from .meeting_session import TranscriptSegment, Bookmark, IntelSnapshot

        with self._connection() as conn:
            # Upsert meeting
            conn.execute("""
                INSERT INTO meetings (id, started_at, ended_at, title,
                    duration_seconds, mic_label, remote_label, web_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    ended_at = excluded.ended_at,
                    title = excluded.title,
                    duration_seconds = excluded.duration_seconds,
                    updated_at = datetime('now')
            """, (
                state.id,
                state.started_at.isoformat(),
                state.ended_at.isoformat() if state.ended_at else None,
                state.title,
                state.duration if state.ended_at else None,
                state.mic_label,
                state.remote_label,
                state.web_url,
            ))

            # Save tags
            conn.execute(
                "DELETE FROM meeting_tags WHERE meeting_id = ?", (state.id,)
            )
            for tag in state.tags:
                conn.execute(
                    "INSERT INTO meeting_tags (meeting_id, tag) VALUES (?, ?)",
                    (state.id, tag)
                )

            # Save segments
            self._save_segments(conn, state.id, state.segments)

            # Save bookmarks
            self._save_bookmarks(conn, state.id, state.bookmarks)

            # Save intel
            if state.intel:
                self._save_intel(conn, state.id, state.intel)

        log.info(f"Meeting {state.id} saved to database")

    def _save_segments(
        self, conn: sqlite3.Connection, meeting_id: str,
        segments: list
    ) -> None:
        """Save transcript segments."""
        # Delete existing segments and re-insert
        conn.execute("DELETE FROM segments WHERE meeting_id = ?", (meeting_id,))
        for seg in segments:
            speaker_id = getattr(seg, 'speaker_id', None)
            conn.execute("""
                INSERT INTO segments
                (meeting_id, text, speaker, speaker_id, start_time, end_time, is_bookmarked)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                meeting_id, seg.text, seg.speaker, speaker_id,
                seg.start_time, seg.end_time, int(seg.is_bookmarked)
            ))

    def _save_bookmarks(
        self, conn: sqlite3.Connection, meeting_id: str,
        bookmarks: list
    ) -> None:
        """Save bookmarks."""
        conn.execute("DELETE FROM bookmarks WHERE meeting_id = ?", (meeting_id,))
        for bm in bookmarks:
            conn.execute("""
                INSERT INTO bookmarks (meeting_id, timestamp, label, created_at)
                VALUES (?, ?, ?, ?)
            """, (meeting_id, bm.timestamp, bm.label, bm.created_at.isoformat()))

    def _save_intel(
        self, conn: sqlite3.Connection, meeting_id: str,
        intel: "IntelSnapshot"
    ) -> None:
        """Save intel snapshot with action items and topics."""
        # Save intel snapshot
        conn.execute("""
            INSERT INTO intel_snapshots (meeting_id, timestamp, summary)
            VALUES (?, ?, ?)
        """, (meeting_id, intel.timestamp, intel.summary))

        # Save topics (replace all)
        conn.execute("DELETE FROM topics WHERE meeting_id = ?", (meeting_id,))
        for topic in intel.topics:
            conn.execute("""
                INSERT INTO topics (meeting_id, topic, extracted_at)
                VALUES (?, ?, ?)
            """, (meeting_id, topic, intel.timestamp))

        # Upsert action items (preserve status across extractions)
        for item in intel.action_items:
            if hasattr(item, 'id'):
                action_item = item
                item_id = action_item.id
                task = action_item.task
                owner = action_item.owner
                due = action_item.due
                status = action_item.status
                source_timestamp = getattr(action_item, 'source_timestamp', None)
                created_at = getattr(action_item, 'created_at', datetime.now().isoformat())
                completed_at = getattr(action_item, 'completed_at', None)
            else:
                # Dict format
                item_id = item.get('id', '')
                task = item.get('task', '')
                owner = item.get('owner')
                due = item.get('due')
                status = item.get('status', 'pending')
                source_timestamp = item.get('source_timestamp')
                created_at = item.get('created_at', datetime.now().isoformat())
                completed_at = item.get('completed_at')

            if not item_id:
                continue

            conn.execute("""
                INSERT INTO action_items
                (id, meeting_id, task, owner, due, status, source_timestamp,
                 created_at, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    status = excluded.status,
                    completed_at = excluded.completed_at
            """, (
                item_id,
                meeting_id,
                task,
                owner,
                due,
                status,
                source_timestamp,
                created_at,
                completed_at,
            ))

    def get_meeting(self, meeting_id: str) -> Optional["MeetingState"]:
        """Load a complete meeting by ID."""
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM meetings WHERE id = ?", (meeting_id,)
            ).fetchone()

            if not row:
                return None

            return self._row_to_meeting_state(conn, row)

    def _row_to_meeting_state(
        self, conn: sqlite3.Connection, row: sqlite3.Row
    ) -> "MeetingState":
        """Convert database row to MeetingState with related data."""
        from .meeting_session import MeetingState, TranscriptSegment, Bookmark, IntelSnapshot

        meeting_id = row['id']

        # Load segments
        segments = [
            TranscriptSegment(
                text=r['text'],
                speaker=r['speaker'],
                start_time=r['start_time'],
                end_time=r['end_time'],
                is_bookmarked=bool(r['is_bookmarked']),
                speaker_id=r['speaker_id'],
            )
            for r in conn.execute(
                "SELECT * FROM segments WHERE meeting_id = ? ORDER BY start_time",
                (meeting_id,)
            )
        ]

        # Load bookmarks
        bookmarks = [
            Bookmark(
                timestamp=r['timestamp'],
                label=r['label'],
                created_at=datetime.fromisoformat(r['created_at']),
            )
            for r in conn.execute(
                "SELECT * FROM bookmarks WHERE meeting_id = ? ORDER BY timestamp",
                (meeting_id,)
            )
        ]

        # Load tags
        tags = [
            r['tag'] for r in conn.execute(
                "SELECT tag FROM meeting_tags WHERE meeting_id = ?",
                (meeting_id,)
            )
        ]

        # Load latest intel
        intel = self._load_latest_intel(conn, meeting_id)

        return MeetingState(
            id=meeting_id,
            started_at=datetime.fromisoformat(row['started_at']),
            ended_at=datetime.fromisoformat(row['ended_at']) if row['ended_at'] else None,
            title=row['title'],
            tags=tags,
            segments=segments,
            bookmarks=bookmarks,
            intel=intel,
            mic_label=row['mic_label'],
            remote_label=row['remote_label'],
            web_url=row['web_url'],
        )

    def _load_latest_intel(
        self, conn: sqlite3.Connection, meeting_id: str
    ) -> Optional["IntelSnapshot"]:
        """Load the most recent intel snapshot for a meeting."""
        from .meeting_session import IntelSnapshot

        row = conn.execute("""
            SELECT * FROM intel_snapshots
            WHERE meeting_id = ?
            ORDER BY timestamp DESC LIMIT 1
        """, (meeting_id,)).fetchone()

        if not row:
            return None

        # Load topics
        topics = [
            r['topic'] for r in conn.execute(
                "SELECT topic FROM topics WHERE meeting_id = ?",
                (meeting_id,)
            )
        ]

        # Load action items
        action_items = []
        for r in conn.execute(
            "SELECT * FROM action_items WHERE meeting_id = ?",
            (meeting_id,)
        ):
            # Return as dicts for compatibility
            action_items.append({
                'id': r['id'],
                'task': r['task'],
                'owner': r['owner'],
                'due': r['due'],
                'status': r['status'],
                'source_timestamp': r['source_timestamp'],
                'created_at': r['created_at'],
                'completed_at': r['completed_at'],
            })

        return IntelSnapshot(
            timestamp=row['timestamp'],
            topics=topics,
            action_items=action_items,
            summary=row['summary'],
        )

    # === Query Methods ===

    def list_meetings(
        self,
        limit: int = 50,
        offset: int = 0,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        tag: Optional[str] = None,
    ) -> list[MeetingSummary]:
        """List meetings with optional filters."""
        with self._connection() as conn:
            query = """
                SELECT m.*,
                    (SELECT COUNT(*) FROM segments WHERE meeting_id = m.id) as segment_count,
                    (SELECT COUNT(*) FROM action_items WHERE meeting_id = m.id) as action_count,
                    (SELECT GROUP_CONCAT(tag) FROM meeting_tags WHERE meeting_id = m.id) as tags
                FROM meetings m
                WHERE 1=1
            """
            params: list[Any] = []

            if date_from:
                query += " AND m.started_at >= ?"
                params.append(date_from.isoformat())
            if date_to:
                query += " AND m.started_at <= ?"
                params.append(date_to.isoformat())
            if tag:
                query += " AND m.id IN (SELECT meeting_id FROM meeting_tags WHERE tag = ?)"
                params.append(tag)

            query += " ORDER BY m.started_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            return [
                MeetingSummary(
                    id=r['id'],
                    started_at=datetime.fromisoformat(r['started_at']),
                    ended_at=datetime.fromisoformat(r['ended_at']) if r['ended_at'] else None,
                    title=r['title'],
                    duration_seconds=r['duration_seconds'] or 0.0,
                    segment_count=r['segment_count'],
                    action_item_count=r['action_count'],
                    tags=r['tags'].split(',') if r['tags'] else [],
                )
                for r in conn.execute(query, params)
            ]

    def list_action_items(
        self,
        include_completed: bool = False,
        meeting_id: Optional[str] = None,
        owner: Optional[str] = None,
    ) -> list[ActionItemSummary]:
        """List action items with optional filters."""
        with self._connection() as conn:
            query = """
                SELECT a.*, m.title as meeting_title, m.started_at as meeting_date
                FROM action_items a
                JOIN meetings m ON a.meeting_id = m.id
                WHERE 1=1
            """
            params: list[Any] = []

            if not include_completed:
                query += " AND a.status = 'pending'"
            if meeting_id:
                query += " AND a.meeting_id = ?"
                params.append(meeting_id)
            if owner:
                query += " AND a.owner = ?"
                params.append(owner)

            query += " ORDER BY a.created_at DESC"

            return [
                ActionItemSummary(
                    id=r['id'],
                    task=r['task'],
                    owner=r['owner'],
                    due=r['due'],
                    status=r['status'],
                    meeting_id=r['meeting_id'],
                    meeting_title=r['meeting_title'],
                    meeting_date=datetime.fromisoformat(r['meeting_date']),
                    created_at=datetime.fromisoformat(r['created_at']),
                    completed_at=datetime.fromisoformat(r['completed_at']) if r['completed_at'] else None,
                )
                for r in conn.execute(query, params)
            ]

    def update_action_item_status(
        self, item_id: str, status: str
    ) -> bool:
        """Update action item status. Returns True if found."""
        with self._connection() as conn:
            completed_at = datetime.now().isoformat() if status in ('done', 'dismissed') else None
            result = conn.execute("""
                UPDATE action_items
                SET status = ?, completed_at = ?
                WHERE id = ?
            """, (status, completed_at, item_id))
            return result.rowcount > 0

    def search_transcripts(
        self, query: str, limit: int = 100
    ) -> list[tuple[str, "TranscriptSegment"]]:
        """Full-text search across all transcripts. Returns (meeting_id, segment) tuples."""
        from .meeting_session import TranscriptSegment

        with self._connection() as conn:
            results = []
            for r in conn.execute("""
                SELECT s.meeting_id, s.text, s.speaker, s.start_time, s.end_time, s.is_bookmarked
                FROM segments_fts
                JOIN segments s ON segments_fts.rowid = s.id
                WHERE segments_fts MATCH ?
                ORDER BY rank
                LIMIT ?
            """, (query, limit)):
                segment = TranscriptSegment(
                    text=r['text'],
                    speaker=r['speaker'],
                    start_time=r['start_time'],
                    end_time=r['end_time'],
                    is_bookmarked=bool(r['is_bookmarked']),
                )
                results.append((r['meeting_id'], segment))
            return results

    def update_action_item_status(self, action_id: str, status: str) -> bool:
        """Update action item status. Returns True if found."""
        with self._connection() as conn:
            completed_at = (
                "datetime('now')" if status == "done" else "NULL"
            )
            result = conn.execute(
                f"""UPDATE action_items
                   SET status = ?, completed_at = {completed_at}
                   WHERE id = ?""",
                (status, action_id),
            )
            return result.rowcount > 0

    def update_meeting_metadata(
        self, meeting_id: str, title: str, tags: list[str]
    ) -> bool:
        """Update meeting title and tags. Returns True if found."""
        with self._connection() as conn:
            # Update title
            result = conn.execute(
                "UPDATE meetings SET title = ?, updated_at = datetime('now') WHERE id = ?",
                (title if title else None, meeting_id),
            )
            if result.rowcount == 0:
                return False

            # Update tags: delete existing and insert new
            conn.execute("DELETE FROM meeting_tags WHERE meeting_id = ?", (meeting_id,))
            if tags:
                conn.executemany(
                    "INSERT INTO meeting_tags (meeting_id, tag) VALUES (?, ?)",
                    [(meeting_id, tag) for tag in tags],
                )
            return True

    def delete_meeting(self, meeting_id: str) -> bool:
        """Delete a meeting and all related data. Returns True if found."""
        with self._connection() as conn:
            result = conn.execute(
                "DELETE FROM meetings WHERE id = ?", (meeting_id,)
            )
            return result.rowcount > 0

    def get_meeting_count(self) -> int:
        """Get total number of meetings in database."""
        with self._connection() as conn:
            row = conn.execute("SELECT COUNT(*) FROM meetings").fetchone()
            return row[0] if row else 0

    # === Speaker Methods ===

    def save_speaker(self, speaker: "SpeakerEmbedding") -> None:
        """Save or update a speaker identity.

        Args:
            speaker: SpeakerEmbedding to save.
        """
        import numpy as np
        with self._connection() as conn:
            embedding_blob = speaker.embedding.astype(np.float32).tobytes()
            conn.execute("""
                INSERT INTO speakers (id, name, avatar, embedding, sample_count)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    avatar = excluded.avatar,
                    embedding = excluded.embedding,
                    sample_count = excluded.sample_count,
                    updated_at = datetime('now')
            """, (
                speaker.id,
                speaker.name,
                speaker.avatar,
                embedding_blob,
                speaker.sample_count,
            ))
            log.debug(f"Saved speaker {speaker.id}: {speaker.name} {speaker.avatar}")

    def get_all_speakers(self) -> list["SpeakerEmbedding"]:
        """Load all known speaker identities.

        Returns:
            List of SpeakerEmbedding objects.
        """
        import numpy as np
        from .speaker_intel import SpeakerEmbedding

        with self._connection() as conn:
            speakers = []
            for row in conn.execute("SELECT * FROM speakers"):
                embedding = np.frombuffer(row['embedding'], dtype=np.float32)
                speakers.append(SpeakerEmbedding(
                    id=row['id'],
                    name=row['name'],
                    embedding=embedding,
                    sample_count=row['sample_count'],
                    avatar=row['avatar'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                ))
            return speakers

    def get_speaker(self, speaker_id: str) -> Optional["SpeakerEmbedding"]:
        """Get a specific speaker by ID.

        Args:
            speaker_id: The speaker's unique ID.

        Returns:
            SpeakerEmbedding if found, None otherwise.
        """
        import numpy as np
        from .speaker_intel import SpeakerEmbedding

        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM speakers WHERE id = ?", (speaker_id,)
            ).fetchone()

            if row:
                embedding = np.frombuffer(row['embedding'], dtype=np.float32)
                return SpeakerEmbedding(
                    id=row['id'],
                    name=row['name'],
                    embedding=embedding,
                    sample_count=row['sample_count'],
                    avatar=row['avatar'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                )
            return None

    def update_speaker_name(self, speaker_id: str, name: str) -> bool:
        """Rename a speaker identity.

        Args:
            speaker_id: The speaker's unique ID.
            name: New display name.

        Returns:
            True if speaker found and updated.
        """
        with self._connection() as conn:
            result = conn.execute(
                "UPDATE speakers SET name = ?, updated_at = datetime('now') WHERE id = ?",
                (name, speaker_id)
            )
            if result.rowcount > 0:
                log.info(f"Updated speaker {speaker_id} name to '{name}'")
                return True
            return False

    def update_speaker_avatar(self, speaker_id: str, avatar: str) -> bool:
        """Update a speaker's avatar emoji.

        Args:
            speaker_id: The speaker's unique ID.
            avatar: New avatar emoji.

        Returns:
            True if speaker found and updated.
        """
        with self._connection() as conn:
            result = conn.execute(
                "UPDATE speakers SET avatar = ?, updated_at = datetime('now') WHERE id = ?",
                (avatar, speaker_id)
            )
            if result.rowcount > 0:
                log.info(f"Updated speaker {speaker_id} avatar to '{avatar}'")
                return True
            return False

    def delete_speaker(self, speaker_id: str) -> bool:
        """Delete a speaker identity.

        Note: This does not cascade to segments - speaker_id in segments
        will become orphaned but speaker text label remains.

        Args:
            speaker_id: The speaker's unique ID.

        Returns:
            True if speaker found and deleted.
        """
        with self._connection() as conn:
            result = conn.execute(
                "DELETE FROM speakers WHERE id = ?", (speaker_id,)
            )
            if result.rowcount > 0:
                log.info(f"Deleted speaker {speaker_id}")
                return True
            return False

    def get_speaker_count(self) -> int:
        """Get total number of known speakers."""
        with self._connection() as conn:
            row = conn.execute("SELECT COUNT(*) FROM speakers").fetchone()
            return row[0] if row else 0

    def get_speaker_segments(
        self, speaker_id: str, limit: int = 500
    ) -> list[dict]:
        """Get all segments for a speaker grouped by meeting.

        Args:
            speaker_id: The speaker's unique ID.
            limit: Maximum total segments to return.

        Returns:
            List of meeting groups, each containing:
            {
                "meeting_id": str,
                "meeting_title": str | None,
                "meeting_date": datetime,
                "meeting_duration": float | None,
                "segments": list of segment dicts
            }
        """
        from .meeting_session import TranscriptSegment

        with self._connection() as conn:
            # Query segments with meeting info, ordered by meeting date desc
            rows = conn.execute("""
                SELECT
                    s.id as segment_id,
                    s.text,
                    s.speaker,
                    s.speaker_id,
                    s.start_time,
                    s.end_time,
                    s.is_bookmarked,
                    m.id as meeting_id,
                    m.title as meeting_title,
                    m.started_at as meeting_date,
                    m.duration_seconds as meeting_duration
                FROM segments s
                JOIN meetings m ON s.meeting_id = m.id
                WHERE s.speaker_id = ?
                ORDER BY m.started_at DESC, s.start_time ASC
                LIMIT ?
            """, (speaker_id, limit)).fetchall()

            # Group by meeting
            meeting_groups: dict[str, dict] = {}
            for row in rows:
                mid = row["meeting_id"]
                if mid not in meeting_groups:
                    meeting_date = datetime.fromisoformat(row["meeting_date"])
                    meeting_groups[mid] = {
                        "meeting_id": mid,
                        "meeting_title": row["meeting_title"],
                        "meeting_date": meeting_date,
                        "meeting_duration": row["meeting_duration"],
                        "segments": [],
                    }
                meeting_groups[mid]["segments"].append({
                    "text": row["text"],
                    "speaker": row["speaker"],
                    "start_time": row["start_time"],
                    "end_time": row["end_time"],
                    "is_bookmarked": bool(row["is_bookmarked"]),
                })

            # Return as list sorted by date (most recent first)
            return sorted(
                meeting_groups.values(),
                key=lambda g: g["meeting_date"],
                reverse=True,
            )

    def get_speaker_stats(self, speaker_id: str) -> dict:
        """Get aggregate statistics for a speaker.

        Args:
            speaker_id: The speaker's unique ID.

        Returns:
            Dict with:
            {
                "total_segments": int,
                "total_speaking_time": float (seconds),
                "meeting_count": int,
                "first_seen": datetime | None,
                "last_seen": datetime | None,
            }
        """
        with self._connection() as conn:
            row = conn.execute("""
                SELECT
                    COUNT(*) as total_segments,
                    COALESCE(SUM(s.end_time - s.start_time), 0) as total_speaking_time,
                    COUNT(DISTINCT s.meeting_id) as meeting_count,
                    MIN(m.started_at) as first_seen,
                    MAX(m.started_at) as last_seen
                FROM segments s
                JOIN meetings m ON s.meeting_id = m.id
                WHERE s.speaker_id = ?
            """, (speaker_id,)).fetchone()

            first_seen = None
            last_seen = None
            if row["first_seen"]:
                first_seen = datetime.fromisoformat(row["first_seen"])
            if row["last_seen"]:
                last_seen = datetime.fromisoformat(row["last_seen"])

            return {
                "total_segments": row["total_segments"] or 0,
                "total_speaking_time": row["total_speaking_time"] or 0.0,
                "meeting_count": row["meeting_count"] or 0,
                "first_seen": first_seen,
                "last_seen": last_seen,
            }


# Singleton instance
_db: Optional[MeetingDatabase] = None


def get_database(db_path: Optional[Path] = None) -> MeetingDatabase:
    """Get or create the database singleton."""
    global _db
    if _db is None:
        _db = MeetingDatabase(db_path)
    return _db


def reset_database() -> None:
    """Reset the database singleton (for testing)."""
    global _db
    _db = None
