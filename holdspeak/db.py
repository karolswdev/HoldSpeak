"""SQLite database persistence for HoldSpeak meetings."""

from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Iterator, Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .logging_config import get_logger

log = get_logger("db")

VALID_ACTION_ITEM_STATUSES = frozenset({"pending", "done", "dismissed"})
VALID_ACTION_ITEM_REVIEW_STATES = frozenset({"pending", "accepted"})
VALID_ACTIVITY_MEETING_CANDIDATE_STATUSES = frozenset(
    {"candidate", "armed", "dismissed", "started"}
)

# Default database location
DEFAULT_DB_PATH = Path.home() / ".local" / "share" / "holdspeak" / "holdspeak.db"
SCHEMA_VERSION = 16

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

-- Project knowledge bases
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    keywords_json TEXT NOT NULL DEFAULT '[]',
    team_members_json TEXT NOT NULL DEFAULT '[]',
    context_json TEXT NOT NULL DEFAULT '{}',
    detection_threshold REAL NOT NULL DEFAULT 0.4,
    is_archived INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Meeting-project associations
CREATE TABLE IF NOT EXISTS meeting_projects (
    meeting_id TEXT NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    source TEXT NOT NULL DEFAULT 'auto',
    confidence REAL NOT NULL DEFAULT 0.0,
    detected_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (meeting_id, project_id)
);

-- Per-window project detection audit log
CREATE TABLE IF NOT EXISTS project_detection_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meeting_id TEXT NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    window_id TEXT NOT NULL,
    score REAL NOT NULL,
    keyword_hits_json TEXT NOT NULL DEFAULT '[]',
    member_hits_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_projects_archived ON projects(is_archived, name);
CREATE INDEX IF NOT EXISTS idx_meeting_projects_project ON meeting_projects(project_id, detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_meeting_projects_meeting ON meeting_projects(meeting_id);
CREATE INDEX IF NOT EXISTS idx_project_detection_log_meeting ON project_detection_log(meeting_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_project_detection_log_project ON project_detection_log(project_id, created_at DESC);

-- Local activity intelligence ledger
CREATE TABLE IF NOT EXISTS activity_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_browser TEXT NOT NULL,
    source_profile TEXT NOT NULL DEFAULT '',
    source_path_hash TEXT NOT NULL DEFAULT '',
    url TEXT NOT NULL,
    normalized_url TEXT NOT NULL,
    title TEXT,
    domain TEXT NOT NULL DEFAULT '',
    visit_count INTEGER NOT NULL DEFAULT 0,
    first_seen_at TEXT,
    last_seen_at TEXT,
    last_visit_raw TEXT,
    entity_type TEXT,
    entity_id TEXT,
    project_id TEXT REFERENCES projects(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_activity_records_source_url
ON activity_records(source_browser, source_profile, normalized_url);
CREATE UNIQUE INDEX IF NOT EXISTS idx_activity_records_source_entity
ON activity_records(source_browser, source_profile, entity_type, entity_id)
WHERE entity_type IS NOT NULL AND entity_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_activity_records_last_seen
ON activity_records(last_seen_at DESC);
CREATE INDEX IF NOT EXISTS idx_activity_records_domain
ON activity_records(domain, last_seen_at DESC);
CREATE INDEX IF NOT EXISTS idx_activity_records_project
ON activity_records(project_id, last_seen_at DESC);

-- Per-source browser history import checkpoints
CREATE TABLE IF NOT EXISTS activity_import_checkpoints (
    source_browser TEXT NOT NULL,
    source_profile TEXT NOT NULL DEFAULT '',
    source_path_hash TEXT NOT NULL DEFAULT '',
    last_visit_raw TEXT,
    last_imported_at TEXT,
    last_error TEXT,
    enabled INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (source_browser, source_profile, source_path_hash)
);

-- Activity privacy controls
CREATE TABLE IF NOT EXISTS activity_privacy_settings (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    enabled INTEGER NOT NULL DEFAULT 1,
    retention_days INTEGER NOT NULL DEFAULT 30,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS activity_domain_rules (
    domain TEXT PRIMARY KEY,
    action TEXT NOT NULL DEFAULT 'exclude',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS activity_project_rules (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name TEXT NOT NULL DEFAULT '',
    enabled INTEGER NOT NULL DEFAULT 1,
    priority INTEGER NOT NULL DEFAULT 100,
    match_type TEXT NOT NULL,
    pattern TEXT NOT NULL,
    entity_type TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_activity_project_rules_enabled
ON activity_project_rules(enabled, priority DESC, created_at ASC);
CREATE INDEX IF NOT EXISTS idx_activity_project_rules_project
ON activity_project_rules(project_id, priority DESC);

-- Assisted activity enrichment connector state and local annotations
CREATE TABLE IF NOT EXISTS activity_enrichment_connectors (
    id TEXT PRIMARY KEY,
    enabled INTEGER NOT NULL DEFAULT 0,
    settings_json TEXT NOT NULL DEFAULT '{}',
    last_run_at TEXT,
    last_error TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS activity_annotations (
    id TEXT PRIMARY KEY,
    activity_record_id INTEGER REFERENCES activity_records(id) ON DELETE CASCADE,
    source_connector_id TEXT NOT NULL,
    annotation_type TEXT NOT NULL,
    title TEXT NOT NULL DEFAULT '',
    value_json TEXT NOT NULL DEFAULT '{}',
    confidence REAL NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_activity_annotations_record
ON activity_annotations(activity_record_id, annotation_type);
CREATE INDEX IF NOT EXISTS idx_activity_annotations_connector
ON activity_annotations(source_connector_id, created_at DESC);

CREATE TABLE IF NOT EXISTS activity_meeting_candidates (
    id TEXT PRIMARY KEY,
    source_connector_id TEXT NOT NULL,
    source_activity_record_id INTEGER REFERENCES activity_records(id) ON DELETE SET NULL,
    dedupe_key TEXT NOT NULL DEFAULT '',
    title TEXT NOT NULL,
    starts_at TEXT,
    ends_at TEXT,
    meeting_url TEXT,
    confidence REAL NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'candidate',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_activity_meeting_candidates_time
ON activity_meeting_candidates(starts_at, status);
CREATE INDEX IF NOT EXISTS idx_activity_meeting_candidates_connector
ON activity_meeting_candidates(source_connector_id, created_at DESC);
CREATE UNIQUE INDEX IF NOT EXISTS idx_activity_meeting_candidates_dedupe
ON activity_meeting_candidates(dedupe_key)
WHERE dedupe_key != '';
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
    source_timestamp: Optional[float]
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
class ProjectSummary:
    """User-defined project knowledge base."""

    id: str
    name: str
    description: str
    keywords: list[str]
    team_members: list[str]
    context: dict[str, Any]
    detection_threshold: float
    is_archived: bool
    meeting_count: int
    created_at: datetime
    updated_at: datetime


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


@dataclass
class ActivityRecord:
    """Normalized local activity record from browser history metadata."""

    id: int
    source_browser: str
    source_profile: str
    source_path_hash: str
    url: str
    normalized_url: str
    title: Optional[str]
    domain: str
    visit_count: int
    first_seen_at: Optional[datetime]
    last_seen_at: Optional[datetime]
    last_visit_raw: Optional[str]
    entity_type: Optional[str]
    entity_id: Optional[str]
    project_id: Optional[str]
    created_at: datetime
    updated_at: datetime


@dataclass
class ActivityImportCheckpoint:
    """Per browser/profile import checkpoint for local activity readers."""

    source_browser: str
    source_profile: str
    source_path_hash: str
    last_visit_raw: Optional[str]
    last_imported_at: Optional[datetime]
    last_error: Optional[str]
    enabled: bool
    created_at: datetime
    updated_at: datetime


@dataclass
class ActivityProjectRule:
    """User-defined rule for assigning local activity to a project."""

    id: str
    project_id: str
    project_name: Optional[str]
    name: str
    enabled: bool
    priority: int
    match_type: str
    pattern: str
    entity_type: Optional[str]
    created_at: datetime
    updated_at: datetime


@dataclass
class ActivityEnrichmentConnectorState:
    """Persisted state for an optional activity enrichment connector."""

    id: str
    enabled: bool
    settings: dict[str, Any]
    last_run_at: Optional[datetime]
    last_error: Optional[str]
    created_at: datetime
    updated_at: datetime


@dataclass
class ActivityAnnotation:
    """Local enrichment annotation attached to an activity record or entity."""

    id: str
    activity_record_id: Optional[int]
    source_connector_id: str
    annotation_type: str
    title: str
    value: dict[str, Any]
    confidence: float
    created_at: datetime
    updated_at: datetime


@dataclass
class ActivityMeetingCandidate:
    """Local candidate for a meeting action derived from activity metadata."""

    id: str
    source_connector_id: str
    source_activity_record_id: Optional[int]
    dedupe_key: str
    title: str
    starts_at: Optional[datetime]
    ends_at: Optional[datetime]
    meeting_url: Optional[str]
    confidence: float
    status: str
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

            if from_version < 10:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS projects (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        description TEXT NOT NULL DEFAULT '',
                        keywords_json TEXT NOT NULL DEFAULT '[]',
                        team_members_json TEXT NOT NULL DEFAULT '[]',
                        context_json TEXT NOT NULL DEFAULT '{}',
                        detection_threshold REAL NOT NULL DEFAULT 0.4,
                        is_archived INTEGER NOT NULL DEFAULT 0,
                        created_at TEXT NOT NULL DEFAULT (datetime('now')),
                        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS meeting_projects (
                        meeting_id TEXT NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
                        project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                        source TEXT NOT NULL DEFAULT 'auto',
                        confidence REAL NOT NULL DEFAULT 0.0,
                        detected_at TEXT NOT NULL DEFAULT (datetime('now')),
                        PRIMARY KEY (meeting_id, project_id)
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS project_detection_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        meeting_id TEXT NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
                        project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                        window_id TEXT NOT NULL,
                        score REAL NOT NULL,
                        keyword_hits_json TEXT NOT NULL DEFAULT '[]',
                        member_hits_json TEXT NOT NULL DEFAULT '[]',
                        created_at TEXT NOT NULL DEFAULT (datetime('now'))
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_projects_archived
                    ON projects(is_archived, name)
                    """
                )
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_meeting_projects_project
                    ON meeting_projects(project_id, detected_at DESC)
                    """
                )
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_meeting_projects_meeting
                    ON meeting_projects(meeting_id)
                    """
                )
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_project_detection_log_meeting
                    ON project_detection_log(meeting_id, created_at DESC)
                    """
                )
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_project_detection_log_project
                    ON project_detection_log(project_id, created_at DESC)
                    """
                )

            if from_version < 11:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS activity_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        source_browser TEXT NOT NULL,
                        source_profile TEXT NOT NULL DEFAULT '',
                        source_path_hash TEXT NOT NULL DEFAULT '',
                        url TEXT NOT NULL,
                        normalized_url TEXT NOT NULL,
                        title TEXT,
                        domain TEXT NOT NULL DEFAULT '',
                        visit_count INTEGER NOT NULL DEFAULT 0,
                        first_seen_at TEXT,
                        last_seen_at TEXT,
                        last_visit_raw TEXT,
                        entity_type TEXT,
                        entity_id TEXT,
                        project_id TEXT REFERENCES projects(id) ON DELETE SET NULL,
                        created_at TEXT NOT NULL DEFAULT (datetime('now')),
                        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE UNIQUE INDEX IF NOT EXISTS idx_activity_records_source_url
                    ON activity_records(source_browser, source_profile, normalized_url)
                    """
                )
                conn.execute(
                    """
                    CREATE UNIQUE INDEX IF NOT EXISTS idx_activity_records_source_entity
                    ON activity_records(source_browser, source_profile, entity_type, entity_id)
                    WHERE entity_type IS NOT NULL AND entity_id IS NOT NULL
                    """
                )
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_activity_records_last_seen
                    ON activity_records(last_seen_at DESC)
                    """
                )
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_activity_records_domain
                    ON activity_records(domain, last_seen_at DESC)
                    """
                )
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_activity_records_project
                    ON activity_records(project_id, last_seen_at DESC)
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS activity_import_checkpoints (
                        source_browser TEXT NOT NULL,
                        source_profile TEXT NOT NULL DEFAULT '',
                        source_path_hash TEXT NOT NULL DEFAULT '',
                        last_visit_raw TEXT,
                        last_imported_at TEXT,
                        last_error TEXT,
                        enabled INTEGER NOT NULL DEFAULT 1,
                        created_at TEXT NOT NULL DEFAULT (datetime('now')),
                        updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                        PRIMARY KEY (source_browser, source_profile, source_path_hash)
                    )
                    """
                )

            if from_version < 12:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS activity_privacy_settings (
                        id INTEGER PRIMARY KEY CHECK (id = 1),
                        enabled INTEGER NOT NULL DEFAULT 1,
                        retention_days INTEGER NOT NULL DEFAULT 30,
                        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
                    )
                    """
                )
                conn.execute(
                    """
                    INSERT OR IGNORE INTO activity_privacy_settings
                        (id, enabled, retention_days, updated_at)
                    VALUES (1, 1, 30, datetime('now'))
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS activity_domain_rules (
                        domain TEXT PRIMARY KEY,
                        action TEXT NOT NULL DEFAULT 'exclude',
                        created_at TEXT NOT NULL DEFAULT (datetime('now')),
                        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
                    )
                    """
                )

            if from_version < 13:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS activity_project_rules (
                        id TEXT PRIMARY KEY,
                        project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                        name TEXT NOT NULL DEFAULT '',
                        enabled INTEGER NOT NULL DEFAULT 1,
                        priority INTEGER NOT NULL DEFAULT 100,
                        match_type TEXT NOT NULL,
                        pattern TEXT NOT NULL,
                        entity_type TEXT,
                        created_at TEXT NOT NULL DEFAULT (datetime('now')),
                        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_activity_project_rules_enabled
                    ON activity_project_rules(enabled, priority DESC, created_at ASC)
                    """
                )
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_activity_project_rules_project
                    ON activity_project_rules(project_id, priority DESC)
                    """
                )

            if from_version < 14:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS activity_enrichment_connectors (
                        id TEXT PRIMARY KEY,
                        enabled INTEGER NOT NULL DEFAULT 0,
                        settings_json TEXT NOT NULL DEFAULT '{}',
                        last_run_at TEXT,
                        last_error TEXT,
                        created_at TEXT NOT NULL DEFAULT (datetime('now')),
                        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS activity_annotations (
                        id TEXT PRIMARY KEY,
                        activity_record_id INTEGER REFERENCES activity_records(id) ON DELETE CASCADE,
                        source_connector_id TEXT NOT NULL,
                        annotation_type TEXT NOT NULL,
                        title TEXT NOT NULL DEFAULT '',
                        value_json TEXT NOT NULL DEFAULT '{}',
                        confidence REAL NOT NULL DEFAULT 0,
                        created_at TEXT NOT NULL DEFAULT (datetime('now')),
                        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_activity_annotations_record
                    ON activity_annotations(activity_record_id, annotation_type)
                    """
                )
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_activity_annotations_connector
                    ON activity_annotations(source_connector_id, created_at DESC)
                    """
                )

            if from_version < 15:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS activity_meeting_candidates (
                        id TEXT PRIMARY KEY,
                        source_connector_id TEXT NOT NULL,
                        source_activity_record_id INTEGER REFERENCES activity_records(id) ON DELETE SET NULL,
                        dedupe_key TEXT NOT NULL DEFAULT '',
                        title TEXT NOT NULL,
                        starts_at TEXT,
                        ends_at TEXT,
                        meeting_url TEXT,
                        confidence REAL NOT NULL DEFAULT 0,
                        status TEXT NOT NULL DEFAULT 'candidate',
                        created_at TEXT NOT NULL DEFAULT (datetime('now')),
                        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_activity_meeting_candidates_time
                    ON activity_meeting_candidates(starts_at, status)
                    """
                )
                conn.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_activity_meeting_candidates_connector
                    ON activity_meeting_candidates(source_connector_id, created_at DESC)
                    """
                )

            if from_version < 16:
                try:
                    conn.execute("SELECT dedupe_key FROM activity_meeting_candidates LIMIT 1")
                except sqlite3.OperationalError:
                    conn.execute(
                        """
                        ALTER TABLE activity_meeting_candidates
                        ADD COLUMN dedupe_key TEXT NOT NULL DEFAULT ''
                        """
                    )
                conn.execute(
                    """
                    CREATE UNIQUE INDEX IF NOT EXISTS idx_activity_meeting_candidates_dedupe
                    ON activity_meeting_candidates(dedupe_key)
                    WHERE dedupe_key != ''
                    """
                )

        # Now apply the full schema (creates tables/indexes that don't exist)
        conn.executescript(SCHEMA_SQL)
        conn.execute(
            """
            INSERT OR IGNORE INTO activity_privacy_settings
                (id, enabled, retention_days, updated_at)
            VALUES (1, 1, 30, datetime('now'))
            """
        )

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
            source_timestamp=row['source_timestamp'],
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


    # ── Project knowledge bases ──────────────────────────────────────────

    def create_project(
        self,
        *,
        project_id: str,
        name: str,
        description: str = "",
        keywords: Optional[list[str]] = None,
        team_members: Optional[list[str]] = None,
        context: Optional[dict[str, Any]] = None,
        detection_threshold: float = 0.4,
    ) -> None:
        """Insert a new project knowledge base."""
        clean_id = str(project_id).strip()
        clean_name = str(name).strip()
        if not clean_id:
            raise ValueError("project_id is required")
        if not clean_name:
            raise ValueError("project name is required")
        threshold = max(0.0, min(1.0, float(detection_threshold)))
        now_iso = datetime.now().isoformat()
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO projects (
                    id, name, description, keywords_json, team_members_json,
                    context_json, detection_threshold, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    clean_id,
                    clean_name,
                    str(description or ""),
                    self._json_dumps(keywords or [], fallback="[]"),
                    self._json_dumps(team_members or [], fallback="[]"),
                    self._json_dumps(context or {}, fallback="{}"),
                    threshold,
                    now_iso,
                    now_iso,
                ),
            )

    def update_project(self, project_id: str, **fields: Any) -> None:
        """Update one or more project fields."""
        clean_id = str(project_id).strip()
        if not clean_id:
            raise ValueError("project_id is required")
        allowed = {
            "name", "description", "keywords", "team_members",
            "context", "detection_threshold", "is_archived",
        }
        updates: list[str] = []
        params: list[Any] = []
        for key, value in fields.items():
            if key not in allowed:
                continue
            if key == "name":
                clean = str(value).strip()
                if not clean:
                    raise ValueError("project name cannot be empty")
                updates.append("name = ?")
                params.append(clean)
            elif key == "description":
                updates.append("description = ?")
                params.append(str(value or ""))
            elif key == "keywords":
                updates.append("keywords_json = ?")
                params.append(self._json_dumps(value or [], fallback="[]"))
            elif key == "team_members":
                updates.append("team_members_json = ?")
                params.append(self._json_dumps(value or [], fallback="[]"))
            elif key == "context":
                updates.append("context_json = ?")
                params.append(self._json_dumps(value or {}, fallback="{}"))
            elif key == "detection_threshold":
                updates.append("detection_threshold = ?")
                params.append(max(0.0, min(1.0, float(value))))
            elif key == "is_archived":
                updates.append("is_archived = ?")
                params.append(1 if value else 0)
        if not updates:
            return
        updates.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        params.append(clean_id)
        with self._connection() as conn:
            conn.execute(
                f"UPDATE projects SET {', '.join(updates)} WHERE id = ?",
                params,
            )

    def get_project(self, project_id: str) -> Optional[ProjectSummary]:
        """Load a single project by ID."""
        clean_id = str(project_id).strip()
        if not clean_id:
            return None
        with self._connection() as conn:
            row = conn.execute(
                """
                SELECT p.*,
                       (SELECT COUNT(*) FROM meeting_projects mp WHERE mp.project_id = p.id) as meeting_count
                FROM projects p
                WHERE p.id = ?
                """,
                (clean_id,),
            ).fetchone()
            if not row:
                return None
            return self._row_to_project(row)

    def list_projects(self, *, include_archived: bool = False) -> list[ProjectSummary]:
        """List all projects with meeting counts."""
        with self._connection() as conn:
            if include_archived:
                rows = conn.execute(
                    """
                    SELECT p.*,
                           (SELECT COUNT(*) FROM meeting_projects mp WHERE mp.project_id = p.id) as meeting_count
                    FROM projects p
                    ORDER BY p.is_archived ASC, p.name ASC
                    """
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT p.*,
                           (SELECT COUNT(*) FROM meeting_projects mp WHERE mp.project_id = p.id) as meeting_count
                    FROM projects p
                    WHERE p.is_archived = 0
                    ORDER BY p.name ASC
                    """
                ).fetchall()
            return [self._row_to_project(row) for row in rows]

    def get_all_projects_for_detector(self) -> list[dict[str, Any]]:
        """Load lightweight project data for the project_detector plugin."""
        with self._connection() as conn:
            rows = conn.execute(
                """
                SELECT id, name, keywords_json, team_members_json, detection_threshold
                FROM projects
                WHERE is_archived = 0
                """
            ).fetchall()
            results: list[dict[str, Any]] = []
            for row in rows:
                results.append({
                    "id": row["id"],
                    "name": row["name"],
                    "keywords": self._json_loads_list(row["keywords_json"]),
                    "team_members": self._json_loads_list(row["team_members_json"]),
                    "detection_threshold": float(row["detection_threshold"]),
                })
            return results

    def associate_meeting_project(
        self,
        *,
        meeting_id: str,
        project_id: str,
        source: str = "auto",
        confidence: float = 0.0,
    ) -> None:
        """Create or update a meeting-project association."""
        now_iso = datetime.now().isoformat()
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO meeting_projects (meeting_id, project_id, source, confidence, detected_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(meeting_id, project_id) DO UPDATE SET
                    source = excluded.source,
                    confidence = MAX(meeting_projects.confidence, excluded.confidence),
                    detected_at = excluded.detected_at
                """,
                (
                    str(meeting_id).strip(),
                    str(project_id).strip(),
                    str(source).strip().lower() or "auto",
                    max(0.0, min(1.0, float(confidence))),
                    now_iso,
                ),
            )

    def disassociate_meeting_project(self, *, meeting_id: str, project_id: str) -> None:
        """Remove a meeting-project association."""
        with self._connection() as conn:
            conn.execute(
                "DELETE FROM meeting_projects WHERE meeting_id = ? AND project_id = ?",
                (str(meeting_id).strip(), str(project_id).strip()),
            )

    def get_meeting_projects(self, meeting_id: str) -> list[dict[str, Any]]:
        """List projects associated with a meeting."""
        with self._connection() as conn:
            rows = conn.execute(
                """
                SELECT mp.project_id, mp.source, mp.confidence, mp.detected_at,
                       p.name as project_name
                FROM meeting_projects mp
                JOIN projects p ON p.id = mp.project_id
                WHERE mp.meeting_id = ?
                ORDER BY mp.confidence DESC
                """,
                (str(meeting_id).strip(),),
            ).fetchall()
            return [
                {
                    "project_id": row["project_id"],
                    "project_name": row["project_name"],
                    "source": row["source"],
                    "confidence": row["confidence"],
                    "detected_at": row["detected_at"],
                }
                for row in rows
            ]

    def get_project_meetings(
        self, project_id: str, *, limit: int = 50, offset: int = 0
    ) -> list[dict[str, Any]]:
        """List meetings associated with a project."""
        with self._connection() as conn:
            rows = conn.execute(
                """
                SELECT m.id, m.title, m.started_at, m.duration_seconds,
                       m.intel_status, mp.source, mp.confidence
                FROM meeting_projects mp
                JOIN meetings m ON m.id = mp.meeting_id
                WHERE mp.project_id = ?
                ORDER BY m.started_at DESC
                LIMIT ? OFFSET ?
                """,
                (str(project_id).strip(), max(1, int(limit)), max(0, int(offset))),
            ).fetchall()
            return [
                {
                    "id": row["id"],
                    "title": row["title"],
                    "started_at": row["started_at"],
                    "duration_seconds": row["duration_seconds"],
                    "intel_status": row["intel_status"],
                    "source": row["source"],
                    "confidence": row["confidence"],
                }
                for row in rows
            ]

    def get_project_action_items(self, project_id: str) -> list[ActionItemSummary]:
        """List action items from all meetings associated with a project."""
        with self._connection() as conn:
            rows = conn.execute(
                """
                SELECT ai.id, ai.task, ai.owner, ai.due, ai.status, ai.review_state,
                       ai.source_timestamp,
                       ai.meeting_id, m.title as meeting_title, m.started_at as meeting_date,
                       ai.created_at, ai.completed_at, ai.reviewed_at
                FROM action_items ai
                JOIN meeting_projects mp ON mp.meeting_id = ai.meeting_id
                JOIN meetings m ON m.id = ai.meeting_id
                WHERE mp.project_id = ?
                ORDER BY ai.created_at DESC
                """,
                (str(project_id).strip(),),
            ).fetchall()
            return [
                ActionItemSummary(
                    id=row["id"],
                    task=row["task"],
                    owner=row["owner"],
                    due=row["due"],
                    status=row["status"],
                    review_state=row["review_state"],
                    meeting_id=row["meeting_id"],
                    meeting_title=row["meeting_title"],
                    meeting_date=datetime.fromisoformat(row["meeting_date"]),
                    source_timestamp=row["source_timestamp"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
                    reviewed_at=datetime.fromisoformat(row["reviewed_at"]) if row["reviewed_at"] else None,
                )
                for row in rows
            ]

    def get_project_artifacts(self, project_id: str) -> list[ArtifactSummary]:
        """List artifacts from all meetings associated with a project."""
        with self._connection() as conn:
            rows = conn.execute(
                """
                SELECT a.*
                FROM artifacts a
                JOIN meeting_projects mp ON mp.meeting_id = a.meeting_id
                WHERE mp.project_id = ?
                ORDER BY a.created_at DESC
                """,
                (str(project_id).strip(),),
            ).fetchall()
            results: list[ArtifactSummary] = []
            for row in rows:
                sources_rows = conn.execute(
                    "SELECT source_type, source_ref FROM artifact_sources WHERE artifact_id = ?",
                    (row["id"],),
                ).fetchall()
                sources = [
                    {"source_type": s["source_type"], "source_ref": s["source_ref"]}
                    for s in sources_rows
                ]
                results.append(
                    ArtifactSummary(
                        id=row["id"],
                        meeting_id=row["meeting_id"],
                        artifact_type=row["artifact_type"],
                        title=row["title"],
                        body_markdown=row["body_markdown"],
                        structured_json=self._json_loads_dict(row["structured_json"]),
                        confidence=float(row["confidence"]),
                        status=row["status"],
                        plugin_id=row["plugin_id"],
                        plugin_version=row["plugin_version"],
                        sources=sources,
                        created_at=datetime.fromisoformat(row["created_at"]),
                        updated_at=datetime.fromisoformat(row["updated_at"]),
                    )
                )
            return results

    def get_project_summary(self, project_id: str) -> dict[str, Any]:
        """Aggregated stats for a project: meeting count, action items by status, date range."""
        clean_id = str(project_id).strip()
        with self._connection() as conn:
            meeting_row = conn.execute(
                """
                SELECT COUNT(*) as meeting_count,
                       MIN(m.started_at) as first_meeting,
                       MAX(m.started_at) as last_meeting
                FROM meeting_projects mp
                JOIN meetings m ON m.id = mp.meeting_id
                WHERE mp.project_id = ?
                """,
                (clean_id,),
            ).fetchone()
            ai_rows = conn.execute(
                """
                SELECT ai.status, COUNT(*) as cnt
                FROM action_items ai
                JOIN meeting_projects mp ON mp.meeting_id = ai.meeting_id
                WHERE mp.project_id = ?
                GROUP BY ai.status
                """,
                (clean_id,),
            ).fetchall()
            artifact_count_row = conn.execute(
                """
                SELECT COUNT(*) as cnt
                FROM artifacts a
                JOIN meeting_projects mp ON mp.meeting_id = a.meeting_id
                WHERE mp.project_id = ?
                """,
                (clean_id,),
            ).fetchone()
            action_items_by_status = {row["status"]: row["cnt"] for row in ai_rows}
            return {
                "meeting_count": meeting_row["meeting_count"] or 0,
                "first_meeting": meeting_row["first_meeting"],
                "last_meeting": meeting_row["last_meeting"],
                "action_items_by_status": action_items_by_status,
                "artifact_count": artifact_count_row["cnt"] if artifact_count_row else 0,
            }

    # ── Local activity intelligence ledger ───────────────────────────────

    def _normalize_activity_url(self, url: object) -> str:
        clean = str(url or "").strip()
        if not clean:
            raise ValueError("url is required")
        parsed = urlsplit(clean)
        if not parsed.scheme or not parsed.netloc:
            return clean

        path = parsed.path or "/"
        if path != "/":
            path = path.rstrip("/")
        query_pairs = sorted(parse_qsl(parsed.query, keep_blank_values=True))
        query = urlencode(query_pairs, doseq=True)
        return urlunsplit(
            (
                parsed.scheme.lower(),
                parsed.netloc.lower(),
                path,
                query,
                "",
            )
        )

    def _activity_domain(self, normalized_url: str, domain: Optional[str]) -> str:
        clean_domain = str(domain or "").strip().lower()
        if clean_domain:
            return clean_domain
        parsed = urlsplit(normalized_url)
        return (parsed.hostname or "").lower()

    def _activity_time_to_iso(self, value: object) -> Optional[str]:
        if value in (None, ""):
            return None
        if isinstance(value, datetime):
            return value.isoformat()
        return str(value)

    def upsert_activity_record(
        self,
        *,
        source_browser: str,
        source_profile: str = "",
        source_path_hash: str = "",
        url: str,
        title: Optional[str] = None,
        domain: Optional[str] = None,
        visit_count: int = 1,
        first_seen_at: Optional[datetime] = None,
        last_seen_at: Optional[datetime] = None,
        last_visit_raw: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> ActivityRecord:
        """Insert or merge one normalized browser activity record."""
        clean_browser = str(source_browser or "").strip().lower()
        if not clean_browser:
            raise ValueError("source_browser is required")
        clean_profile = str(source_profile or "").strip()
        clean_path_hash = str(source_path_hash or "").strip()
        clean_url = str(url or "").strip()
        normalized_url = self._normalize_activity_url(clean_url)
        clean_domain = self._activity_domain(normalized_url, domain)
        clean_entity_type = (
            str(entity_type).strip().lower()
            if entity_type is not None and str(entity_type).strip()
            else None
        )
        clean_entity_id = (
            str(entity_id).strip()
            if entity_id is not None and str(entity_id).strip()
            else None
        )
        clean_project_id = (
            str(project_id).strip()
            if project_id is not None and str(project_id).strip()
            else None
        )
        now_iso = datetime.now().isoformat()
        first_seen_iso = self._activity_time_to_iso(first_seen_at) or self._activity_time_to_iso(last_seen_at)
        last_seen_iso = self._activity_time_to_iso(last_seen_at) or first_seen_iso
        raw_timestamp = str(last_visit_raw) if last_visit_raw not in (None, "") else None

        with self._connection() as conn:
            existing = conn.execute(
                """
                SELECT *
                FROM activity_records
                WHERE source_browser = ?
                  AND source_profile = ?
                  AND (
                    normalized_url = ?
                    OR (
                        ? IS NOT NULL
                        AND ? IS NOT NULL
                        AND entity_type = ?
                        AND entity_id = ?
                    )
                  )
                ORDER BY
                    CASE WHEN normalized_url = ? THEN 0 ELSE 1 END,
                    updated_at DESC
                LIMIT 1
                """,
                (
                    clean_browser,
                    clean_profile,
                    normalized_url,
                    clean_entity_type,
                    clean_entity_id,
                    clean_entity_type,
                    clean_entity_id,
                    normalized_url,
                ),
            ).fetchone()

            if existing is None:
                cursor = conn.execute(
                    """
                    INSERT INTO activity_records (
                        source_browser, source_profile, source_path_hash, url,
                        normalized_url, title, domain, visit_count, first_seen_at,
                        last_seen_at, last_visit_raw, entity_type, entity_id,
                        project_id, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        clean_browser,
                        clean_profile,
                        clean_path_hash,
                        clean_url,
                        normalized_url,
                        title,
                        clean_domain,
                        max(0, int(visit_count)),
                        first_seen_iso,
                        last_seen_iso,
                        raw_timestamp,
                        clean_entity_type,
                        clean_entity_id,
                        clean_project_id,
                        now_iso,
                        now_iso,
                    ),
                )
                record_id = int(cursor.lastrowid)
            else:
                record_id = int(existing["id"])
                existing_first = existing["first_seen_at"]
                existing_last = existing["last_seen_at"]
                merged_first = min(
                    [value for value in (existing_first, first_seen_iso) if value],
                    default=None,
                )
                merged_last = max(
                    [value for value in (existing_last, last_seen_iso) if value],
                    default=None,
                )
                conn.execute(
                    """
                    UPDATE activity_records
                    SET source_path_hash = COALESCE(NULLIF(?, ''), source_path_hash),
                        url = ?,
                        normalized_url = ?,
                        title = COALESCE(?, title),
                        domain = ?,
                        visit_count = MAX(visit_count, ?),
                        first_seen_at = ?,
                        last_seen_at = ?,
                        last_visit_raw = COALESCE(?, last_visit_raw),
                        entity_type = COALESCE(?, entity_type),
                        entity_id = COALESCE(?, entity_id),
                        project_id = COALESCE(?, project_id),
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        clean_path_hash,
                        clean_url,
                        normalized_url,
                        title,
                        clean_domain,
                        max(0, int(visit_count)),
                        merged_first,
                        merged_last,
                        raw_timestamp,
                        clean_entity_type,
                        clean_entity_id,
                        clean_project_id,
                        now_iso,
                        record_id,
                    ),
                )

            row = conn.execute(
                "SELECT * FROM activity_records WHERE id = ?",
                (record_id,),
            ).fetchone()
            return self._row_to_activity_record(row)

    def list_activity_records(
        self,
        *,
        source_browser: Optional[str] = None,
        source_profile: Optional[str] = None,
        project_id: Optional[str] = None,
        domain: Optional[str] = None,
        entity_type: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> list[ActivityRecord]:
        """List normalized activity records for recent-context surfaces."""
        where: list[str] = []
        params: list[Any] = []
        if source_browser:
            where.append("source_browser = ?")
            params.append(str(source_browser).strip().lower())
        if source_profile is not None:
            where.append("source_profile = ?")
            params.append(str(source_profile).strip())
        if project_id:
            where.append("project_id = ?")
            params.append(str(project_id).strip())
        if domain:
            where.append("domain = ?")
            params.append(str(domain).strip().lower())
        if entity_type:
            where.append("entity_type = ?")
            params.append(str(entity_type).strip().lower())
        if since is not None:
            where.append("last_seen_at >= ?")
            params.append(since.isoformat())

        query = "SELECT * FROM activity_records"
        if where:
            query += " WHERE " + " AND ".join(where)
        query += " ORDER BY last_seen_at DESC, updated_at DESC, id DESC LIMIT ?"
        params.append(max(1, min(int(limit), 5000)))
        with self._connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_activity_record(row) for row in rows]

    def delete_activity_records(
        self,
        *,
        source_browser: Optional[str] = None,
        source_profile: Optional[str] = None,
        project_id: Optional[str] = None,
        domain: Optional[str] = None,
        older_than: Optional[datetime] = None,
    ) -> int:
        """Delete imported activity records for clear/retention controls."""
        where: list[str] = []
        params: list[Any] = []
        if source_browser:
            where.append("source_browser = ?")
            params.append(str(source_browser).strip().lower())
        if source_profile is not None:
            where.append("source_profile = ?")
            params.append(str(source_profile).strip())
        if project_id:
            where.append("project_id = ?")
            params.append(str(project_id).strip())
        if domain:
            where.append("domain = ?")
            params.append(str(domain).strip().lower())
        if older_than is not None:
            where.append("last_seen_at < ?")
            params.append(older_than.isoformat())
        query = "DELETE FROM activity_records"
        if where:
            query += " WHERE " + " AND ".join(where)
        with self._connection() as conn:
            cursor = conn.execute(query, params)
            return int(cursor.rowcount if cursor.rowcount is not None else 0)

    def set_activity_import_checkpoint(
        self,
        *,
        source_browser: str,
        source_profile: str = "",
        source_path_hash: str = "",
        last_visit_raw: Optional[str] = None,
        last_imported_at: Optional[datetime] = None,
        last_error: Optional[str] = None,
        enabled: bool = True,
    ) -> ActivityImportCheckpoint:
        """Create or update a browser history import checkpoint."""
        clean_browser = str(source_browser or "").strip().lower()
        if not clean_browser:
            raise ValueError("source_browser is required")
        clean_profile = str(source_profile or "").strip()
        clean_path_hash = str(source_path_hash or "").strip()
        now_iso = datetime.now().isoformat()
        imported_iso = (
            last_imported_at.isoformat()
            if isinstance(last_imported_at, datetime)
            else now_iso
        )
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO activity_import_checkpoints (
                    source_browser, source_profile, source_path_hash,
                    last_visit_raw, last_imported_at, last_error, enabled,
                    created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source_browser, source_profile, source_path_hash)
                DO UPDATE SET
                    last_visit_raw = excluded.last_visit_raw,
                    last_imported_at = excluded.last_imported_at,
                    last_error = excluded.last_error,
                    enabled = excluded.enabled,
                    updated_at = excluded.updated_at
                """,
                (
                    clean_browser,
                    clean_profile,
                    clean_path_hash,
                    str(last_visit_raw) if last_visit_raw not in (None, "") else None,
                    imported_iso,
                    str(last_error) if last_error not in (None, "") else None,
                    int(bool(enabled)),
                    now_iso,
                    now_iso,
                ),
            )
            row = conn.execute(
                """
                SELECT *
                FROM activity_import_checkpoints
                WHERE source_browser = ?
                  AND source_profile = ?
                  AND source_path_hash = ?
                """,
                (clean_browser, clean_profile, clean_path_hash),
            ).fetchone()
            return self._row_to_activity_checkpoint(row)

    def list_activity_import_checkpoints(self) -> list[ActivityImportCheckpoint]:
        """List all browser history import checkpoints."""
        with self._connection() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM activity_import_checkpoints
                ORDER BY source_browser ASC, source_profile ASC, source_path_hash ASC
                """
            ).fetchall()
            return [self._row_to_activity_checkpoint(row) for row in rows]

    def get_activity_import_checkpoint(
        self,
        *,
        source_browser: str,
        source_profile: str = "",
        source_path_hash: str = "",
    ) -> Optional[ActivityImportCheckpoint]:
        """Load one browser history import checkpoint."""
        with self._connection() as conn:
            row = conn.execute(
                """
                SELECT *
                FROM activity_import_checkpoints
                WHERE source_browser = ?
                  AND source_profile = ?
                  AND source_path_hash = ?
                """,
                (
                    str(source_browser or "").strip().lower(),
                    str(source_profile or "").strip(),
                    str(source_path_hash or "").strip(),
                ),
            ).fetchone()
            if row is None:
                return None
            return self._row_to_activity_checkpoint(row)

    def get_activity_privacy_settings(self) -> dict[str, Any]:
        """Return activity ingestion privacy settings with defaults."""
        with self._connection() as conn:
            row = conn.execute(
                """
                SELECT enabled, retention_days, updated_at
                FROM activity_privacy_settings
                WHERE id = 1
                """
            ).fetchone()
            if row is None:
                conn.execute(
                    """
                    INSERT INTO activity_privacy_settings
                        (id, enabled, retention_days, updated_at)
                    VALUES (1, 1, 30, ?)
                    """,
                    (datetime.now().isoformat(),),
                )
                row = conn.execute(
                    """
                    SELECT enabled, retention_days, updated_at
                    FROM activity_privacy_settings
                    WHERE id = 1
                    """
                ).fetchone()
            return {
                "enabled": bool(row["enabled"]),
                "paused": not bool(row["enabled"]),
                "retention_days": int(row["retention_days"] or 30),
                "updated_at": str(row["updated_at"]),
            }

    def update_activity_privacy_settings(
        self,
        *,
        enabled: Optional[bool] = None,
        retention_days: Optional[int] = None,
    ) -> dict[str, Any]:
        """Update activity ingestion privacy settings."""
        current = self.get_activity_privacy_settings()
        next_enabled = current["enabled"] if enabled is None else bool(enabled)
        next_retention = current["retention_days"]
        if retention_days is not None:
            next_retention = max(1, min(int(retention_days), 3650))
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO activity_privacy_settings
                    (id, enabled, retention_days, updated_at)
                VALUES (1, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    enabled = excluded.enabled,
                    retention_days = excluded.retention_days,
                    updated_at = excluded.updated_at
                """,
                (int(next_enabled), int(next_retention), datetime.now().isoformat()),
            )
        return self.get_activity_privacy_settings()

    def list_activity_domain_rules(self) -> list[dict[str, str]]:
        """List domain allow/deny rules for activity ingestion."""
        with self._connection() as conn:
            rows = conn.execute(
                """
                SELECT domain, action, created_at, updated_at
                FROM activity_domain_rules
                ORDER BY domain ASC
                """
            ).fetchall()
            return [
                {
                    "domain": str(row["domain"]),
                    "action": str(row["action"] or "exclude"),
                    "created_at": str(row["created_at"]),
                    "updated_at": str(row["updated_at"]),
                }
                for row in rows
            ]

    def upsert_activity_domain_rule(
        self,
        *,
        domain: str,
        action: str = "exclude",
    ) -> dict[str, str]:
        """Create or update one activity domain privacy rule."""
        clean_domain = str(domain or "").strip().lower()
        if not clean_domain:
            raise ValueError("domain is required")
        clean_action = str(action or "exclude").strip().lower()
        if clean_action not in {"exclude", "allow"}:
            raise ValueError("activity domain action must be 'exclude' or 'allow'")
        now_iso = datetime.now().isoformat()
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO activity_domain_rules (domain, action, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(domain) DO UPDATE SET
                    action = excluded.action,
                    updated_at = excluded.updated_at
                """,
                (clean_domain, clean_action, now_iso, now_iso),
            )
        return next(
            rule for rule in self.list_activity_domain_rules()
            if rule["domain"] == clean_domain
        )

    def delete_activity_domain_rule(self, domain: str) -> bool:
        """Delete one activity domain privacy rule."""
        clean_domain = str(domain or "").strip().lower()
        if not clean_domain:
            return False
        with self._connection() as conn:
            cursor = conn.execute(
                "DELETE FROM activity_domain_rules WHERE domain = ?",
                (clean_domain,),
            )
            return bool(cursor.rowcount)

    def is_activity_domain_excluded(self, domain: str) -> bool:
        """Return true if a domain or one of its parents is excluded."""
        clean_domain = str(domain or "").strip().lower()
        if not clean_domain:
            return False
        with self._connection() as conn:
            rows = conn.execute(
                """
                SELECT domain, action
                FROM activity_domain_rules
                WHERE action = 'exclude'
                """
            ).fetchall()
        for row in rows:
            rule_domain = str(row["domain"] or "").lower()
            if clean_domain == rule_domain or clean_domain.endswith(f".{rule_domain}"):
                return True
        return False

    def create_activity_project_rule(
        self,
        *,
        project_id: str,
        name: str = "",
        match_type: str,
        pattern: str,
        entity_type: Optional[str] = None,
        priority: int = 100,
        enabled: bool = True,
        rule_id: Optional[str] = None,
    ) -> ActivityProjectRule:
        """Create a deterministic rule that maps activity records to a project."""
        clean_project_id = str(project_id or "").strip()
        if not clean_project_id:
            raise ValueError("project_id is required")
        if self.get_project(clean_project_id) is None:
            raise ValueError(f"project not found: {clean_project_id}")
        clean_match_type, clean_pattern, clean_entity_type = self._normalize_activity_project_rule_fields(
            match_type=match_type,
            pattern=pattern,
            entity_type=entity_type,
        )
        clean_id = str(rule_id or f"apr-{uuid.uuid4().hex[:12]}").strip()
        now_iso = datetime.now().isoformat()
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO activity_project_rules (
                    id, project_id, name, enabled, priority, match_type,
                    pattern, entity_type, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    clean_id,
                    clean_project_id,
                    str(name or "").strip(),
                    int(bool(enabled)),
                    int(priority),
                    clean_match_type,
                    clean_pattern,
                    clean_entity_type,
                    now_iso,
                    now_iso,
                ),
            )
        rule = self.get_activity_project_rule(clean_id)
        if rule is None:
            raise RuntimeError("activity project rule was not created")
        return rule

    def get_activity_project_rule(self, rule_id: str) -> Optional[ActivityProjectRule]:
        """Load one activity project mapping rule."""
        clean_id = str(rule_id or "").strip()
        if not clean_id:
            return None
        with self._connection() as conn:
            row = conn.execute(
                """
                SELECT apr.*, p.name AS project_name
                FROM activity_project_rules apr
                LEFT JOIN projects p ON p.id = apr.project_id
                WHERE apr.id = ?
                """,
                (clean_id,),
            ).fetchone()
            if row is None:
                return None
            return self._row_to_activity_project_rule(row)

    def update_activity_project_rule(
        self,
        rule_id: str,
        **fields: Any,
    ) -> Optional[ActivityProjectRule]:
        """Update one activity project mapping rule."""
        clean_id = str(rule_id or "").strip()
        if not clean_id:
            return None
        allowed = {
            "project_id",
            "name",
            "enabled",
            "priority",
            "match_type",
            "pattern",
            "entity_type",
        }
        current = self.get_activity_project_rule(clean_id)
        if current is None:
            return None

        next_match_type = fields.get("match_type", current.match_type)
        next_pattern = fields.get("pattern", current.pattern)
        next_entity_type = fields.get("entity_type", current.entity_type)
        clean_match_type, clean_pattern, clean_entity_type = self._normalize_activity_project_rule_fields(
            match_type=next_match_type,
            pattern=next_pattern,
            entity_type=next_entity_type,
        )

        updates: list[str] = []
        params: list[Any] = []
        for key, value in fields.items():
            if key not in allowed:
                continue
            if key == "project_id":
                clean_project_id = str(value or "").strip()
                if not clean_project_id:
                    raise ValueError("project_id is required")
                if self.get_project(clean_project_id) is None:
                    raise ValueError(f"project not found: {clean_project_id}")
                updates.append("project_id = ?")
                params.append(clean_project_id)
            elif key == "name":
                updates.append("name = ?")
                params.append(str(value or "").strip())
            elif key == "enabled":
                updates.append("enabled = ?")
                params.append(int(bool(value)))
            elif key == "priority":
                updates.append("priority = ?")
                params.append(int(value))
            elif key == "match_type":
                updates.append("match_type = ?")
                params.append(clean_match_type)
            elif key == "pattern":
                updates.append("pattern = ?")
                params.append(clean_pattern)
            elif key == "entity_type":
                updates.append("entity_type = ?")
                params.append(clean_entity_type)
        if not updates:
            return current
        updates.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        params.append(clean_id)
        with self._connection() as conn:
            conn.execute(
                f"UPDATE activity_project_rules SET {', '.join(updates)} WHERE id = ?",
                params,
            )
        return self.get_activity_project_rule(clean_id)

    def delete_activity_project_rule(self, rule_id: str) -> bool:
        """Delete one activity project mapping rule."""
        clean_id = str(rule_id or "").strip()
        if not clean_id:
            return False
        with self._connection() as conn:
            cursor = conn.execute(
                "DELETE FROM activity_project_rules WHERE id = ?",
                (clean_id,),
            )
            return bool(cursor.rowcount)

    def list_activity_project_rules(
        self,
        *,
        include_disabled: bool = False,
    ) -> list[ActivityProjectRule]:
        """List activity project rules in deterministic matching order."""
        query = """
            SELECT apr.*, p.name AS project_name
            FROM activity_project_rules apr
            LEFT JOIN projects p ON p.id = apr.project_id
        """
        params: list[Any] = []
        if not include_disabled:
            query += " WHERE apr.enabled = 1"
        query += " ORDER BY apr.priority DESC, apr.created_at ASC, apr.id ASC"
        with self._connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_activity_project_rule(row) for row in rows]

    def preview_activity_project_rule(
        self,
        *,
        project_id: str,
        match_type: str,
        pattern: str,
        entity_type: Optional[str] = None,
        limit: int = 50,
    ) -> list[ActivityRecord]:
        """Preview existing records that would match a proposed rule."""
        from .activity_mapping import first_matching_rule

        clean_project_id = str(project_id or "").strip()
        if not clean_project_id:
            raise ValueError("project_id is required")
        if self.get_project(clean_project_id) is None:
            raise ValueError(f"project not found: {clean_project_id}")
        clean_match_type, clean_pattern, clean_entity_type = self._normalize_activity_project_rule_fields(
            match_type=match_type,
            pattern=pattern,
            entity_type=entity_type,
        )
        now = datetime.now()
        rule = ActivityProjectRule(
            id="preview",
            project_id=clean_project_id,
            project_name=None,
            name="",
            enabled=True,
            priority=0,
            match_type=clean_match_type,
            pattern=clean_pattern,
            entity_type=clean_entity_type,
            created_at=now,
            updated_at=now,
        )
        matches: list[ActivityRecord] = []
        for record in self._iter_activity_records():
            if first_matching_rule(record, [rule]) is not None:
                matches.append(record)
            if len(matches) >= max(1, min(int(limit), 500)):
                break
        return matches

    def apply_activity_project_rules(self, *, limit: Optional[int] = None) -> int:
        """Backfill existing activity records from enabled project mapping rules."""
        from .activity_mapping import project_id_for_record

        rules = self.list_activity_project_rules(include_disabled=False)
        if not rules:
            return 0
        updated = 0
        cap = None if limit is None else max(1, int(limit))
        for record in self._iter_activity_records():
            project_id = project_id_for_record(record, rules)
            if project_id and project_id != record.project_id:
                self.assign_activity_record_project(record.id, project_id)
                updated += 1
                if cap is not None and updated >= cap:
                    break
        return updated

    def assign_activity_record_project(self, record_id: int, project_id: Optional[str]) -> bool:
        """Assign or clear a project ID on one existing activity record."""
        clean_project_id = (
            str(project_id).strip()
            if project_id is not None and str(project_id).strip()
            else None
        )
        if clean_project_id is not None and self.get_project(clean_project_id) is None:
            raise ValueError(f"project not found: {clean_project_id}")
        with self._connection() as conn:
            cursor = conn.execute(
                """
                UPDATE activity_records
                SET project_id = ?, updated_at = ?
                WHERE id = ?
                """,
                (clean_project_id, datetime.now().isoformat(), int(record_id)),
            )
            return bool(cursor.rowcount)

    def match_activity_project_rule(
        self,
        record: ActivityRecord,
        rules: Optional[list[ActivityProjectRule]] = None,
    ) -> Optional[ActivityProjectRule]:
        """Return the first enabled mapping rule for an activity record."""
        from .activity_mapping import first_matching_rule

        return first_matching_rule(
            record,
            rules if rules is not None else self.list_activity_project_rules(include_disabled=False),
        )

    def _iter_activity_records(self) -> Iterator[ActivityRecord]:
        """Iterate all activity records in recent-first order without the public cap."""
        with self._connection() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM activity_records
                ORDER BY last_seen_at DESC, updated_at DESC, id DESC
                """
            ).fetchall()
            return iter([self._row_to_activity_record(row) for row in rows])

    def _normalize_activity_project_rule_fields(
        self,
        *,
        match_type: object,
        pattern: object,
        entity_type: Optional[object] = None,
    ) -> tuple[str, str, Optional[str]]:
        from .activity_mapping import normalize_match_type

        clean_match_type = normalize_match_type(match_type)
        clean_pattern = str(pattern or "").strip()
        if not clean_pattern:
            raise ValueError("pattern is required")
        clean_entity_type = (
            str(entity_type).strip().lower()
            if entity_type is not None and str(entity_type).strip()
            else None
        )
        if clean_match_type == "entity_type":
            clean_pattern = clean_pattern.lower()
            clean_entity_type = None
        elif clean_match_type in {"domain", "url_contains", "title_contains", "github_repo", "source_browser"}:
            clean_pattern = clean_pattern.lower()
        return clean_match_type, clean_pattern, clean_entity_type

    def upsert_activity_enrichment_connector(
        self,
        *,
        connector_id: str,
        enabled: Optional[bool] = None,
        settings: Optional[dict[str, Any]] = None,
        last_run_at: Optional[datetime] = None,
        last_error: Optional[str] = None,
    ) -> ActivityEnrichmentConnectorState:
        """Create or update persisted state for one enrichment connector."""
        clean_id = str(connector_id or "").strip()
        if not clean_id:
            raise ValueError("connector_id is required")
        current = self.get_activity_enrichment_connector(clean_id)
        next_enabled = bool(enabled) if enabled is not None else (current.enabled if current else False)
        next_settings = settings if settings is not None else (current.settings if current else {})
        now_iso = datetime.now().isoformat()
        last_run_iso = (
            last_run_at.isoformat()
            if isinstance(last_run_at, datetime)
            else (current.last_run_at.isoformat() if current and current.last_run_at else None)
        )
        clean_error = (
            str(last_error)
            if last_error not in (None, "")
            else (current.last_error if current and last_error is None else None)
        )
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO activity_enrichment_connectors (
                    id, enabled, settings_json, last_run_at, last_error,
                    created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    enabled = excluded.enabled,
                    settings_json = excluded.settings_json,
                    last_run_at = excluded.last_run_at,
                    last_error = excluded.last_error,
                    updated_at = excluded.updated_at
                """,
                (
                    clean_id,
                    int(next_enabled),
                    self._json_dumps(next_settings or {}, fallback="{}"),
                    last_run_iso,
                    clean_error,
                    now_iso,
                    now_iso,
                ),
            )
        state = self.get_activity_enrichment_connector(clean_id)
        if state is None:
            raise RuntimeError("activity enrichment connector was not created")
        return state

    def get_activity_enrichment_connector(
        self,
        connector_id: str,
    ) -> Optional[ActivityEnrichmentConnectorState]:
        """Load persisted state for one enrichment connector."""
        clean_id = str(connector_id or "").strip()
        if not clean_id:
            return None
        with self._connection() as conn:
            row = conn.execute(
                """
                SELECT *
                FROM activity_enrichment_connectors
                WHERE id = ?
                """,
                (clean_id,),
            ).fetchone()
            if row is None:
                return None
            return self._row_to_activity_enrichment_connector(row)

    def list_activity_enrichment_connectors(self) -> list[ActivityEnrichmentConnectorState]:
        """List persisted enrichment connector states."""
        with self._connection() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM activity_enrichment_connectors
                ORDER BY id ASC
                """
            ).fetchall()
            return [self._row_to_activity_enrichment_connector(row) for row in rows]

    def record_activity_enrichment_run(
        self,
        *,
        connector_id: str,
        last_run_at: Optional[datetime] = None,
        last_error: Optional[str] = None,
    ) -> ActivityEnrichmentConnectorState:
        """Persist the latest run result for one enrichment connector."""
        state = self.get_activity_enrichment_connector(connector_id)
        return self.upsert_activity_enrichment_connector(
            connector_id=connector_id,
            enabled=state.enabled if state else False,
            settings=state.settings if state else {},
            last_run_at=last_run_at or datetime.now(),
            last_error=last_error if last_error is not None else "",
        )

    def create_activity_annotation(
        self,
        *,
        source_connector_id: str,
        annotation_type: str,
        title: str = "",
        value: Optional[dict[str, Any]] = None,
        confidence: float = 0.0,
        activity_record_id: Optional[int] = None,
        annotation_id: Optional[str] = None,
    ) -> ActivityAnnotation:
        """Persist one local enrichment annotation."""
        clean_connector = str(source_connector_id or "").strip()
        if not clean_connector:
            raise ValueError("source_connector_id is required")
        clean_type = str(annotation_type or "").strip().lower()
        if not clean_type:
            raise ValueError("annotation_type is required")
        clean_id = str(annotation_id or f"ann-{uuid.uuid4().hex[:12]}").strip()
        record_id = int(activity_record_id) if activity_record_id is not None else None
        now_iso = datetime.now().isoformat()
        with self._connection() as conn:
            if record_id is not None:
                exists = conn.execute(
                    "SELECT 1 FROM activity_records WHERE id = ?",
                    (record_id,),
                ).fetchone()
                if exists is None:
                    raise ValueError(f"activity record not found: {record_id}")
            conn.execute(
                """
                INSERT INTO activity_annotations (
                    id, activity_record_id, source_connector_id, annotation_type,
                    title, value_json, confidence, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    clean_id,
                    record_id,
                    clean_connector,
                    clean_type,
                    str(title or "").strip(),
                    self._json_dumps(value or {}, fallback="{}"),
                    max(0.0, min(1.0, float(confidence))),
                    now_iso,
                    now_iso,
                ),
            )
            row = conn.execute(
                "SELECT * FROM activity_annotations WHERE id = ?",
                (clean_id,),
            ).fetchone()
            return self._row_to_activity_annotation(row)

    def list_activity_annotations(
        self,
        *,
        activity_record_id: Optional[int] = None,
        source_connector_id: Optional[str] = None,
        annotation_type: Optional[str] = None,
        limit: int = 100,
    ) -> list[ActivityAnnotation]:
        """List local enrichment annotations."""
        where: list[str] = []
        params: list[Any] = []
        if activity_record_id is not None:
            where.append("activity_record_id = ?")
            params.append(int(activity_record_id))
        if source_connector_id:
            where.append("source_connector_id = ?")
            params.append(str(source_connector_id).strip())
        if annotation_type:
            where.append("annotation_type = ?")
            params.append(str(annotation_type).strip().lower())
        query = "SELECT * FROM activity_annotations"
        if where:
            query += " WHERE " + " AND ".join(where)
        query += " ORDER BY created_at DESC, id DESC LIMIT ?"
        params.append(max(1, min(int(limit), 5000)))
        with self._connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_activity_annotation(row) for row in rows]

    def delete_activity_annotations(
        self,
        *,
        activity_record_id: Optional[int] = None,
        source_connector_id: Optional[str] = None,
        annotation_type: Optional[str] = None,
    ) -> int:
        """Delete local enrichment annotations by connector, record, or type."""
        where: list[str] = []
        params: list[Any] = []
        if activity_record_id is not None:
            where.append("activity_record_id = ?")
            params.append(int(activity_record_id))
        if source_connector_id:
            where.append("source_connector_id = ?")
            params.append(str(source_connector_id).strip())
        if annotation_type:
            where.append("annotation_type = ?")
            params.append(str(annotation_type).strip().lower())
        query = "DELETE FROM activity_annotations"
        if where:
            query += " WHERE " + " AND ".join(where)
        with self._connection() as conn:
            cursor = conn.execute(query, params)
            return int(cursor.rowcount if cursor.rowcount is not None else 0)

    def create_activity_meeting_candidate(
        self,
        *,
        source_connector_id: str,
        title: str,
        source_activity_record_id: Optional[int] = None,
        starts_at: Optional[datetime] = None,
        ends_at: Optional[datetime] = None,
        meeting_url: Optional[str] = None,
        confidence: float = 0.0,
        status: str = "candidate",
        candidate_id: Optional[str] = None,
    ) -> ActivityMeetingCandidate:
        """Persist one local meeting candidate from an enrichment connector."""
        clean_connector = str(source_connector_id or "").strip()
        if not clean_connector:
            raise ValueError("source_connector_id is required")
        clean_title = str(title or "").strip()
        if not clean_title:
            raise ValueError("title is required")
        clean_status = self._normalize_activity_meeting_candidate_status(status)
        record_id = int(source_activity_record_id) if source_activity_record_id is not None else None
        clean_id = str(candidate_id or f"amc-{uuid.uuid4().hex[:12]}").strip()
        clean_meeting_url = str(meeting_url).strip() if meeting_url not in (None, "") else None
        dedupe_key = self._activity_meeting_candidate_dedupe_key(
            source_connector_id=clean_connector,
            source_activity_record_id=record_id,
            meeting_url=clean_meeting_url,
            title=clean_title,
        )
        now_iso = datetime.now().isoformat()
        starts_iso = self._activity_time_to_iso(starts_at)
        ends_iso = self._activity_time_to_iso(ends_at)
        clean_confidence = max(0.0, min(1.0, float(confidence)))
        with self._connection() as conn:
            if record_id is not None:
                exists = conn.execute(
                    "SELECT 1 FROM activity_records WHERE id = ?",
                    (record_id,),
                ).fetchone()
                if exists is None:
                    raise ValueError(f"activity record not found: {record_id}")
            existing = conn.execute(
                """
                SELECT *
                FROM activity_meeting_candidates
                WHERE dedupe_key = ?
                  AND dedupe_key != ''
                """,
                (dedupe_key,),
            ).fetchone()
            if existing is not None:
                next_status = clean_status if clean_status != "candidate" else str(existing["status"])
                conn.execute(
                    """
                    UPDATE activity_meeting_candidates
                    SET source_activity_record_id = COALESCE(?, source_activity_record_id),
                        title = ?,
                        starts_at = COALESCE(?, starts_at),
                        ends_at = COALESCE(?, ends_at),
                        meeting_url = COALESCE(?, meeting_url),
                        confidence = MAX(confidence, ?),
                        status = ?,
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        record_id,
                        clean_title,
                        starts_iso,
                        ends_iso,
                        clean_meeting_url,
                        clean_confidence,
                        next_status,
                        now_iso,
                        str(existing["id"]),
                    ),
                )
                row = conn.execute(
                    "SELECT * FROM activity_meeting_candidates WHERE id = ?",
                    (str(existing["id"]),),
                ).fetchone()
                return self._row_to_activity_meeting_candidate(row)
            conn.execute(
                """
                INSERT INTO activity_meeting_candidates (
                    id, source_connector_id, source_activity_record_id, dedupe_key, title,
                    starts_at, ends_at, meeting_url, confidence, status,
                    created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    clean_id,
                    clean_connector,
                    record_id,
                    dedupe_key,
                    clean_title,
                    starts_iso,
                    ends_iso,
                    clean_meeting_url,
                    clean_confidence,
                    clean_status,
                    now_iso,
                    now_iso,
                ),
            )
            row = conn.execute(
                "SELECT * FROM activity_meeting_candidates WHERE id = ?",
                (clean_id,),
            ).fetchone()
            return self._row_to_activity_meeting_candidate(row)

    def list_activity_meeting_candidates(
        self,
        *,
        source_connector_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> list[ActivityMeetingCandidate]:
        """List local meeting candidates."""
        where: list[str] = []
        params: list[Any] = []
        if source_connector_id:
            where.append("source_connector_id = ?")
            params.append(str(source_connector_id).strip())
        if status:
            where.append("status = ?")
            params.append(self._normalize_activity_meeting_candidate_status(status))
        query = "SELECT * FROM activity_meeting_candidates"
        if where:
            query += " WHERE " + " AND ".join(where)
        query += " ORDER BY starts_at ASC, created_at DESC, id DESC LIMIT ?"
        params.append(max(1, min(int(limit), 5000)))
        with self._connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_activity_meeting_candidate(row) for row in rows]

    def update_activity_meeting_candidate_status(
        self,
        candidate_id: str,
        status: str,
    ) -> Optional[ActivityMeetingCandidate]:
        """Update one meeting candidate status."""
        clean_id = str(candidate_id or "").strip()
        if not clean_id:
            return None
        clean_status = self._normalize_activity_meeting_candidate_status(status)
        with self._connection() as conn:
            cursor = conn.execute(
                """
                UPDATE activity_meeting_candidates
                SET status = ?, updated_at = ?
                WHERE id = ?
                """,
                (clean_status, datetime.now().isoformat(), clean_id),
            )
            if not cursor.rowcount:
                return None
            row = conn.execute(
                "SELECT * FROM activity_meeting_candidates WHERE id = ?",
                (clean_id,),
            ).fetchone()
            return self._row_to_activity_meeting_candidate(row)

    def delete_activity_meeting_candidates(
        self,
        *,
        source_connector_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> int:
        """Delete local meeting candidates by connector or status."""
        where: list[str] = []
        params: list[Any] = []
        if source_connector_id:
            where.append("source_connector_id = ?")
            params.append(str(source_connector_id).strip())
        if status:
            where.append("status = ?")
            params.append(self._normalize_activity_meeting_candidate_status(status))
        query = "DELETE FROM activity_meeting_candidates"
        if where:
            query += " WHERE " + " AND ".join(where)
        with self._connection() as conn:
            cursor = conn.execute(query, params)
            return int(cursor.rowcount if cursor.rowcount is not None else 0)

    def _normalize_activity_meeting_candidate_status(self, status: object) -> str:
        clean_status = str(status or "").strip().lower()
        if clean_status not in VALID_ACTIVITY_MEETING_CANDIDATE_STATUSES:
            raise ValueError(
                "activity meeting candidate status must be one of "
                f"{sorted(VALID_ACTIVITY_MEETING_CANDIDATE_STATUSES)}"
            )
        return clean_status

    def _activity_meeting_candidate_dedupe_key(
        self,
        *,
        source_connector_id: str,
        source_activity_record_id: Optional[int],
        meeting_url: Optional[str],
        title: str,
    ) -> str:
        clean_connector = str(source_connector_id or "").strip().lower()
        if source_activity_record_id is not None:
            return f"{clean_connector}:record:{int(source_activity_record_id)}"
        if meeting_url:
            try:
                clean_url = self._normalize_activity_url(meeting_url)
            except ValueError:
                clean_url = str(meeting_url).strip().lower()
            return f"{clean_connector}:url:{clean_url}"
        return f"{clean_connector}:title:{str(title or '').strip().lower()}"

    def _row_to_activity_record(self, row: sqlite3.Row) -> ActivityRecord:
        return ActivityRecord(
            id=int(row["id"]),
            source_browser=str(row["source_browser"]),
            source_profile=str(row["source_profile"] or ""),
            source_path_hash=str(row["source_path_hash"] or ""),
            url=str(row["url"]),
            normalized_url=str(row["normalized_url"]),
            title=row["title"],
            domain=str(row["domain"] or ""),
            visit_count=int(row["visit_count"] or 0),
            first_seen_at=datetime.fromisoformat(row["first_seen_at"]) if row["first_seen_at"] else None,
            last_seen_at=datetime.fromisoformat(row["last_seen_at"]) if row["last_seen_at"] else None,
            last_visit_raw=row["last_visit_raw"],
            entity_type=row["entity_type"],
            entity_id=row["entity_id"],
            project_id=row["project_id"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def _row_to_activity_meeting_candidate(
        self,
        row: sqlite3.Row,
    ) -> ActivityMeetingCandidate:
        return ActivityMeetingCandidate(
            id=str(row["id"]),
            source_connector_id=str(row["source_connector_id"]),
            source_activity_record_id=(
                int(row["source_activity_record_id"])
                if row["source_activity_record_id"] is not None
                else None
            ),
            dedupe_key=str(row["dedupe_key"] or ""),
            title=str(row["title"]),
            starts_at=datetime.fromisoformat(row["starts_at"]) if row["starts_at"] else None,
            ends_at=datetime.fromisoformat(row["ends_at"]) if row["ends_at"] else None,
            meeting_url=row["meeting_url"],
            confidence=float(row["confidence"] or 0),
            status=str(row["status"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def _row_to_activity_enrichment_connector(
        self,
        row: sqlite3.Row,
    ) -> ActivityEnrichmentConnectorState:
        return ActivityEnrichmentConnectorState(
            id=str(row["id"]),
            enabled=bool(row["enabled"]),
            settings=self._json_loads_dict(row["settings_json"]),
            last_run_at=datetime.fromisoformat(row["last_run_at"]) if row["last_run_at"] else None,
            last_error=row["last_error"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def _row_to_activity_annotation(self, row: sqlite3.Row) -> ActivityAnnotation:
        return ActivityAnnotation(
            id=str(row["id"]),
            activity_record_id=int(row["activity_record_id"]) if row["activity_record_id"] is not None else None,
            source_connector_id=str(row["source_connector_id"]),
            annotation_type=str(row["annotation_type"]),
            title=str(row["title"] or ""),
            value=self._json_loads_dict(row["value_json"]),
            confidence=float(row["confidence"] or 0),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def _row_to_activity_project_rule(self, row: sqlite3.Row) -> ActivityProjectRule:
        return ActivityProjectRule(
            id=str(row["id"]),
            project_id=str(row["project_id"]),
            project_name=row["project_name"],
            name=str(row["name"] or ""),
            enabled=bool(row["enabled"]),
            priority=int(row["priority"] or 0),
            match_type=str(row["match_type"]),
            pattern=str(row["pattern"]),
            entity_type=row["entity_type"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def _row_to_activity_checkpoint(self, row: sqlite3.Row) -> ActivityImportCheckpoint:
        return ActivityImportCheckpoint(
            source_browser=str(row["source_browser"]),
            source_profile=str(row["source_profile"] or ""),
            source_path_hash=str(row["source_path_hash"] or ""),
            last_visit_raw=row["last_visit_raw"],
            last_imported_at=(
                datetime.fromisoformat(row["last_imported_at"])
                if row["last_imported_at"]
                else None
            ),
            last_error=row["last_error"],
            enabled=bool(row["enabled"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def log_project_detection(
        self,
        *,
        meeting_id: str,
        project_id: str,
        window_id: str,
        score: float,
        keyword_hits: Optional[list[str]] = None,
        member_hits: Optional[list[str]] = None,
    ) -> None:
        """Record one project detection score for an intent window."""
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO project_detection_log
                    (meeting_id, project_id, window_id, score, keyword_hits_json, member_hits_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    str(meeting_id).strip(),
                    str(project_id).strip(),
                    str(window_id).strip(),
                    max(0.0, float(score)),
                    self._json_dumps(keyword_hits or [], fallback="[]"),
                    self._json_dumps(member_hits or [], fallback="[]"),
                ),
            )

    def get_project_detection_log(
        self, project_id: str, *, limit: int = 200
    ) -> list[dict[str, Any]]:
        """Get recent detection audit entries for a project."""
        with self._connection() as conn:
            rows = conn.execute(
                """
                SELECT pdl.*, m.title as meeting_title
                FROM project_detection_log pdl
                LEFT JOIN meetings m ON m.id = pdl.meeting_id
                WHERE pdl.project_id = ?
                ORDER BY pdl.created_at DESC
                LIMIT ?
                """,
                (str(project_id).strip(), max(1, int(limit))),
            ).fetchall()
            return [
                {
                    "meeting_id": row["meeting_id"],
                    "meeting_title": row["meeting_title"],
                    "window_id": row["window_id"],
                    "score": row["score"],
                    "keyword_hits": self._json_loads_list(row["keyword_hits_json"]),
                    "member_hits": self._json_loads_list(row["member_hits_json"]),
                    "created_at": row["created_at"],
                }
                for row in rows
            ]

    def _row_to_project(self, row: sqlite3.Row) -> ProjectSummary:
        """Convert a DB row to a ProjectSummary."""
        return ProjectSummary(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            keywords=self._json_loads_list(row["keywords_json"]),
            team_members=self._json_loads_list(row["team_members_json"]),
            context=self._json_loads_dict(row["context_json"]),
            detection_threshold=float(row["detection_threshold"]),
            is_archived=bool(row["is_archived"]),
            meeting_count=int(row["meeting_count"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )


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
