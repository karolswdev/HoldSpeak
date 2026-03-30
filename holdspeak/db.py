"""SQLite database persistence for HoldSpeak meetings."""

from __future__ import annotations

import json
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
SCHEMA_VERSION = 9

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

-- Deferred-intel attempt history (retry and terminal outcomes)
CREATE TABLE IF NOT EXISTS intel_job_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meeting_id TEXT NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    attempt INTEGER NOT NULL,
    outcome TEXT NOT NULL, -- scheduled_retry | terminal_failure | success
    error TEXT,
    retry_at TEXT,
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
CREATE INDEX IF NOT EXISTS idx_intel_jobs_status ON intel_jobs(status, requested_at);
CREATE INDEX IF NOT EXISTS idx_intel_job_attempts_meeting ON intel_job_attempts(meeting_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_segments_speaker_id ON segments(speaker_id);
CREATE INDEX IF NOT EXISTS idx_speakers_name ON speakers(name);

-- MIR timeline windows (per-meeting rolling windows)
CREATE TABLE IF NOT EXISTS intent_windows (
    meeting_id TEXT NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    window_id TEXT NOT NULL,
    start_seconds REAL NOT NULL DEFAULT 0,
    end_seconds REAL NOT NULL DEFAULT 0,
    transcript_hash TEXT NOT NULL DEFAULT '',
    transcript_excerpt TEXT NOT NULL DEFAULT '',
    profile TEXT NOT NULL DEFAULT 'balanced',
    threshold REAL NOT NULL DEFAULT 0.6,
    active_intents_json TEXT NOT NULL DEFAULT '[]',
    override_intents_json TEXT NOT NULL DEFAULT '[]',
    tags_json TEXT NOT NULL DEFAULT '[]',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (meeting_id, window_id)
);

-- MIR per-window confidence scores
CREATE TABLE IF NOT EXISTS intent_window_scores (
    meeting_id TEXT NOT NULL,
    window_id TEXT NOT NULL,
    intent_label TEXT NOT NULL,
    score REAL NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (meeting_id, window_id, intent_label),
    FOREIGN KEY (meeting_id, window_id) REFERENCES intent_windows(meeting_id, window_id) ON DELETE CASCADE
);

-- MIR plugin execution history
CREATE TABLE IF NOT EXISTS plugin_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meeting_id TEXT NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    window_id TEXT NOT NULL,
    plugin_id TEXT NOT NULL,
    plugin_version TEXT NOT NULL DEFAULT 'unknown',
    status TEXT NOT NULL,
    idempotency_key TEXT,
    duration_ms REAL NOT NULL DEFAULT 0,
    output_json TEXT,
    error TEXT,
    deduped INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Deferred MIR plugin execution queue (heavy plugins)
CREATE TABLE IF NOT EXISTS plugin_run_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meeting_id TEXT NOT NULL,
    window_id TEXT NOT NULL,
    plugin_id TEXT NOT NULL,
    plugin_version TEXT NOT NULL DEFAULT 'unknown',
    transcript_hash TEXT NOT NULL DEFAULT '',
    idempotency_key TEXT NOT NULL UNIQUE,
    context_json TEXT NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'queued',
    requested_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    attempts INTEGER NOT NULL DEFAULT 0,
    last_error TEXT
);

CREATE INDEX IF NOT EXISTS idx_intent_windows_meeting ON intent_windows(meeting_id, start_seconds, created_at);
CREATE INDEX IF NOT EXISTS idx_intent_window_scores_meeting ON intent_window_scores(meeting_id, window_id);
CREATE INDEX IF NOT EXISTS idx_plugin_runs_meeting ON plugin_runs(meeting_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_plugin_runs_window ON plugin_runs(meeting_id, window_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_plugin_runs_status ON plugin_runs(status, created_at DESC);
CREATE UNIQUE INDEX IF NOT EXISTS idx_plugin_runs_idempotency ON plugin_runs(idempotency_key);
CREATE INDEX IF NOT EXISTS idx_plugin_run_jobs_status ON plugin_run_jobs(status, requested_at);
CREATE INDEX IF NOT EXISTS idx_plugin_run_jobs_meeting ON plugin_run_jobs(meeting_id, requested_at);

-- Synthesized artifacts
CREATE TABLE IF NOT EXISTS artifacts (
    id TEXT PRIMARY KEY,
    meeting_id TEXT NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    artifact_type TEXT NOT NULL,
    title TEXT NOT NULL,
    body_markdown TEXT NOT NULL DEFAULT '',
    structured_json TEXT NOT NULL DEFAULT '{}',
    confidence REAL NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'draft',
    plugin_id TEXT NOT NULL DEFAULT 'unknown',
    plugin_version TEXT NOT NULL DEFAULT 'unknown',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Artifact lineage references (window/plugin run)
CREATE TABLE IF NOT EXISTS artifact_sources (
    artifact_id TEXT NOT NULL REFERENCES artifacts(id) ON DELETE CASCADE,
    source_type TEXT NOT NULL,
    source_ref TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (artifact_id, source_type, source_ref)
);

CREATE INDEX IF NOT EXISTS idx_artifacts_meeting ON artifacts(meeting_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_artifacts_type ON artifacts(artifact_type, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_artifact_sources_ref ON artifact_sources(source_type, source_ref);
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
class IntelQueueSummary:
    """Aggregated deferred-intel queue telemetry."""

    total_jobs: int
    queued_jobs: int
    running_jobs: int
    failed_jobs: int
    queued_due_jobs: int
    scheduled_retry_jobs: int
    next_retry_at: Optional[datetime] = None


@dataclass
class IntelJobAttempt:
    """Deferred-intel attempt event for one meeting."""

    meeting_id: str
    attempt: int
    outcome: str
    error: Optional[str]
    retry_at: Optional[datetime]
    created_at: datetime


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


@dataclass
class IntentWindowSummary:
    """Persisted MIR intent window with confidence scores."""

    meeting_id: str
    window_id: str
    start_seconds: float
    end_seconds: float
    transcript_hash: str
    transcript_excerpt: str
    profile: str
    threshold: float
    active_intents: list[str]
    intent_scores: dict[str, float]
    override_intents: list[str]
    tags: list[str]
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime


@dataclass
class PluginRunSummary:
    """Persisted MIR plugin-run record."""

    id: int
    meeting_id: str
    window_id: str
    plugin_id: str
    plugin_version: str
    status: str
    idempotency_key: Optional[str]
    duration_ms: float
    output: Optional[dict[str, Any]]
    error: Optional[str]
    deduped: bool
    created_at: datetime
    updated_at: datetime


@dataclass
class PluginRunJob:
    """Deferred MIR plugin-run queue item."""

    id: int
    meeting_id: str
    window_id: str
    plugin_id: str
    plugin_version: str
    transcript_hash: str
    idempotency_key: str
    context: dict[str, Any]
    status: str
    requested_at: datetime
    updated_at: datetime
    attempts: int
    last_error: Optional[str]


@dataclass
class PluginRunJobQueueSummary:
    """Aggregated deferred plugin-run queue telemetry."""

    total_jobs: int
    queued_jobs: int
    running_jobs: int
    failed_jobs: int
    queued_due_jobs: int
    scheduled_retry_jobs: int
    next_retry_at: Optional[datetime] = None


@dataclass
class ArtifactSummary:
    """Persisted synthesized artifact with lineage sources."""

    id: str
    meeting_id: str
    artifact_type: str
    title: str
    body_markdown: str
    structured_json: dict[str, Any]
    confidence: float
    status: str
    plugin_id: str
    plugin_version: str
    sources: list[dict[str, str]]
    created_at: datetime
    updated_at: datetime


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

            # Migration v5 -> v6: Add deferred-intel attempt history table.
            if from_version < 6:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS intel_job_attempts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        meeting_id TEXT NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
                        attempt INTEGER NOT NULL,
                        outcome TEXT NOT NULL,
                        error TEXT,
                        retry_at TEXT,
                        created_at TEXT NOT NULL DEFAULT (datetime('now'))
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_intel_job_attempts_meeting
                    ON intel_job_attempts(meeting_id, created_at DESC)
                    """
                )

            # Migration v6 -> v7: Add MIR persistence tables.
            if from_version < 7:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS intent_windows (
                        meeting_id TEXT NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
                        window_id TEXT NOT NULL,
                        start_seconds REAL NOT NULL DEFAULT 0,
                        end_seconds REAL NOT NULL DEFAULT 0,
                        transcript_hash TEXT NOT NULL DEFAULT '',
                        transcript_excerpt TEXT NOT NULL DEFAULT '',
                        profile TEXT NOT NULL DEFAULT 'balanced',
                        threshold REAL NOT NULL DEFAULT 0.6,
                        active_intents_json TEXT NOT NULL DEFAULT '[]',
                        override_intents_json TEXT NOT NULL DEFAULT '[]',
                        tags_json TEXT NOT NULL DEFAULT '[]',
                        metadata_json TEXT NOT NULL DEFAULT '{}',
                        created_at TEXT NOT NULL DEFAULT (datetime('now')),
                        updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                        PRIMARY KEY (meeting_id, window_id)
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS intent_window_scores (
                        meeting_id TEXT NOT NULL,
                        window_id TEXT NOT NULL,
                        intent_label TEXT NOT NULL,
                        score REAL NOT NULL,
                        created_at TEXT NOT NULL DEFAULT (datetime('now')),
                        PRIMARY KEY (meeting_id, window_id, intent_label),
                        FOREIGN KEY (meeting_id, window_id) REFERENCES intent_windows(meeting_id, window_id) ON DELETE CASCADE
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS plugin_runs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        meeting_id TEXT NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
                        window_id TEXT NOT NULL,
                        plugin_id TEXT NOT NULL,
                        plugin_version TEXT NOT NULL DEFAULT 'unknown',
                        status TEXT NOT NULL,
                        idempotency_key TEXT,
                        duration_ms REAL NOT NULL DEFAULT 0,
                        output_json TEXT,
                        error TEXT,
                        deduped INTEGER NOT NULL DEFAULT 0,
                        created_at TEXT NOT NULL DEFAULT (datetime('now')),
                        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_intent_windows_meeting
                    ON intent_windows(meeting_id, start_seconds, created_at)
                    """
                )
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_intent_window_scores_meeting
                    ON intent_window_scores(meeting_id, window_id)
                    """
                )
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_plugin_runs_meeting
                    ON plugin_runs(meeting_id, created_at DESC)
                    """
                )
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_plugin_runs_window
                    ON plugin_runs(meeting_id, window_id, created_at DESC)
                    """
                )
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_plugin_runs_status
                    ON plugin_runs(status, created_at DESC)
                    """
                )
                conn.execute(
                    """
                    CREATE UNIQUE INDEX IF NOT EXISTS idx_plugin_runs_idempotency
                    ON plugin_runs(idempotency_key)
                    """
                )

            # Migration v7 -> v8: Add synthesized artifacts and lineage tables.
            if from_version < 8:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS artifacts (
                        id TEXT PRIMARY KEY,
                        meeting_id TEXT NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
                        artifact_type TEXT NOT NULL,
                        title TEXT NOT NULL,
                        body_markdown TEXT NOT NULL DEFAULT '',
                        structured_json TEXT NOT NULL DEFAULT '{}',
                        confidence REAL NOT NULL DEFAULT 0,
                        status TEXT NOT NULL DEFAULT 'draft',
                        plugin_id TEXT NOT NULL DEFAULT 'unknown',
                        plugin_version TEXT NOT NULL DEFAULT 'unknown',
                        created_at TEXT NOT NULL DEFAULT (datetime('now')),
                        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS artifact_sources (
                        artifact_id TEXT NOT NULL REFERENCES artifacts(id) ON DELETE CASCADE,
                        source_type TEXT NOT NULL,
                        source_ref TEXT NOT NULL,
                        created_at TEXT NOT NULL DEFAULT (datetime('now')),
                        PRIMARY KEY (artifact_id, source_type, source_ref)
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_artifacts_meeting
                    ON artifacts(meeting_id, created_at DESC)
                    """
                )
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_artifacts_type
                    ON artifacts(artifact_type, created_at DESC)
                    """
                )
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_artifact_sources_ref
                    ON artifact_sources(source_type, source_ref)
                    """
                )

            # Migration v8 -> v9: Add deferred MIR plugin-run queue tables.
            if from_version < 9:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS plugin_run_jobs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        meeting_id TEXT NOT NULL,
                        window_id TEXT NOT NULL,
                        plugin_id TEXT NOT NULL,
                        plugin_version TEXT NOT NULL DEFAULT 'unknown',
                        transcript_hash TEXT NOT NULL DEFAULT '',
                        idempotency_key TEXT NOT NULL UNIQUE,
                        context_json TEXT NOT NULL DEFAULT '{}',
                        status TEXT NOT NULL DEFAULT 'queued',
                        requested_at TEXT NOT NULL DEFAULT (datetime('now')),
                        updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                        attempts INTEGER NOT NULL DEFAULT 0,
                        last_error TEXT
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_plugin_run_jobs_status
                    ON plugin_run_jobs(status, requested_at)
                    """
                )
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_plugin_run_jobs_meeting
                    ON plugin_run_jobs(meeting_id, requested_at)
                    """
                )

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

    def claim_next_intel_job(self, *, include_scheduled: bool = False) -> Optional[IntelJob]:
        """Claim the next queued intelligence job for processing."""
        now_iso = datetime.now().isoformat()
        with self._connection() as conn:
            if include_scheduled:
                row = conn.execute(
                    """
                    SELECT * FROM intel_jobs
                    WHERE status = 'queued'
                    ORDER BY requested_at ASC
                    LIMIT 1
                    """
                ).fetchone()
            else:
                row = conn.execute(
                    """
                    SELECT * FROM intel_jobs
                    WHERE status = 'queued'
                      AND requested_at <= ?
                    ORDER BY requested_at ASC
                    LIMIT 1
                    """,
                    (now_iso,),
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

    def retry_intel_job(
        self,
        meeting_id: str,
        error: str,
        *,
        retry_at: datetime,
        attempt: int,
        max_attempts: int,
    ) -> None:
        """Requeue a deferred intelligence job for a future retry."""
        now = datetime.now().isoformat()
        retry_at_iso = retry_at.isoformat()
        retry_label = retry_at.replace(microsecond=0).isoformat()
        detail = (
            f"Deferred intel attempt {attempt}/{max_attempts} failed: {error} "
            f"Retrying at {retry_label}."
        )
        with self._connection() as conn:
            conn.execute(
                """
                UPDATE intel_jobs
                SET status = 'queued',
                    requested_at = ?,
                    updated_at = ?,
                    last_error = ?
                WHERE meeting_id = ?
                """,
                (retry_at_iso, now, error, meeting_id),
            )
            conn.execute(
                """
                UPDATE meetings
                SET intel_status = 'queued',
                    intel_status_detail = ?,
                    intel_completed_at = NULL,
                    updated_at = datetime('now')
                WHERE id = ?
                """,
                (detail, meeting_id),
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

    def get_intel_queue_summary(self) -> IntelQueueSummary:
        """Return aggregate telemetry for deferred-intel queue state."""
        now_iso = datetime.now().isoformat()
        with self._connection() as conn:
            row = conn.execute(
                """
                SELECT
                    COUNT(*) AS total_jobs,
                    SUM(CASE WHEN status = 'queued' THEN 1 ELSE 0 END) AS queued_jobs,
                    SUM(CASE WHEN status = 'running' THEN 1 ELSE 0 END) AS running_jobs,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed_jobs,
                    SUM(CASE WHEN status = 'queued' AND requested_at <= ? THEN 1 ELSE 0 END) AS queued_due_jobs,
                    SUM(CASE WHEN status = 'queued' AND requested_at > ? THEN 1 ELSE 0 END) AS scheduled_retry_jobs
                FROM intel_jobs
                """,
                (now_iso, now_iso),
            ).fetchone()

            next_row = conn.execute(
                """
                SELECT MIN(requested_at) AS next_retry_at
                FROM intel_jobs
                WHERE status = 'queued'
                  AND requested_at > ?
                  AND last_error IS NOT NULL
                """,
                (now_iso,),
            ).fetchone()

        next_retry_at = None
        if next_row is not None and next_row["next_retry_at"]:
            next_retry_at = datetime.fromisoformat(next_row["next_retry_at"])

        return IntelQueueSummary(
            total_jobs=int(row["total_jobs"] or 0),
            queued_jobs=int(row["queued_jobs"] or 0),
            running_jobs=int(row["running_jobs"] or 0),
            failed_jobs=int(row["failed_jobs"] or 0),
            queued_due_jobs=int(row["queued_due_jobs"] or 0),
            scheduled_retry_jobs=int(row["scheduled_retry_jobs"] or 0),
            next_retry_at=next_retry_at,
        )

    def record_intel_job_attempt(
        self,
        meeting_id: str,
        *,
        attempt: int,
        outcome: str,
        error: Optional[str] = None,
        retry_at: Optional[datetime] = None,
    ) -> None:
        """Append an intel-attempt history event."""
        now = datetime.now().isoformat()
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO intel_job_attempts (
                    meeting_id, attempt, outcome, error, retry_at, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    meeting_id,
                    int(attempt),
                    str(outcome),
                    error,
                    retry_at.isoformat() if retry_at else None,
                    now,
                ),
            )

    def list_intel_job_attempts(self, meeting_id: str, *, limit: int = 5) -> list[IntelJobAttempt]:
        """Return most recent deferred-intel attempt events for one meeting."""
        bounded_limit = max(1, min(int(limit), 50))
        with self._connection() as conn:
            rows = conn.execute(
                """
                SELECT meeting_id, attempt, outcome, error, retry_at, created_at
                FROM intel_job_attempts
                WHERE meeting_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (meeting_id, bounded_limit),
            ).fetchall()

        return [
            IntelJobAttempt(
                meeting_id=row["meeting_id"],
                attempt=int(row["attempt"]),
                outcome=row["outcome"],
                error=row["error"],
                retry_at=(datetime.fromisoformat(row["retry_at"]) if row["retry_at"] else None),
                created_at=datetime.fromisoformat(row["created_at"]),
            )
            for row in rows
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

    # === MIR Persistence ===

    def _json_dumps(self, value: object, *, fallback: str) -> str:
        try:
            return json.dumps(value, separators=(",", ":"), sort_keys=True)
        except Exception:
            return fallback

    def _json_loads_list(self, raw: object) -> list[Any]:
        if not isinstance(raw, str) or not raw:
            return []
        try:
            parsed = json.loads(raw)
        except Exception:
            return []
        if not isinstance(parsed, list):
            return []
        return parsed

    def _json_loads_dict(self, raw: object) -> dict[str, Any]:
        if not isinstance(raw, str) or not raw:
            return {}
        try:
            parsed = json.loads(raw)
        except Exception:
            return {}
        if not isinstance(parsed, dict):
            return {}
        return {str(key): value for key, value in parsed.items()}

    def record_intent_window(
        self,
        *,
        meeting_id: str,
        window_id: str,
        start_seconds: float,
        end_seconds: float,
        transcript_hash: str,
        transcript_excerpt: str = "",
        profile: str = "balanced",
        threshold: float = 0.6,
        active_intents: Optional[list[str]] = None,
        intent_scores: Optional[dict[str, float]] = None,
        override_intents: Optional[list[str]] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """Insert or update one persisted MIR intent window."""
        clean_meeting_id = str(meeting_id).strip()
        clean_window_id = str(window_id).strip()
        if not clean_meeting_id:
            raise ValueError("meeting_id is required")
        if not clean_window_id:
            raise ValueError("window_id is required")

        start_value = max(0.0, float(start_seconds))
        end_value = max(start_value, float(end_seconds))
        clean_profile = str(profile).strip().lower() or "balanced"
        clean_threshold = float(threshold)
        clean_hash = str(transcript_hash or "").strip()
        clean_excerpt = str(transcript_excerpt or "").strip()
        clean_active = [
            str(intent).strip().lower()
            for intent in (active_intents or [])
            if str(intent).strip()
        ]
        clean_override = [
            str(intent).strip().lower()
            for intent in (override_intents or [])
            if str(intent).strip()
        ]
        clean_tags = [
            str(tag).strip().lower()
            for tag in (tags or [])
            if str(tag).strip()
        ]
        clean_metadata = dict(metadata) if isinstance(metadata, dict) else {}
        clean_scores: dict[str, float] = {}
        if isinstance(intent_scores, dict):
            for raw_label, raw_score in intent_scores.items():
                label = str(raw_label).strip().lower()
                if not label:
                    continue
                try:
                    score_value = float(raw_score)
                except Exception:
                    continue
                clean_scores[label] = score_value

        now_iso = datetime.now().isoformat()
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO intent_windows (
                    meeting_id, window_id, start_seconds, end_seconds, transcript_hash,
                    transcript_excerpt, profile, threshold, active_intents_json,
                    override_intents_json, tags_json, metadata_json, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(meeting_id, window_id) DO UPDATE SET
                    start_seconds = excluded.start_seconds,
                    end_seconds = excluded.end_seconds,
                    transcript_hash = excluded.transcript_hash,
                    transcript_excerpt = excluded.transcript_excerpt,
                    profile = excluded.profile,
                    threshold = excluded.threshold,
                    active_intents_json = excluded.active_intents_json,
                    override_intents_json = excluded.override_intents_json,
                    tags_json = excluded.tags_json,
                    metadata_json = excluded.metadata_json,
                    updated_at = excluded.updated_at
                """,
                (
                    clean_meeting_id,
                    clean_window_id,
                    start_value,
                    end_value,
                    clean_hash,
                    clean_excerpt,
                    clean_profile,
                    clean_threshold,
                    self._json_dumps(clean_active, fallback="[]"),
                    self._json_dumps(clean_override, fallback="[]"),
                    self._json_dumps(clean_tags, fallback="[]"),
                    self._json_dumps(clean_metadata, fallback="{}"),
                    now_iso,
                    now_iso,
                ),
            )
            conn.execute(
                """
                DELETE FROM intent_window_scores
                WHERE meeting_id = ? AND window_id = ?
                """,
                (clean_meeting_id, clean_window_id),
            )
            for intent_label, score in sorted(clean_scores.items()):
                conn.execute(
                    """
                    INSERT INTO intent_window_scores (
                        meeting_id, window_id, intent_label, score, created_at
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        clean_meeting_id,
                        clean_window_id,
                        intent_label,
                        float(score),
                        now_iso,
                    ),
                )

    def list_intent_windows(
        self,
        meeting_id: str,
        *,
        limit: int = 200,
    ) -> list[IntentWindowSummary]:
        """List persisted MIR intent windows for one meeting."""
        clean_meeting_id = str(meeting_id).strip()
        bounded_limit = max(1, min(int(limit), 2000))
        with self._connection() as conn:
            window_rows = conn.execute(
                """
                SELECT *
                FROM intent_windows
                WHERE meeting_id = ?
                ORDER BY start_seconds ASC, created_at ASC
                LIMIT ?
                """,
                (clean_meeting_id, bounded_limit),
            ).fetchall()
            if not window_rows:
                return []

            score_rows = conn.execute(
                """
                SELECT meeting_id, window_id, intent_label, score
                FROM intent_window_scores
                WHERE meeting_id = ?
                ORDER BY window_id ASC, intent_label ASC
                """,
                (clean_meeting_id,),
            ).fetchall()

        scores_by_window: dict[str, dict[str, float]] = {}
        for row in score_rows:
            wid = str(row["window_id"])
            scores_by_window.setdefault(wid, {})[str(row["intent_label"])] = float(row["score"])

        windows: list[IntentWindowSummary] = []
        for row in window_rows:
            window_id = str(row["window_id"])
            windows.append(
                IntentWindowSummary(
                    meeting_id=str(row["meeting_id"]),
                    window_id=window_id,
                    start_seconds=float(row["start_seconds"]),
                    end_seconds=float(row["end_seconds"]),
                    transcript_hash=str(row["transcript_hash"] or ""),
                    transcript_excerpt=str(row["transcript_excerpt"] or ""),
                    profile=str(row["profile"] or "balanced"),
                    threshold=float(row["threshold"] if row["threshold"] is not None else 0.6),
                    active_intents=[
                        str(intent).strip().lower()
                        for intent in self._json_loads_list(row["active_intents_json"])
                        if str(intent).strip()
                    ],
                    intent_scores=scores_by_window.get(window_id, {}),
                    override_intents=[
                        str(intent).strip().lower()
                        for intent in self._json_loads_list(row["override_intents_json"])
                        if str(intent).strip()
                    ],
                    tags=[
                        str(tag).strip().lower()
                        for tag in self._json_loads_list(row["tags_json"])
                        if str(tag).strip()
                    ],
                    metadata=self._json_loads_dict(row["metadata_json"]),
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                )
            )
        return windows

    def record_plugin_run(
        self,
        *,
        meeting_id: str,
        window_id: str,
        plugin_id: str,
        plugin_version: str,
        status: str,
        idempotency_key: Optional[str] = None,
        duration_ms: float = 0.0,
        output: Optional[dict[str, Any]] = None,
        error: Optional[str] = None,
        deduped: bool = False,
    ) -> None:
        """Persist one MIR plugin-run record."""
        clean_meeting_id = str(meeting_id).strip()
        clean_window_id = str(window_id).strip()
        clean_plugin_id = str(plugin_id).strip()
        clean_status = str(status).strip().lower()
        clean_plugin_version = str(plugin_version).strip() or "unknown"
        clean_idempotency_key = (
            str(idempotency_key).strip() if isinstance(idempotency_key, str) and idempotency_key.strip() else None
        )
        if not clean_meeting_id:
            raise ValueError("meeting_id is required")
        if not clean_window_id:
            raise ValueError("window_id is required")
        if not clean_plugin_id:
            raise ValueError("plugin_id is required")
        if not clean_status:
            raise ValueError("status is required")

        now_iso = datetime.now().isoformat()
        output_json = self._json_dumps(output, fallback="null") if output is not None else None
        with self._connection() as conn:
            if clean_idempotency_key:
                conn.execute(
                    """
                    INSERT INTO plugin_runs (
                        meeting_id, window_id, plugin_id, plugin_version, status,
                        idempotency_key, duration_ms, output_json, error, deduped, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(idempotency_key) DO UPDATE SET
                        meeting_id = excluded.meeting_id,
                        window_id = excluded.window_id,
                        plugin_id = excluded.plugin_id,
                        plugin_version = excluded.plugin_version,
                        status = excluded.status,
                        duration_ms = excluded.duration_ms,
                        output_json = excluded.output_json,
                        error = excluded.error,
                        deduped = excluded.deduped,
                        updated_at = excluded.updated_at
                    """,
                    (
                        clean_meeting_id,
                        clean_window_id,
                        clean_plugin_id,
                        clean_plugin_version,
                        clean_status,
                        clean_idempotency_key,
                        float(duration_ms),
                        output_json,
                        error,
                        int(bool(deduped)),
                        now_iso,
                        now_iso,
                    ),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO plugin_runs (
                        meeting_id, window_id, plugin_id, plugin_version, status,
                        idempotency_key, duration_ms, output_json, error, deduped, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        clean_meeting_id,
                        clean_window_id,
                        clean_plugin_id,
                        clean_plugin_version,
                        clean_status,
                        None,
                        float(duration_ms),
                        output_json,
                        error,
                        int(bool(deduped)),
                        now_iso,
                        now_iso,
                    ),
                )

    def list_plugin_runs(
        self,
        meeting_id: str,
        *,
        window_id: Optional[str] = None,
        limit: int = 500,
    ) -> list[PluginRunSummary]:
        """List persisted MIR plugin-run history for one meeting."""
        clean_meeting_id = str(meeting_id).strip()
        clean_window_id = str(window_id).strip() if isinstance(window_id, str) else None
        bounded_limit = max(1, min(int(limit), 5000))

        with self._connection() as conn:
            query = """
                SELECT *
                FROM plugin_runs
                WHERE meeting_id = ?
            """
            params: list[Any] = [clean_meeting_id]
            if clean_window_id:
                query += " AND window_id = ?"
                params.append(clean_window_id)
            query += " ORDER BY created_at DESC, id DESC LIMIT ?"
            params.append(bounded_limit)
            rows = conn.execute(query, params).fetchall()

        output: list[PluginRunSummary] = []
        for row in rows:
            output_json = row["output_json"]
            parsed_output: Optional[dict[str, Any]] = None
            if isinstance(output_json, str) and output_json:
                try:
                    parsed_value = json.loads(output_json)
                except Exception:
                    parsed_value = None
                if isinstance(parsed_value, dict):
                    parsed_output = parsed_value

            output.append(
                PluginRunSummary(
                    id=int(row["id"]),
                    meeting_id=str(row["meeting_id"]),
                    window_id=str(row["window_id"]),
                    plugin_id=str(row["plugin_id"]),
                    plugin_version=str(row["plugin_version"] or "unknown"),
                    status=str(row["status"] or "unknown"),
                    idempotency_key=str(row["idempotency_key"]) if row["idempotency_key"] else None,
                    duration_ms=float(row["duration_ms"] if row["duration_ms"] is not None else 0.0),
                    output=parsed_output,
                    error=row["error"],
                    deduped=bool(row["deduped"]),
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                )
            )
        return output

    def _row_to_plugin_run_job(self, row: sqlite3.Row) -> PluginRunJob:
        context = self._json_loads_dict(row["context_json"])
        return PluginRunJob(
            id=int(row["id"]),
            meeting_id=str(row["meeting_id"]),
            window_id=str(row["window_id"]),
            plugin_id=str(row["plugin_id"]),
            plugin_version=str(row["plugin_version"] or "unknown"),
            transcript_hash=str(row["transcript_hash"] or ""),
            idempotency_key=str(row["idempotency_key"]),
            context=context,
            status=str(row["status"] or "queued"),
            requested_at=datetime.fromisoformat(str(row["requested_at"])),
            updated_at=datetime.fromisoformat(str(row["updated_at"])),
            attempts=int(row["attempts"] or 0),
            last_error=row["last_error"],
        )

    def enqueue_plugin_run_job(
        self,
        *,
        meeting_id: str,
        window_id: str,
        plugin_id: str,
        plugin_version: str,
        transcript_hash: str,
        idempotency_key: str,
        context: Optional[dict[str, Any]] = None,
    ) -> bool:
        """Queue one deferred MIR plugin run.

        Returns True when a new queue row was inserted, False when an existing
        idempotency key was refreshed/reused.
        """
        clean_meeting_id = str(meeting_id).strip()
        clean_window_id = str(window_id).strip()
        clean_plugin_id = str(plugin_id).strip()
        clean_plugin_version = str(plugin_version).strip() or "unknown"
        clean_hash = str(transcript_hash or "").strip()
        clean_key = str(idempotency_key).strip()
        if not clean_meeting_id:
            raise ValueError("meeting_id is required")
        if not clean_window_id:
            raise ValueError("window_id is required")
        if not clean_plugin_id:
            raise ValueError("plugin_id is required")
        if not clean_key:
            raise ValueError("idempotency_key is required")

        now_iso = datetime.now().isoformat()
        context_json = self._json_dumps(context or {}, fallback="{}")
        with self._connection() as conn:
            existing = conn.execute(
                """
                SELECT id FROM plugin_run_jobs
                WHERE idempotency_key = ?
                """,
                (clean_key,),
            ).fetchone()
            if existing is None:
                conn.execute(
                    """
                    INSERT INTO plugin_run_jobs (
                        meeting_id, window_id, plugin_id, plugin_version,
                        transcript_hash, idempotency_key, context_json, status,
                        requested_at, updated_at, attempts, last_error
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 'queued', ?, ?, 0, NULL)
                    """,
                    (
                        clean_meeting_id,
                        clean_window_id,
                        clean_plugin_id,
                        clean_plugin_version,
                        clean_hash,
                        clean_key,
                        context_json,
                        now_iso,
                        now_iso,
                    ),
                )
                return True

            conn.execute(
                """
                UPDATE plugin_run_jobs
                SET meeting_id = ?,
                    window_id = ?,
                    plugin_id = ?,
                    plugin_version = ?,
                    transcript_hash = ?,
                    context_json = ?,
                    status = CASE WHEN status = 'running' THEN status ELSE 'queued' END,
                    requested_at = CASE WHEN status = 'running' THEN requested_at ELSE ? END,
                    updated_at = ?,
                    last_error = NULL
                WHERE idempotency_key = ?
                """,
                (
                    clean_meeting_id,
                    clean_window_id,
                    clean_plugin_id,
                    clean_plugin_version,
                    clean_hash,
                    context_json,
                    now_iso,
                    now_iso,
                    clean_key,
                ),
            )
            return False

    def claim_next_plugin_run_job(
        self,
        *,
        include_scheduled: bool = False,
    ) -> Optional[PluginRunJob]:
        """Claim the next deferred MIR plugin run for processing."""
        now_iso = datetime.now().isoformat()
        with self._connection() as conn:
            row = conn.execute(
                """
                SELECT *
                FROM plugin_run_jobs
                WHERE status = 'queued'
                  AND (requested_at <= ? OR ? = 1)
                ORDER BY requested_at ASC, id ASC
                LIMIT 1
                """,
                (now_iso, 1 if include_scheduled else 0),
            ).fetchone()
            if row is None:
                return None
            job_id = int(row["id"])
            conn.execute(
                """
                UPDATE plugin_run_jobs
                SET status = 'running',
                    attempts = attempts + 1,
                    updated_at = ?
                WHERE id = ? AND status = 'queued'
                """,
                (now_iso, job_id),
            )
            claimed = conn.execute(
                "SELECT * FROM plugin_run_jobs WHERE id = ?",
                (job_id,),
            ).fetchone()
            if claimed is None:
                return None
            return self._row_to_plugin_run_job(claimed)

    def get_plugin_run_job(self, job_id: int) -> Optional[PluginRunJob]:
        """Load one deferred MIR plugin-run queue item by id."""
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM plugin_run_jobs WHERE id = ?",
                (int(job_id),),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_plugin_run_job(row)

    def retry_plugin_run_job(
        self,
        job_id: int,
        *,
        error: str,
        retry_at: datetime,
    ) -> None:
        """Requeue a deferred MIR plugin run for a later retry."""
        with self._connection() as conn:
            conn.execute(
                """
                UPDATE plugin_run_jobs
                SET status = 'queued',
                    requested_at = ?,
                    updated_at = ?,
                    last_error = ?
                WHERE id = ?
                """,
                (
                    retry_at.isoformat(),
                    datetime.now().isoformat(),
                    str(error),
                    int(job_id),
                ),
            )

    def fail_plugin_run_job(self, job_id: int, *, error: str) -> None:
        """Mark a deferred MIR plugin run as permanently failed."""
        with self._connection() as conn:
            conn.execute(
                """
                UPDATE plugin_run_jobs
                SET status = 'failed',
                    updated_at = ?,
                    last_error = ?
                WHERE id = ?
                """,
                (datetime.now().isoformat(), str(error), int(job_id)),
            )

    def complete_plugin_run_job(self, job_id: int) -> None:
        """Remove a completed deferred MIR plugin run from the queue."""
        with self._connection() as conn:
            conn.execute(
                "DELETE FROM plugin_run_jobs WHERE id = ?",
                (int(job_id),),
            )

    def list_plugin_run_jobs(
        self,
        *,
        status: str = "all",
        meeting_id: Optional[str] = None,
        limit: int = 200,
    ) -> list[PluginRunJob]:
        """List deferred MIR plugin-run queue items."""
        clean_status = str(status or "all").strip().lower()
        clean_meeting_id = str(meeting_id).strip() if isinstance(meeting_id, str) and meeting_id.strip() else None
        bounded_limit = max(1, min(int(limit), 5000))

        with self._connection() as conn:
            query = "SELECT * FROM plugin_run_jobs WHERE 1=1"
            params: list[Any] = []
            if clean_status != "all":
                query += " AND status = ?"
                params.append(clean_status)
            if clean_meeting_id:
                query += " AND meeting_id = ?"
                params.append(clean_meeting_id)
            query += " ORDER BY requested_at ASC, id ASC LIMIT ?"
            params.append(bounded_limit)
            rows = conn.execute(query, params).fetchall()

        return [self._row_to_plugin_run_job(row) for row in rows]

    def get_plugin_run_job_summary(self) -> PluginRunJobQueueSummary:
        """Return aggregate telemetry for deferred plugin-run queue state."""
        now_iso = datetime.now().isoformat()
        with self._connection() as conn:
            row = conn.execute(
                """
                SELECT
                    COUNT(*) AS total_jobs,
                    SUM(CASE WHEN status = 'queued' THEN 1 ELSE 0 END) AS queued_jobs,
                    SUM(CASE WHEN status = 'running' THEN 1 ELSE 0 END) AS running_jobs,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed_jobs,
                    SUM(CASE WHEN status = 'queued' AND requested_at <= ? THEN 1 ELSE 0 END) AS queued_due_jobs,
                    SUM(CASE WHEN status = 'queued' AND requested_at > ? THEN 1 ELSE 0 END) AS scheduled_retry_jobs
                FROM plugin_run_jobs
                """,
                (now_iso, now_iso),
            ).fetchone()

            next_row = conn.execute(
                """
                SELECT MIN(requested_at) AS next_retry_at
                FROM plugin_run_jobs
                WHERE status = 'queued'
                  AND requested_at > ?
                  AND last_error IS NOT NULL
                """,
                (now_iso,),
            ).fetchone()

        next_retry_at = None
        if next_row is not None and next_row["next_retry_at"]:
            next_retry_at = datetime.fromisoformat(next_row["next_retry_at"])

        return PluginRunJobQueueSummary(
            total_jobs=int(row["total_jobs"] or 0),
            queued_jobs=int(row["queued_jobs"] or 0),
            running_jobs=int(row["running_jobs"] or 0),
            failed_jobs=int(row["failed_jobs"] or 0),
            queued_due_jobs=int(row["queued_due_jobs"] or 0),
            scheduled_retry_jobs=int(row["scheduled_retry_jobs"] or 0),
            next_retry_at=next_retry_at,
        )

    def record_artifact(
        self,
        *,
        artifact_id: str,
        meeting_id: str,
        artifact_type: str,
        title: str,
        body_markdown: str = "",
        structured_json: Optional[dict[str, Any]] = None,
        confidence: float = 0.0,
        status: str = "draft",
        plugin_id: str = "unknown",
        plugin_version: str = "unknown",
        sources: Optional[list[dict[str, str]]] = None,
    ) -> None:
        """Insert or update one synthesized artifact and its lineage sources."""
        clean_artifact_id = str(artifact_id).strip()
        clean_meeting_id = str(meeting_id).strip()
        clean_type = str(artifact_type).strip().lower() or "plugin_output"
        clean_title = str(title).strip() or "Artifact"
        clean_body = str(body_markdown or "")
        clean_status = str(status).strip().lower() or "draft"
        clean_plugin_id = str(plugin_id).strip() or "unknown"
        clean_plugin_version = str(plugin_version).strip() or "unknown"
        if not clean_artifact_id:
            raise ValueError("artifact_id is required")
        if not clean_meeting_id:
            raise ValueError("meeting_id is required")
        if clean_status not in {"draft", "needs_review", "accepted", "rejected"}:
            raise ValueError(f"Invalid artifact status: {clean_status!r}")

        normalized_sources: list[tuple[str, str]] = []
        for source in sources or []:
            source_type = ""
            source_ref = ""
            if isinstance(source, dict):
                source_type = str(source.get("source_type") or "").strip().lower()
                source_ref = str(source.get("source_ref") or "").strip()
            elif isinstance(source, (tuple, list)) and len(source) == 2:
                source_type = str(source[0] or "").strip().lower()
                source_ref = str(source[1] or "").strip()
            if source_type and source_ref and (source_type, source_ref) not in normalized_sources:
                normalized_sources.append((source_type, source_ref))

        now_iso = datetime.now().isoformat()
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO artifacts (
                    id, meeting_id, artifact_type, title, body_markdown, structured_json,
                    confidence, status, plugin_id, plugin_version, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    meeting_id = excluded.meeting_id,
                    artifact_type = excluded.artifact_type,
                    title = excluded.title,
                    body_markdown = excluded.body_markdown,
                    structured_json = excluded.structured_json,
                    confidence = excluded.confidence,
                    status = excluded.status,
                    plugin_id = excluded.plugin_id,
                    plugin_version = excluded.plugin_version,
                    updated_at = excluded.updated_at
                """,
                (
                    clean_artifact_id,
                    clean_meeting_id,
                    clean_type,
                    clean_title,
                    clean_body,
                    self._json_dumps(structured_json or {}, fallback="{}"),
                    max(0.0, min(1.0, float(confidence))),
                    clean_status,
                    clean_plugin_id,
                    clean_plugin_version,
                    now_iso,
                    now_iso,
                ),
            )
            conn.execute(
                "DELETE FROM artifact_sources WHERE artifact_id = ?",
                (clean_artifact_id,),
            )
            for source_type, source_ref in normalized_sources:
                conn.execute(
                    """
                    INSERT INTO artifact_sources (artifact_id, source_type, source_ref, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (clean_artifact_id, source_type, source_ref, now_iso),
                )

    def list_artifacts(
        self,
        meeting_id: str,
        *,
        limit: int = 200,
    ) -> list[ArtifactSummary]:
        """List synthesized artifacts for one meeting, including lineage refs."""
        clean_meeting_id = str(meeting_id).strip()
        bounded_limit = max(1, min(int(limit), 2000))

        with self._connection() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM artifacts
                WHERE meeting_id = ?
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (clean_meeting_id, bounded_limit),
            ).fetchall()
            if not rows:
                return []

            artifact_ids = [str(row["id"]) for row in rows]
            placeholders = ",".join("?" for _ in artifact_ids)
            source_rows = conn.execute(
                f"""
                SELECT artifact_id, source_type, source_ref
                FROM artifact_sources
                WHERE artifact_id IN ({placeholders})
                ORDER BY source_type ASC, source_ref ASC
                """,
                artifact_ids,
            ).fetchall()

        sources_by_artifact: dict[str, list[dict[str, str]]] = {}
        for row in source_rows:
            artifact_id = str(row["artifact_id"])
            sources_by_artifact.setdefault(artifact_id, []).append(
                {
                    "source_type": str(row["source_type"]),
                    "source_ref": str(row["source_ref"]),
                }
            )

        output: list[ArtifactSummary] = []
        for row in rows:
            output.append(
                ArtifactSummary(
                    id=str(row["id"]),
                    meeting_id=str(row["meeting_id"]),
                    artifact_type=str(row["artifact_type"]),
                    title=str(row["title"]),
                    body_markdown=str(row["body_markdown"] or ""),
                    structured_json=self._json_loads_dict(row["structured_json"]),
                    confidence=float(row["confidence"] if row["confidence"] is not None else 0.0),
                    status=str(row["status"] or "draft"),
                    plugin_id=str(row["plugin_id"] or "unknown"),
                    plugin_version=str(row["plugin_version"] or "unknown"),
                    sources=sources_by_artifact.get(str(row["id"]), []),
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                )
            )
        return output

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
