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

VALID_ACTION_ITEM_STATUSES = frozenset({"pending", "done", "dismissed"})
VALID_ACTION_ITEM_REVIEW_STATES = frozenset({"pending", "accepted"})

# Default database location
DEFAULT_DB_PATH = Path.home() / ".local" / "share" / "holdspeak" / "holdspeak.db"
SCHEMA_VERSION = 5

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
    intel_status TEXT NOT NULL DEFAULT 'disabled',
    intel_status_detail TEXT,
    intel_requested_at TEXT,
    intel_completed_at TEXT,
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
    review_state TEXT NOT NULL DEFAULT 'pending',
    reviewed_at TEXT,
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

-- Deferred intel jobs for meetings that need later processing
CREATE TABLE IF NOT EXISTS intel_jobs (
    meeting_id TEXT PRIMARY KEY REFERENCES meetings(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'queued',
    transcript_hash TEXT NOT NULL,
    requested_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    attempts INTEGER NOT NULL DEFAULT 0,
    last_error TEXT
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
CREATE INDEX IF NOT EXISTS idx_intel_jobs_status ON intel_jobs(status, requested_at);
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
    intel_status: str = "disabled"
    intel_status_detail: Optional[str] = None


@dataclass
class IntelJob:
    """Deferred intelligence job metadata."""

    meeting_id: str
    status: str
    transcript_hash: str
    requested_at: datetime
    updated_at: datetime
    attempts: int
    last_error: Optional[str]
    meeting_title: Optional[str] = None
    started_at: Optional[datetime] = None
    intel_status_detail: Optional[str] = None


@dataclass
class ActionItemSummary:
    """Action item with meeting context."""
    id: str
    task: str
    owner: Optional[str]
    due: Optional[str]
    status: str
    review_state: str
    meeting_id: str
    meeting_title: Optional[str]
    meeting_date: datetime
    created_at: datetime
    completed_at: Optional[datetime]
    reviewed_at: Optional[datetime]


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

            # Migration v3 -> v4: Add intel status fields to meetings
            if from_version < 4:
                for column_name, column_sql in (
                    ("intel_status", "ALTER TABLE meetings ADD COLUMN intel_status TEXT NOT NULL DEFAULT 'disabled'"),
                    ("intel_status_detail", "ALTER TABLE meetings ADD COLUMN intel_status_detail TEXT"),
                    ("intel_requested_at", "ALTER TABLE meetings ADD COLUMN intel_requested_at TEXT"),
                    ("intel_completed_at", "ALTER TABLE meetings ADD COLUMN intel_completed_at TEXT"),
                ):
                    try:
                        conn.execute(f"SELECT {column_name} FROM meetings LIMIT 1")
                    except sqlite3.OperationalError:
                        log.info(f"Migrating meetings table: adding {column_name} column")
                        conn.execute(column_sql)

            # Migration v4 -> v5: Add review-state fields for action-item triage.
            if from_version < 5:
                for column_name, column_sql in (
                    ("review_state", "ALTER TABLE action_items ADD COLUMN review_state TEXT NOT NULL DEFAULT 'pending'"),
                    ("reviewed_at", "ALTER TABLE action_items ADD COLUMN reviewed_at TEXT"),
                ):
                    try:
                        conn.execute(f"SELECT {column_name} FROM action_items LIMIT 1")
                    except sqlite3.OperationalError:
                        log.info(f"Migrating action_items table: adding {column_name} column")
                        conn.execute(column_sql)

        # Now apply the full schema (creates tables/indexes that don't exist)
        conn.executescript(SCHEMA_SQL)

        conn.execute(
            "INSERT OR REPLACE INTO schema_version (version) VALUES (?)",
            (SCHEMA_VERSION,)
        )
        log.info(f"Database schema updated to version {SCHEMA_VERSION}")

    def _normalize_action_item_status(self, status: object) -> str:
        """Validate and normalize an action item status value."""
        normalized = str(status).strip().lower()
        if normalized not in VALID_ACTION_ITEM_STATUSES:
            raise ValueError(
                f"Invalid action item status: {status!r}. "
                f"Expected one of {sorted(VALID_ACTION_ITEM_STATUSES)}"
            )
        return normalized

    def _normalize_action_item_review_state(self, state: object) -> str:
        """Validate and normalize an action-item review-state value."""
        normalized = str(state).strip().lower()
        if normalized not in VALID_ACTION_ITEM_REVIEW_STATES:
            raise ValueError(
                f"Invalid action item review_state: {state!r}. "
                f"Expected one of {sorted(VALID_ACTION_ITEM_REVIEW_STATES)}"
            )
        return normalized

    def _normalize_completed_at(
        self,
        *,
        status: str,
        completed_at: object,
    ) -> Optional[str]:
        """Normalize completion timestamps to match the action item status."""
        if status == "pending":
            return None
        if completed_at in (None, ""):
            return datetime.now().isoformat()
        return str(completed_at)

    # === Meeting CRUD ===

    def save_meeting(self, state: "MeetingState") -> None:
        """Save or update a meeting and all related data."""
        from .meeting_session import TranscriptSegment, Bookmark, IntelSnapshot

        with self._connection() as conn:
            # Upsert meeting
            conn.execute("""
                INSERT INTO meetings (id, started_at, ended_at, title,
                    duration_seconds, intel_status, intel_status_detail,
                    intel_requested_at, intel_completed_at, mic_label, remote_label, web_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    ended_at = excluded.ended_at,
                    title = excluded.title,
                    duration_seconds = excluded.duration_seconds,
                    intel_status = excluded.intel_status,
                    intel_status_detail = excluded.intel_status_detail,
                    intel_requested_at = excluded.intel_requested_at,
                    intel_completed_at = excluded.intel_completed_at,
                    updated_at = datetime('now')
            """, (
                state.id,
                state.started_at.isoformat(),
                state.ended_at.isoformat() if state.ended_at else None,
                state.title,
                state.duration if state.ended_at else None,
                state.intel_status,
                state.intel_status_detail,
                state.intel_requested_at.isoformat() if state.intel_requested_at else None,
                state.intel_completed_at.isoformat() if state.intel_completed_at else None,
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
                review_state = getattr(action_item, 'review_state', 'pending')
                source_timestamp = getattr(action_item, 'source_timestamp', None)
                created_at = getattr(action_item, 'created_at', datetime.now().isoformat())
                completed_at = getattr(action_item, 'completed_at', None)
                reviewed_at = getattr(action_item, 'reviewed_at', None)
            else:
                # Dict format
                item_id = item.get('id', '')
                task = item.get('task', '')
                owner = item.get('owner')
                due = item.get('due')
                status = item.get('status', 'pending')
                review_state = item.get('review_state', 'pending')
                source_timestamp = item.get('source_timestamp')
                created_at = item.get('created_at', datetime.now().isoformat())
                completed_at = item.get('completed_at')
                reviewed_at = item.get('reviewed_at')

            if not item_id:
                continue

            status = self._normalize_action_item_status(status)
            review_state = self._normalize_action_item_review_state(review_state)
            completed_at = self._normalize_completed_at(
                status=status,
                completed_at=completed_at,
            )
            if review_state == "pending":
                reviewed_at = None
            elif reviewed_at in (None, ""):
                reviewed_at = datetime.now().isoformat()

            conn.execute("""
                INSERT INTO action_items
                (id, meeting_id, task, owner, due, status, review_state, reviewed_at,
                 source_timestamp, created_at, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    meeting_id = excluded.meeting_id,
                    task = excluded.task,
                    owner = excluded.owner,
                    due = excluded.due,
                    source_timestamp = excluded.source_timestamp,
                    status = CASE
                        WHEN excluded.status = 'pending' THEN action_items.status
                        ELSE excluded.status
                    END,
                    completed_at = CASE
                        WHEN excluded.status = 'pending' THEN action_items.completed_at
                        ELSE excluded.completed_at
                    END,
                    review_state = CASE
                        WHEN excluded.review_state = 'pending' THEN action_items.review_state
                        ELSE excluded.review_state
                    END,
                    reviewed_at = CASE
                        WHEN excluded.review_state = 'pending' THEN action_items.reviewed_at
                        ELSE excluded.reviewed_at
                    END
            """, (
                item_id,
                meeting_id,
                task,
                owner,
                due,
                status,
                review_state,
                reviewed_at,
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
            intel_status=row["intel_status"] or "disabled",
            intel_status_detail=row["intel_status_detail"],
            intel_requested_at=datetime.fromisoformat(row["intel_requested_at"]) if row["intel_requested_at"] else None,
            intel_completed_at=datetime.fromisoformat(row["intel_completed_at"]) if row["intel_completed_at"] else None,
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
                'review_state': r['review_state'] or "pending",
                'reviewed_at': r['reviewed_at'],
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

    # === Deferred Intel Queue ===

    def enqueue_intel_job(
        self,
        meeting_id: str,
        *,
        transcript_hash: str,
        reason: Optional[str] = None,
    ) -> None:
        """Queue or refresh deferred intelligence processing for a meeting."""
        now = datetime.now().isoformat()
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO intel_jobs (
                    meeting_id, status, transcript_hash, requested_at, updated_at, attempts, last_error
                )
                VALUES (?, 'queued', ?, ?, ?, 0, ?)
                ON CONFLICT(meeting_id) DO UPDATE SET
                    status = 'queued',
                    transcript_hash = excluded.transcript_hash,
                    requested_at = excluded.requested_at,
                    updated_at = excluded.updated_at,
                    last_error = excluded.last_error
                """,
                (meeting_id, transcript_hash, now, now, reason),
            )

            conn.execute(
                """
                UPDATE meetings
                SET intel_status = 'queued',
                    intel_status_detail = ?,
                    intel_requested_at = COALESCE(intel_requested_at, ?),
                    intel_completed_at = NULL,
                    updated_at = datetime('now')
                WHERE id = ?
                """,
                (
                    reason or "Queued for later processing.",
                    now,
                    meeting_id,
                ),
            )

    def claim_next_intel_job(self) -> Optional[IntelJob]:
        """Claim the next queued intelligence job for processing."""
        with self._connection() as conn:
            row = conn.execute(
                """
                SELECT * FROM intel_jobs
                WHERE status = 'queued'
                ORDER BY requested_at ASC
                LIMIT 1
                """
            ).fetchone()
            if row is None:
                return None

            updated_at = datetime.now().isoformat()
            conn.execute(
                """
                UPDATE intel_jobs
                SET status = 'running',
                    attempts = attempts + 1,
                    updated_at = ?,
                    last_error = NULL
                WHERE meeting_id = ?
                """,
                (updated_at, row["meeting_id"]),
            )

            conn.execute(
                """
                UPDATE meetings
                SET intel_status = 'running',
                    intel_status_detail = 'Processing queued meeting intelligence.',
                    updated_at = datetime('now')
                WHERE id = ?
                """,
                (row["meeting_id"],),
            )

            return IntelJob(
                meeting_id=row["meeting_id"],
                status="running",
                transcript_hash=row["transcript_hash"],
                requested_at=datetime.fromisoformat(row["requested_at"]),
                updated_at=datetime.fromisoformat(updated_at),
                attempts=int(row["attempts"]) + 1,
                last_error=None,
            )

    def complete_intel_job(self, meeting_id: str) -> None:
        """Remove a completed deferred intelligence job."""
        with self._connection() as conn:
            conn.execute("DELETE FROM intel_jobs WHERE meeting_id = ?", (meeting_id,))

    def list_intel_jobs(
        self,
        *,
        status: Optional[str] = None,
        limit: int = 20,
    ) -> list[IntelJob]:
        """List deferred intelligence jobs with meeting context."""
        with self._connection() as conn:
            query = """
                SELECT
                    j.*,
                    m.title AS meeting_title,
                    m.started_at AS meeting_started_at,
                    m.intel_status_detail AS intel_status_detail
                FROM intel_jobs j
                JOIN meetings m ON m.id = j.meeting_id
                WHERE 1=1
            """
            params: list[Any] = []

            if status and status != "all":
                query += " AND j.status = ?"
                params.append(status)

            query += """
                ORDER BY
                    CASE j.status
                        WHEN 'running' THEN 0
                        WHEN 'queued' THEN 1
                        WHEN 'failed' THEN 2
                        ELSE 3
                    END,
                    j.requested_at ASC
                LIMIT ?
            """
            params.append(limit)

            return [
                IntelJob(
                    meeting_id=row["meeting_id"],
                    status=row["status"],
                    transcript_hash=row["transcript_hash"],
                    requested_at=datetime.fromisoformat(row["requested_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                    attempts=int(row["attempts"]),
                    last_error=row["last_error"],
                    meeting_title=row["meeting_title"],
                    started_at=(
                        datetime.fromisoformat(row["meeting_started_at"])
                        if row["meeting_started_at"]
                        else None
                    ),
                    intel_status_detail=row["intel_status_detail"],
                )
                for row in conn.execute(query, params)
            ]

    def fail_intel_job(self, meeting_id: str, error: str) -> None:
        """Mark a deferred intelligence job as failed."""
        now = datetime.now().isoformat()
        with self._connection() as conn:
            conn.execute(
                """
                UPDATE intel_jobs
                SET status = 'failed',
                    updated_at = ?,
                    last_error = ?
                WHERE meeting_id = ?
                """,
                (now, error, meeting_id),
            )
            conn.execute(
                """
                UPDATE meetings
                SET intel_status = 'error',
                    intel_status_detail = ?,
                    intel_completed_at = ?,
                    updated_at = datetime('now')
                WHERE id = ?
                """,
                (error, now, meeting_id),
            )

    def requeue_intel_job(self, meeting_id: str, *, reason: Optional[str] = None) -> bool:
        """Requeue deferred intelligence processing for a meeting."""
        meeting = self.get_meeting(meeting_id)
        if meeting is None or not meeting.segments:
            return False

        self.enqueue_intel_job(
            meeting_id,
            transcript_hash=meeting.transcript_hash(),
            reason=reason or "Manual retry requested.",
        )
        return True

    def update_meeting_intel_status(
        self,
        meeting_id: str,
        *,
        status: str,
        detail: Optional[str] = None,
        requested_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
    ) -> None:
        """Update persisted intel status for a meeting."""
        with self._connection() as conn:
            conn.execute(
                """
                UPDATE meetings
                SET intel_status = ?,
                    intel_status_detail = ?,
                    intel_requested_at = COALESCE(?, intel_requested_at),
                    intel_completed_at = ?,
                    updated_at = datetime('now')
                WHERE id = ?
                """,
                (
                    status,
                    detail,
                    requested_at.isoformat() if requested_at else None,
                    completed_at.isoformat() if completed_at else None,
                    meeting_id,
                ),
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
                    intel_status=r["intel_status"] or "disabled",
                    intel_status_detail=r["intel_status_detail"],
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
                self._row_to_action_item_summary(r)
                for r in conn.execute(query, params)
            ]

    def _row_to_action_item_summary(self, row: sqlite3.Row) -> ActionItemSummary:
        """Convert a DB row to ActionItemSummary."""
        return ActionItemSummary(
            id=row['id'],
            task=row['task'],
            owner=row['owner'],
            due=row['due'],
            status=row['status'],
            review_state=row['review_state'] or "pending",
            meeting_id=row['meeting_id'],
            meeting_title=row['meeting_title'],
            meeting_date=datetime.fromisoformat(row['meeting_date']),
            created_at=datetime.fromisoformat(row['created_at']),
            completed_at=datetime.fromisoformat(row['completed_at']) if row['completed_at'] else None,
            reviewed_at=datetime.fromisoformat(row['reviewed_at']) if row['reviewed_at'] else None,
        )

    def get_action_item(self, item_id: str) -> Optional[ActionItemSummary]:
        """Get a single action item by ID, including meeting metadata."""
        with self._connection() as conn:
            row = conn.execute(
                """
                SELECT a.*, m.title as meeting_title, m.started_at as meeting_date
                FROM action_items a
                JOIN meetings m ON a.meeting_id = m.id
                WHERE a.id = ?
                """,
                (item_id,),
            ).fetchone()
            if row is None:
                return None
            return self._row_to_action_item_summary(row)

    def update_action_item_status(
        self, item_id: str, status: str
    ) -> bool:
        """Update action item status. Returns True if found."""
        status = self._normalize_action_item_status(status)
        with self._connection() as conn:
            completed_at = self._normalize_completed_at(
                status=status,
                completed_at=None,
            )
            result = conn.execute("""
                UPDATE action_items
                SET status = ?, completed_at = ?
                WHERE id = ?
            """, (status, completed_at, item_id))
            return result.rowcount > 0

    def update_action_item_review_state(
        self, item_id: str, review_state: str
    ) -> bool:
        """Update action item review state. Returns True if found."""
        review_state = self._normalize_action_item_review_state(review_state)
        with self._connection() as conn:
            reviewed_at = datetime.now().isoformat() if review_state == "accepted" else None
            result = conn.execute(
                """
                UPDATE action_items
                SET review_state = ?, reviewed_at = ?
                WHERE id = ?
                """,
                (review_state, reviewed_at, item_id),
            )
            return result.rowcount > 0

    def edit_action_item(
        self,
        item_id: str,
        *,
        task: str,
        owner: Optional[str],
        due: Optional[str],
    ) -> bool:
        """Edit action-item content and mark the item as accepted."""
        clean_task = str(task).strip()
        if not clean_task:
            raise ValueError("Action item task cannot be empty")

        clean_owner = owner.strip() if isinstance(owner, str) else owner
        clean_due = due.strip() if isinstance(due, str) else due
        with self._connection() as conn:
            result = conn.execute(
                """
                UPDATE action_items
                SET task = ?,
                    owner = ?,
                    due = ?,
                    review_state = 'accepted',
                    reviewed_at = ?
                WHERE id = ?
                """,
                (
                    clean_task,
                    clean_owner or None,
                    clean_due or None,
                    datetime.now().isoformat(),
                    item_id,
                ),
            )
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
