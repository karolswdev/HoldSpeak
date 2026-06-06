"""SQLite database persistence for HoldSpeak meetings."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, Iterator

from ..logging_config import get_logger
from .meetings import MeetingRepository
from .intel import IntelRepository
from .plugins import PluginArtifactRepository
from .projects import ProjectRepository
from .activity import ActivityRepository
from .actuators import ActuatorRepository
from .corrections import DictationCorrectionRepository
from .journal import DictationJournalRepository
from .milestones import MilestoneRepository

log = get_logger("db")

# Validation constants live in .models (shared with the repositories); re-exported
# here via `from .models import *` above.

# Default database location
DEFAULT_DB_PATH = Path.home() / ".local" / "share" / "holdspeak" / "holdspeak.db"
SCHEMA_VERSION = 1

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

-- Phase 37 (HS-37-02): actuator proposals — a proposed external side effect
-- awaiting human approval. Lifecycle: proposed -> approved -> executed |
-- rejected | failed (a failed proposal may be re-approved for retry).
-- `payload_json` is the parity source-of-truth the guarded executor checks
-- before acting (HS-37-04); every transition is recorded in
-- actuator_proposal_audit so "no silent egress" is provable after the fact.
CREATE TABLE IF NOT EXISTS actuator_proposals (
    id TEXT PRIMARY KEY,
    meeting_id TEXT NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    window_id TEXT NOT NULL DEFAULT '',
    plugin_id TEXT NOT NULL,
    plugin_version TEXT NOT NULL DEFAULT 'unknown',
    idempotency_key TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL DEFAULT 'proposed',
    target TEXT NOT NULL,
    action TEXT NOT NULL,
    preview TEXT NOT NULL,
    payload_json TEXT NOT NULL DEFAULT '{}',
    reversible INTEGER NOT NULL DEFAULT 0,
    required_capabilities_json TEXT NOT NULL DEFAULT '[]',
    decided_by TEXT,
    result_json TEXT,
    error TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    decided_at TEXT,
    executed_at TEXT,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Per-transition audit trail for actuator proposals.
CREATE TABLE IF NOT EXISTS actuator_proposal_audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    proposal_id TEXT NOT NULL REFERENCES actuator_proposals(id) ON DELETE CASCADE,
    actor TEXT NOT NULL DEFAULT 'system',
    from_status TEXT,
    to_status TEXT NOT NULL,
    detail TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_actuator_proposals_meeting ON actuator_proposals(meeting_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_actuator_proposals_status ON actuator_proposals(status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_actuator_proposal_audit_proposal ON actuator_proposal_audit(proposal_id, created_at);

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
    started_meeting_id TEXT,
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

-- HS-13-05: per-pack run history. Replaces the single-row
-- last_run_at / last_error on activity_enrichment_connectors as
-- the source of truth for connector behaviour over time.
CREATE TABLE IF NOT EXISTS connector_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    connector_id TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT NOT NULL,
    succeeded INTEGER NOT NULL DEFAULT 0,
    error TEXT,
    output_bytes INTEGER NOT NULL DEFAULT 0,
    annotation_count INTEGER NOT NULL DEFAULT 0,
    candidate_count INTEGER NOT NULL DEFAULT 0,
    command_count INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_connector_runs_connector_started
ON connector_runs(connector_id, started_at DESC);

-- Phase 40 (HS-40-02): persistent dictation correction memory. The durable
-- home for the in-process `CorrectionStore` ring — corrections written through
-- on record and the recent set loaded back on a fresh store, so routing
-- learning survives a restart. Gist-only + secret-rejected before insert.
CREATE TABLE IF NOT EXISTS dictation_corrections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT NOT NULL,
    gist TEXT NOT NULL,
    value TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_dictation_corrections_recent
ON dictation_corrections(created_at DESC, id DESC);

-- Phase 42 (HS-42-01): durable one-time milestones for first-run state. A key
-- is recorded once (e.g. `first_dictation_success`); `first_run` is true while
-- the first-success key is absent, so a healthy returning user is never sent
-- back to setup-mode. Opaque keys only — no payload, no secrets.
CREATE TABLE IF NOT EXISTS milestones (
    key TEXT PRIMARY KEY,
    achieved_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Phase 45 (HS-45-01): the dictation journal. A durable, local-only, private
-- record of each dictation/dry-run pipeline run — what was said, how it routed,
-- what got typed, and per-stage latency — so the daily-driver dictation loop
-- becomes reviewable, correctable after the fact, and replayable. The transcript
-- + final text are secret-filtered before insert and the table is retention-
-- capped (prune-on-insert to a last-N bound). `corrected` / `correction_id` are
-- set by HS-45-03 when a user fixes an entry in the moment.
CREATE TABLE IF NOT EXISTS dictation_journal (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    source TEXT NOT NULL,
    project_root TEXT,
    transcript TEXT NOT NULL DEFAULT '',
    intent TEXT,
    block_id TEXT,
    target_profile TEXT,
    final_text TEXT NOT NULL DEFAULT '',
    stage_ms TEXT NOT NULL DEFAULT '{}',
    total_ms REAL NOT NULL DEFAULT 0,
    rewrite_pass_ms TEXT NOT NULL DEFAULT '[]',
    confidence REAL,
    warnings TEXT NOT NULL DEFAULT '[]',
    corrected INTEGER NOT NULL DEFAULT 0,
    correction_id INTEGER
);

CREATE INDEX IF NOT EXISTS idx_dictation_journal_recent
ON dictation_journal(created_at DESC, id DESC);
"""



class Database:
    """SQLite database manager for meeting persistence."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DEFAULT_DB_PATH
        self._ensure_schema()
        self.meetings = MeetingRepository(self._connection, self)
        self.intel = IntelRepository(self._connection, self)
        self.plugins = PluginArtifactRepository(self._connection, self)
        self.projects = ProjectRepository(self._connection, self)
        self.activity = ActivityRepository(self._connection, self)
        self.actuators = ActuatorRepository(self._connection, self)
        self.dictation_corrections = DictationCorrectionRepository(self._connection, self)
        self.dictation_journal = DictationJournalRepository(self._connection, self)
        self.milestones = MilestoneRepository(self._connection, self)

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
                self._apply_schema(conn)

    def _apply_schema(self, conn: sqlite3.Connection) -> None:
        """Create the database schema.

        Phase 31 (HS-31-04) squashed the former 18-version migration ladder to a
        single canonical schema: SCHEMA_SQL builds the full current schema in one
        shot. There is no in-place upgrade path (greenfield) — SCHEMA_VERSION starts
        fresh at 1; future schema changes add migration steps from here.
        """
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
            (SCHEMA_VERSION,),
        )
        log.info(f"Database schema created at version {SCHEMA_VERSION}")


    # === MIR Persistence ===



















    # === Query Methods ===


    # ── Project knowledge bases ──────────────────────────────────────────













    # ── Local activity intelligence ledger ───────────────────────────────
























































# Singleton instance
_db: Optional[Database] = None


def get_database(db_path: Optional[Path] = None) -> Database:
    """Get or create the database singleton."""
    global _db
    if _db is None:
        _db = Database(db_path)
    return _db


def reset_database() -> None:
    """Reset the database singleton (for testing)."""
    global _db
    _db = None
