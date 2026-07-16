"""SQLite database persistence for HoldSpeak meetings."""

from __future__ import annotations

import shutil
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional, Iterator

from ..logging_config import get_logger
from .meetings import MeetingRepository
from .intel import IntelRepository
from .mesh_relay import MeshRelayRepository
from .steering import SteeringAuditRepository
from .projections import ProjectionRepository
from .plugins import PluginArtifactRepository
from .projects import ProjectRepository
from .activity import ActivityRepository
from .actuators import ActuatorRepository
from .corrections import DictationCorrectionRepository
from .journal import DictationJournalRepository
from .milestones import MilestoneRepository
from .onboarding import OnboardingRepository
from .dictation_delivery import DictationDeliveryRepository
from .cadence import CadenceRepository
from .primitives import (
    RecipeRepository,
    ChainRepository,
    DirectoryMembershipRepository,
    DirectoryRepository,
    KBRepository,
    ModelManifestRepository,
    NoteRepository,
    ProfileRepository,
    WorkflowRepository,
)
from .relationships import KnowledgeMembershipRepository, ProjectRelationshipRepository
from .invocations import CapabilityInvocationRepository
from .delivery_attempts import WorkAttemptRepository

log = get_logger("db")

# Validation constants live in .models (shared with the repositories); re-exported
# here via `from .models import *` above.

# Default database location
DEFAULT_DB_PATH = Path.home() / ".local" / "share" / "holdspeak" / "holdspeak.db"
SCHEMA_VERSION = 23  # v23: durable Work attempts + transition events (HS-94-04)


class SchemaVersionError(RuntimeError):
    """The stored database is newer than this build of HoldSpeak understands.

    Raised instead of touching the data, so an older build can never
    downgrade-rebuild a database written by a newer one.
    """


def read_schema_version(db_path: Path) -> Optional[int]:
    """Return a database's stored schema version without opening it for use.

    A missing file or a missing/empty `schema_version` table reads as None (a
    fresh database). This is a read-only probe: it never creates the file and
    never runs `_ensure_schema`, so `doctor` can report a newer-than-known
    database honestly instead of triggering the refusal.
    """
    if not db_path.exists():
        return None
    conn = sqlite3.connect(str(db_path))
    try:
        try:
            row = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
        except sqlite3.DatabaseError:
            # No schema_version table (OperationalError) or the file is not a
            # SQLite database at all (DatabaseError). Either way: no version.
            return None
        if not row or row[0] is None:
            return None
        return int(row[0])
    finally:
        conn.close()


def _timestamped_backup_path(db_path: Path) -> Path:
    """A non-clobbering, timestamped backup path next to the database."""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = db_path.with_name(f"{db_path.name}.{timestamp}.bak")
    counter = 1
    while backup_path.exists():
        backup_path = db_path.with_name(f"{db_path.name}.{timestamp}-{counter}.bak")
        counter += 1
    return backup_path


def backup_database(db_path: Path) -> Path:
    """Snapshot the SQLite database to a timestamped sibling and return it.

    Uses SQLite's online backup API (`Connection.backup`) so the copy is a
    consistent snapshot even if something else holds a connection. This is the
    safety net invoked before any destructive schema action, so an upgrade never
    changes a user's data without leaving a recoverable copy first, and it is
    what the `holdspeak backup` command runs on demand. The backup lands next to
    the database as `<name>.<timestamp>.bak`; a counter is appended if that name
    is already taken.
    """
    backup_path = _timestamped_backup_path(db_path)
    source = sqlite3.connect(str(db_path))
    try:
        dest = sqlite3.connect(str(backup_path))
        try:
            source.backup(dest)
        finally:
            dest.close()
    finally:
        source.close()
    return backup_path


def restore_database(backup_path: Path, db_path: Path) -> Optional[Path]:
    """Restore `db_path` from `backup_path`, returning the safety backup taken.

    The current database (if any) is itself snapshotted first, so a restore can
    never be the thing that loses data: if you restore the wrong file you can
    still get back to where you were. Returns the path of that safety backup, or
    None when there was no existing database to protect. Raises ValueError if
    `backup_path` is not a readable HoldSpeak database.
    """
    if not backup_path.exists():
        raise ValueError(f"Backup file not found: {backup_path}")

    probe = sqlite3.connect(str(backup_path))
    try:
        try:
            probe.execute("SELECT MAX(version) FROM schema_version").fetchone()
        except sqlite3.DatabaseError as exc:
            raise ValueError(
                f"{backup_path} is not a readable HoldSpeak database backup ({exc})."
            ) from exc
    finally:
        probe.close()

    safety: Optional[Path] = None
    if db_path.exists():
        safety = backup_database(db_path)

    db_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(backup_path, db_path)
    return safety

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
    capture_status TEXT NOT NULL DEFAULT 'finalized',
    capture_failure TEXT,
    capture_checkpoint_at TEXT,
    capture_checkpoint_seconds REAL NOT NULL DEFAULT 0,
    provenance TEXT NOT NULL DEFAULT 'desktop',
    sync_modified_at TEXT NOT NULL DEFAULT (datetime('now')),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Tags for meetings (many-to-many)
CREATE TABLE IF NOT EXISTS meeting_tags (
    meeting_id TEXT NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    tag TEXT NOT NULL,
    PRIMARY KEY (meeting_id, tag)
);

-- Equal-timestamp divergent Meeting edits are never silently discarded. The
-- deterministic LWW winner remains canonical while the losing value stays
-- recoverable here until an owner resolves it (HS-92-04).
CREATE TABLE IF NOT EXISTS meeting_sync_conflicts (
    id TEXT PRIMARY KEY,
    meeting_id TEXT NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    local_json TEXT NOT NULL,
    incoming_json TEXT NOT NULL,
    winner TEXT NOT NULL DEFAULT 'local',
    detected_at TEXT NOT NULL DEFAULT (datetime('now')),
    resolved_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_meeting_sync_conflicts_open
ON meeting_sync_conflicts(meeting_id, resolved_at, detected_at DESC);

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
    -- v6 (Phase 74): an artifact is owner-typed like a proposal (v5).
    -- origin='meeting' rows carry a real meeting_id; origin='run' rows (a
    -- persona/chain/workflow run's output) carry NULL — their anchor is the
    -- capability lineage in artifact_sources.
    meeting_id TEXT REFERENCES meetings(id) ON DELETE CASCADE,
    origin TEXT NOT NULL DEFAULT 'meeting' CHECK (origin IN ('meeting', 'run')),
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
    -- v5 (Phase 72): a proposal is owner-typed. origin='meeting' rows carry a
    -- real meeting_id; origin='desk' rows (the iPad desk relay) carry NULL —
    -- the old hidden 'companion' sentinel meeting is gone.
    meeting_id TEXT REFERENCES meetings(id) ON DELETE CASCADE,
    origin TEXT NOT NULL DEFAULT 'meeting' CHECK (origin IN ('meeting', 'desk')),
    window_id TEXT NOT NULL DEFAULT '',
    plugin_id TEXT NOT NULL,
    plugin_version TEXT NOT NULL DEFAULT 'unknown',
    idempotency_key TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL DEFAULT 'proposed',
    review_decision TEXT NOT NULL DEFAULT 'unreviewed'
        CHECK (review_decision IN ('unreviewed','accepted','dismissed')),
    authorization_state TEXT NOT NULL DEFAULT 'proposed'
        CHECK (authorization_state IN ('not_requested','proposed','approved','rejected','expired','revoked')),
    execution_state TEXT NOT NULL DEFAULT 'not_started'
        CHECK (execution_state IN ('not_started','queued','running','succeeded','failed','cancelled','unavailable')),
    target TEXT NOT NULL,
    action TEXT NOT NULL,
    preview TEXT NOT NULL,
    payload_json TEXT NOT NULL DEFAULT '{}',
    reversible INTEGER NOT NULL DEFAULT 0,
    required_capabilities_json TEXT NOT NULL DEFAULT '[]',
    decided_by TEXT,
    approved_payload_hash TEXT,
    approved_destination TEXT,
    approved_preview_hash TEXT,
    preview_renderer_version TEXT,
    effect_class TEXT,
    policy_version TEXT,
    operation_json TEXT NOT NULL DEFAULT '{}',
    policy_snapshot_json TEXT NOT NULL DEFAULT '{}',
    grant_id TEXT,
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

-- HS-92-08: revocable, bounded authority. A grant never contains a secret or
-- payload; it binds WHO may perform WHICH effect, WHERE, with WHAT data/scope,
-- until WHEN and for HOW MANY uses.
CREATE TABLE IF NOT EXISTS authority_grants (
    id TEXT PRIMARY KEY,
    actor TEXT NOT NULL,
    operation_family TEXT NOT NULL,
    effect_class TEXT NOT NULL,
    destination TEXT NOT NULL,
    data_classes_json TEXT NOT NULL DEFAULT '[]',
    project_scope TEXT,
    resource_scope TEXT,
    issued_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    max_uses INTEGER NOT NULL DEFAULT 1,
    remaining_uses INTEGER NOT NULL DEFAULT 1,
    revoked_at TEXT,
    revoke_reason TEXT,
    binding_hash TEXT NOT NULL,
    control_mode TEXT NOT NULL DEFAULT 'neutral'
        CHECK (control_mode IN ('safe','neutral','yolo'))
);
CREATE INDEX IF NOT EXISTS idx_authority_grants_active
ON authority_grants(actor, operation_family, effect_class, destination, expires_at);

CREATE TABLE IF NOT EXISTS authority_grant_uses (
    id TEXT PRIMARY KEY,
    grant_id TEXT NOT NULL REFERENCES authority_grants(id) ON DELETE CASCADE,
    operation_id TEXT NOT NULL,
    actor TEXT NOT NULL,
    effect_class TEXT NOT NULL,
    destination TEXT NOT NULL,
    outcome TEXT NOT NULL DEFAULT 'consumed',
    used_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_authority_grant_uses_grant
ON authority_grant_uses(grant_id, used_at DESC);

-- HS-92-09: presentation state only. Receipt/attention content is projected
-- from authoritative source tables and is never copied into a second audit.
CREATE TABLE IF NOT EXISTS desk_projection_state (
    projection_id TEXT PRIMARY KEY,
    attention_state TEXT NOT NULL DEFAULT 'unseen'
        CHECK (attention_state IN ('unseen','acknowledged')),
    dismissed_at TEXT,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_desk_projection_state_attention
ON desk_projection_state(attention_state, dismissed_at, updated_at DESC);

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

-- Phase 53: persisted dismissals for activity pre-briefing nudges.
-- A nudge_key is deterministic (e.g. "window:<since_iso>", "record:<id>") so a
-- dismissal survives recomputation across reloads.
CREATE TABLE IF NOT EXISTS activity_nudge_dismissals (
    nudge_key TEXT PRIMARY KEY,
    dismissed_at TEXT NOT NULL DEFAULT (datetime('now'))
);

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

-- Phase 92 (HS-92-03): disposition is independent of first success, so
-- Continue later never creates a redirect loop. First-value receipts contain
-- mechanics only; there is deliberately no phrase/content column.
CREATE TABLE IF NOT EXISTS onboarding_state (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    disposition TEXT NOT NULL CHECK (disposition IN ('completed', 'dismissed', 'needs_help')),
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS first_value_attempts (
    id TEXT PRIMARY KEY,
    started_at TEXT NOT NULL,
    succeeded_at TEXT,
    steps INTEGER NOT NULL DEFAULT 0,
    decisions INTEGER NOT NULL DEFAULT 0,
    destination TEXT NOT NULL CHECK (destination IN ('this_machine', 'paired_desktop')),
    failure_category TEXT,
    finished_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_first_value_attempts_started
ON first_value_attempts(started_at DESC);

-- Phase 93 (HS-93-05): first-value mechanics come from observed, bounded
-- interaction events. No payload/content column exists by construction.
CREATE TABLE IF NOT EXISTS first_value_events (
    event_id TEXT PRIMARY KEY,
    attempt_id TEXT NOT NULL REFERENCES first_value_attempts(id) ON DELETE CASCADE,
    kind TEXT NOT NULL,
    occurred_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_first_value_events_attempt
ON first_value_events(attempt_id, occurred_at);

-- Phase 93 (HS-93-05): a companion supplies one durable delivery identity.
-- The hub claims it before touching the delivery hook and caches the terminal
-- response, so a reconnect can read the Receipt without typing a second time.
CREATE TABLE IF NOT EXISTS remote_dictation_deliveries (
    delivery_id TEXT PRIMARY KEY,
    request_hash TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'succeeded', 'failed')),
    response_status INTEGER,
    response_json TEXT,
    error TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_remote_dictation_deliveries_updated
ON remote_dictation_deliveries(updated_at DESC);

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

-- ── Primitive Framework: the desk's synced first-class primitives ──────────
-- Note / KB / Agent (persona) / Chain / Workflow. Authorable on any surface
-- (desktop / iPad / web), the desktop is the canonical store. Each carries a
-- `last_modified` (ISO-8601 UTC, last-write-wins) and a `deleted` tombstone so
-- it syncs exactly like meetings/artifacts (see web/routes/sync.py).

-- Note (content/synced): freeform markdown.
CREATE TABLE IF NOT EXISTS notes (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL DEFAULT '',
    body_markdown TEXT NOT NULL DEFAULT '',
    tags_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    last_modified TEXT NOT NULL DEFAULT (datetime('now')),
    deleted INTEGER NOT NULL DEFAULT 0
);

-- KB (organization/synced): the desk's knowledge container — a named bag of
-- member primitive ids. DISTINCT from project.yaml kb-map / .hs context files.
CREATE TABLE IF NOT EXISTS kbs (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL DEFAULT '',
    member_ids_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    last_modified TEXT NOT NULL DEFAULT (datetime('now')),
    deleted INTEGER NOT NULL DEFAULT 0
);

-- Recipe (capability/synced): the canonical, runnable user-authored persona.
-- DISTINCT from agent_context.AgentSession (a live claude/codex coding session,
-- which keeps the word "agent").
CREATE TABLE IF NOT EXISTS recipes (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL DEFAULT '',
    avatar TEXT NOT NULL DEFAULT '',
    role TEXT NOT NULL DEFAULT '',
    system_prompt TEXT NOT NULL DEFAULT '',
    user_template TEXT NOT NULL DEFAULT '',
    tools_json TEXT NOT NULL DEFAULT '[]',
    kb_id TEXT,
    profile_id TEXT,
    -- v7 (Phase 77): the iPad-authored pinned context persists on the hub
    -- (ends the loss HS-72-01 documented in the Swift tolerant decode).
    manual_context TEXT NOT NULL DEFAULT '',
    use_zone_context INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    last_modified TEXT NOT NULL DEFAULT (datetime('now')),
    deleted INTEGER NOT NULL DEFAULT 0
);

-- Chain (capability/synced): an ordered run of recipes.
CREATE TABLE IF NOT EXISTS chains (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL DEFAULT '',
    steps_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    last_modified TEXT NOT NULL DEFAULT (datetime('now')),
    deleted INTEGER NOT NULL DEFAULT 0
);

-- Workflow (capability/synced): a saved Workbench workflow (prompt | graph_json).
CREATE TABLE IF NOT EXISTS workflows (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL DEFAULT '',
    prompt TEXT NOT NULL DEFAULT '',
    graph_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    last_modified TEXT NOT NULL DEFAULT (datetime('now')),
    deleted INTEGER NOT NULL DEFAULT 0
);

-- Phase 92 (HS-92-06): one durable envelope for every Persona, Sequence, and
-- Workflow run. This augments; it does not replace optimized domain job tables.
CREATE TABLE IF NOT EXISTS capability_invocations (
    id TEXT PRIMARY KEY,
    correlation_id TEXT NOT NULL UNIQUE,
    definition_ref TEXT NOT NULL,
    initiator TEXT NOT NULL DEFAULT 'owner',
    grounding_refs_json TEXT NOT NULL DEFAULT '[]',
    requested_placement TEXT NOT NULL DEFAULT 'this_machine',
    input_snapshot_json TEXT NOT NULL DEFAULT '{}',
    state TEXT NOT NULL DEFAULT 'running'
        CHECK (state IN ('running','succeeded','failed','cancelled','unavailable','empty')),
    result_ref TEXT,
    error TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    completed_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_capability_invocations_definition
ON capability_invocations(definition_ref, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_capability_invocations_state
ON capability_invocations(state, created_at DESC);

CREATE TABLE IF NOT EXISTS capability_attempts (
    id TEXT PRIMARY KEY,
    invocation_id TEXT NOT NULL REFERENCES capability_invocations(id) ON DELETE CASCADE,
    attempt_index INTEGER NOT NULL,
    destination TEXT NOT NULL,
    actual_placement_json TEXT NOT NULL DEFAULT '{}',
    provider TEXT,
    state TEXT NOT NULL DEFAULT 'running'
        CHECK (state IN ('running','succeeded','failed','cancelled','empty')),
    error TEXT,
    result_ref TEXT,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    UNIQUE(invocation_id, attempt_index)
);
CREATE INDEX IF NOT EXISTS idx_capability_attempts_invocation
ON capability_attempts(invocation_id, attempt_index);

-- Runtime profile (capability/synced, Phase 24): a named "where intelligence runs"
-- target. SHAPE ONLY — the API key NEVER lives here and never syncs; the hub joins
-- its own secret at request time (mirrors the connector credential rule).
CREATE TABLE IF NOT EXISTS profiles (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL DEFAULT '',
    kind TEXT NOT NULL DEFAULT 'onDevice',
    model_file TEXT NOT NULL DEFAULT '',
    base_url TEXT NOT NULL DEFAULT '',
    model TEXT NOT NULL DEFAULT '',
    node TEXT NOT NULL DEFAULT '', -- meshNode kind (HS-85-02): the executing mesh node
    context_limit INTEGER NOT NULL DEFAULT 16384,
    requires_key INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    last_modified TEXT NOT NULL DEFAULT (datetime('now')),
    deleted INTEGER NOT NULL DEFAULT 0
);

-- Model manifest (capability/synced, HSM-16-08): "this node has this model" —
-- availability only. The model BINARY never syncs; by design this table has no
-- path/url/bytes column, so nothing binary-shaped can even be stored to leak.
CREATE TABLE IF NOT EXISTS model_manifests (
    id TEXT PRIMARY KEY,
    node TEXT NOT NULL DEFAULT '',
    name TEXT NOT NULL DEFAULT '',
    capabilities_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    last_modified TEXT NOT NULL DEFAULT (datetime('now')),
    deleted INTEGER NOT NULL DEFAULT 0
);

-- Mesh relay queue (HS-85-01): HUB-LOCAL run rows — a run addressed to one
-- node, claimed by that node's worker, executed on ITS OWN provider, result
-- posted back. Never a synced kind: prompts move only hub <-> the executing
-- node (the deferred-intel trust posture). Deadlines enforced lazily on read.
CREATE TABLE IF NOT EXISTS mesh_relay_jobs (
    id TEXT PRIMARY KEY,
    node TEXT NOT NULL,
    task_kind TEXT NOT NULL DEFAULT 'llm',
    system_prompt TEXT NOT NULL DEFAULT '',
    user_prompt TEXT NOT NULL DEFAULT '',
    temperature REAL,
    max_tokens INTEGER,
    model_hint TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'queued', -- queued | running | completed | failed
    result TEXT,
    error TEXT,
    deadline_at TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    claimed_at TEXT,
    completed_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_mesh_relay_jobs_node_status
    ON mesh_relay_jobs(node, status);

-- Mesh worker liveness (HS-85-01): last claim-poll per node. Liveness is
-- born from the worker's own polling; the mesh has no other heartbeat.
CREATE TABLE IF NOT EXISTS mesh_workers (
    node TEXT PRIMARY KEY,
    last_seen TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Directory (organization/synced): the canonical organization container; the
-- iPad renders it spatially as a "zone". Only identity + nesting sync here
-- (`id, name, parent_id`); the zone's geometry/paint is per-device layout and
-- stays on the surface, never canonical. `parent_id` chains = nested directories.
CREATE TABLE IF NOT EXISTS directories (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL DEFAULT '',
    parent_id TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    last_modified TEXT NOT NULL DEFAULT (datetime('now')),
    deleted INTEGER NOT NULL DEFAULT 0
);

-- Directory membership (organization/synced): the canonical filing map
-- `primitive_id -> directory_id`. SUPERSEDES the legacy single-valued `filed`
-- maps (web `hs.desk.filed`, the iPad's `filed` dict): one filing per primitive,
-- so the PRIMARY KEY is primitive_id. Membership is organization (it MUST sync),
-- distinct from a primitive's free-place geometry (layout, never canonical).
CREATE TABLE IF NOT EXISTS directory_memberships (
    primitive_id TEXT PRIMARY KEY,
    directory_id TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    last_modified TEXT NOT NULL DEFAULT (datetime('now')),
    deleted INTEGER NOT NULL DEFAULT 0
);

-- Independent, qualified relationship axes (HS-92-05). These do not mutate
-- one another: a resource has one Zone and any number of Knowledge/Projects.
CREATE TABLE IF NOT EXISTS knowledge_memberships (
    knowledge_id TEXT NOT NULL REFERENCES kbs(id) ON DELETE CASCADE,
    resource_ref TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    last_modified TEXT NOT NULL DEFAULT (datetime('now')),
    deleted INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (knowledge_id, resource_ref)
);
CREATE TABLE IF NOT EXISTS project_resources (
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    resource_ref TEXT NOT NULL,
    relationship TEXT NOT NULL DEFAULT 'member',
    source TEXT NOT NULL DEFAULT 'manual',
    confidence REAL NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    last_modified TEXT NOT NULL DEFAULT (datetime('now')),
    deleted INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (project_id, resource_ref)
);

CREATE INDEX IF NOT EXISTS idx_notes_modified ON notes(last_modified DESC);
CREATE INDEX IF NOT EXISTS idx_kbs_modified ON kbs(last_modified DESC);
CREATE INDEX IF NOT EXISTS idx_recipes_modified ON recipes(last_modified DESC);
CREATE INDEX IF NOT EXISTS idx_chains_modified ON chains(last_modified DESC);
CREATE INDEX IF NOT EXISTS idx_workflows_modified ON workflows(last_modified DESC);
CREATE INDEX IF NOT EXISTS idx_directories_modified ON directories(last_modified DESC);
CREATE INDEX IF NOT EXISTS idx_directory_memberships_dir ON directory_memberships(directory_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_memberships_resource ON knowledge_memberships(resource_ref, deleted);
CREATE INDEX IF NOT EXISTS idx_knowledge_memberships_modified ON knowledge_memberships(last_modified);
CREATE INDEX IF NOT EXISTS idx_project_resources_resource ON project_resources(resource_ref, deleted);
CREATE INDEX IF NOT EXISTS idx_project_resources_modified ON project_resources(last_modified);

-- ── Cadence Engine (CAD-1-01) ──────────────────────────────────────────────
-- Open Loops are source-PROJECTED entities: the collector idempotently upserts
-- one row per (source_type, source_id); the user's lifecycle decisions
-- (snoozed/killed/nudge_count) live only here and survive re-collection (a
-- killed loop stays killed). The engine is off by default and writes ONLY these
-- cadence_* tables — it never performs an external side effect (that goes through
-- the existing actuator propose->approve->execute path in later phases).
CREATE TABLE IF NOT EXISTS cadence_loops (
    id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,
    source_id TEXT NOT NULL,
    project TEXT,
    title TEXT NOT NULL,
    summary TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'open',     -- open, snoozed, closed, killed, delegated
    priority TEXT NOT NULL DEFAULT 'normal',  -- low, normal, high, urgent
    needs_review INTEGER NOT NULL DEFAULT 0,  -- low-confidence: quiet, never a push
    owner TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    due_at TEXT,
    snoozed_until TEXT,
    stale_score REAL NOT NULL DEFAULT 0,
    last_nudged_at TEXT,
    nudge_count INTEGER NOT NULL DEFAULT 0
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_cadence_loops_source ON cadence_loops(source_type, source_id);
CREATE INDEX IF NOT EXISTS idx_cadence_loops_status ON cadence_loops(status, snoozed_until);

CREATE TABLE IF NOT EXISTS cadence_evidence_refs (
    id TEXT PRIMARY KEY,
    loop_id TEXT NOT NULL REFERENCES cadence_loops(id) ON DELETE CASCADE,
    kind TEXT NOT NULL,
    ref_id TEXT NOT NULL,
    label TEXT NOT NULL DEFAULT '',
    timestamp TEXT,
    deep_link TEXT
);
CREATE INDEX IF NOT EXISTS idx_cadence_evidence_loop ON cadence_evidence_refs(loop_id);

CREATE TABLE IF NOT EXISTS cadence_next_actions (
    id TEXT PRIMARY KEY,
    loop_id TEXT NOT NULL REFERENCES cadence_loops(id) ON DELETE CASCADE,
    kind TEXT NOT NULL,
    title TEXT NOT NULL,
    body_markdown TEXT NOT NULL DEFAULT '',
    confidence REAL NOT NULL DEFAULT 0,
    reversible INTEGER NOT NULL DEFAULT 1,
    proposal_id TEXT,
    generated_by TEXT NOT NULL DEFAULT 'deterministic',
    generated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_cadence_next_actions_loop ON cadence_next_actions(loop_id);

CREATE TABLE IF NOT EXISTS cadence_nudges (
    id TEXT PRIMARY KEY,
    loop_id TEXT NOT NULL REFERENCES cadence_loops(id) ON DELETE CASCADE,
    next_action_id TEXT,
    surface TEXT NOT NULL,
    severity TEXT NOT NULL DEFAULT 'normal',  -- quiet, normal, persistent, escalated
    title TEXT NOT NULL DEFAULT '',
    message_markdown TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'pending',   -- pending, shown, acted, dismissed, expired
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    shown_at TEXT,
    acted_at TEXT,
    expires_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_cadence_nudges_loop ON cadence_nudges(loop_id);
CREATE INDEX IF NOT EXISTS idx_cadence_nudges_status ON cadence_nudges(status);

CREATE TABLE IF NOT EXISTS cadence_policies (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    enabled INTEGER NOT NULL DEFAULT 1,
    config_json TEXT NOT NULL DEFAULT '{}',
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Steering audit (HS-87-03): every keystroke toward a pane, remembered.
-- Privacy-respecting receipt: the text's sha256 + first 120 chars, never
-- the full steer. Refusals audit too, with the refusal as the outcome.
CREATE TABLE IF NOT EXISTS steering_audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL DEFAULT (datetime('now')),
    session_key TEXT NOT NULL,
    agent TEXT NOT NULL DEFAULT '',
    pane_id TEXT,
    text_sha256 TEXT NOT NULL,
    text_head TEXT NOT NULL DEFAULT '',
    grounding_json TEXT NOT NULL DEFAULT '[]',
    submit INTEGER NOT NULL DEFAULT 1,
    outcome TEXT NOT NULL,
    detail TEXT,
    operation_json TEXT NOT NULL DEFAULT '{}',
    policy_snapshot_json TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_steering_audit_ts ON steering_audit(ts);
CREATE INDEX IF NOT EXISTS idx_steering_audit_key ON steering_audit(session_key);

-- Work attempts (HS-94-04, PLATFORM-CONTRACT §4.2): one bounded undertaking
-- of one primary Story, bound to node/source/worktree/session/target with
-- explicit association provenance. attempt_id is opaque and never reused.
-- No filesystem path enters this table by construction.
CREATE TABLE IF NOT EXISTS work_attempts (
    attempt_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    project TEXT NOT NULL,
    story_id TEXT NOT NULL,
    worktree_id TEXT NOT NULL,
    node_id TEXT,                 -- NULL = the embedded local node
    session_id TEXT,              -- NULL until an agent session binds
    target_id TEXT,               -- opaque terminal handle, when known
    association_kind TEXT NOT NULL
        CHECK (association_kind IN ('launch','rider_claim','manual','contract','heuristic')),
    claimed_by TEXT,
    claimed_at TEXT,
    exact INTEGER NOT NULL DEFAULT 0,
    state TEXT NOT NULL DEFAULT 'starting'
        CHECK (state IN ('starting','working','waiting','idle','ended','abandoned','unknown')),
    started_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    ended_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_work_attempts_story
ON work_attempts(source_id, project, story_id, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_work_attempts_session
ON work_attempts(session_id, state);
CREATE INDEX IF NOT EXISTS idx_work_attempts_worktree
ON work_attempts(worktree_id, state);
-- One session may pin at most ONE live attempt as exact; the repo-wide
-- heuristic can list it on several cards only as non-exact rows.
CREATE UNIQUE INDEX IF NOT EXISTS idx_work_attempts_exact_session
ON work_attempts(session_id)
WHERE exact = 1 AND session_id IS NOT NULL AND state NOT IN ('ended','abandoned');

-- Replayable attempt lifecycle: every applied transition, timestamped.
-- History is preserved through worktree removal and hub restarts.
CREATE TABLE IF NOT EXISTS work_attempt_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    attempt_id TEXT NOT NULL REFERENCES work_attempts(attempt_id) ON DELETE CASCADE,
    from_state TEXT,
    to_state TEXT NOT NULL,
    reason TEXT NOT NULL DEFAULT '',
    occurred_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_work_attempt_events_attempt
ON work_attempt_events(attempt_id, id);
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
        self.onboarding = OnboardingRepository(self._connection, self)
        self.dictation_deliveries = DictationDeliveryRepository(self._connection, self)
        self.cadence = CadenceRepository(self._connection, self)  # CAD-1-01
        # Primitive Framework: the desk's synced first-class primitives.
        self.notes = NoteRepository(self._connection, self)
        self.kbs = KBRepository(self._connection, self)
        self.recipes = RecipeRepository(self._connection, self)
        self.profiles = ProfileRepository(self._connection, self)
        self.chains = ChainRepository(self._connection, self)
        self.workflows = WorkflowRepository(self._connection, self)
        self.directories = DirectoryRepository(self._connection, self)
        self.directory_memberships = DirectoryMembershipRepository(self._connection, self)
        self.knowledge_memberships = KnowledgeMembershipRepository(self._connection, self)
        self.project_relationships = ProjectRelationshipRepository(self._connection, self)
        self.capability_invocations = CapabilityInvocationRepository(self._connection, self)
        self.model_manifests = ModelManifestRepository(self._connection, self)
        self.mesh_relay = MeshRelayRepository(self._connection, self)
        self.steering = SteeringAuditRepository(self._connection, self)
        self.projections = ProjectionRepository(self._connection, self)
        self.work_attempts = WorkAttemptRepository(self._connection, self)  # HS-94-04

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
        """Bring the database to the current schema version, safely by default.

        The four-way matrix that defines HoldSpeak's forward upgrade contract:

        - **fresh / empty** (no stored version): create the schema at the current
          version, exactly as the original install path did.
        - **stored == SCHEMA_VERSION**: nothing to do.
        - **stored < SCHEMA_VERSION**: an older database. Back it up first, then
          apply the schema. No destructive action ever runs without a backup.
        - **stored > SCHEMA_VERSION**: a database written by a newer HoldSpeak.
          Refuse with a clear error and leave the data untouched; never
          downgrade-rebuild it.
        """
        stored = self._read_schema_version()

        if stored is None or stored == 0:
            with self._connection() as conn:
                self._apply_schema(conn)
            return

        if stored == SCHEMA_VERSION:
            return

        if stored > SCHEMA_VERSION:
            raise SchemaVersionError(
                f"The database at {self.db_path} is schema version {stored}, but "
                f"this build of HoldSpeak only understands version {SCHEMA_VERSION}. "
                f"It was almost certainly written by a newer HoldSpeak. Upgrade "
                f"HoldSpeak (or restore a backup from this version). The database "
                f"was left untouched."
            )

        # stored < SCHEMA_VERSION: an older database. Back up before any change.
        backup = backup_database(self.db_path)
        log.warning(
            f"Database at {self.db_path} is schema version {stored}; this build is "
            f"{SCHEMA_VERSION}. Backed up to {backup} before applying the schema."
        )
        with self._connection() as conn:
            self._migrate_renames(conn, stored)
            self._apply_schema(conn)

    @staticmethod
    def _migrate_renames(conn: sqlite3.Connection, stored: int) -> None:
        """Non-additive migrations the canonical DDL cannot express.

        v8: the persona table `agents` became `recipes` (the owner-ratified
        Recipe rename). A plain re-apply would create an EMPTY `recipes` table
        beside the old data; the rename carries it. Runs after the backup, so
        the pre-rename copy is always recoverable.
        """
        if stored < 8:
            has_old = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='agents'"
            ).fetchone()
            has_new = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='recipes'"
            ).fetchone()
            if has_old and not has_new:
                conn.execute("ALTER TABLE agents RENAME TO recipes")
                conn.execute("DROP INDEX IF EXISTS idx_agents_modified")

        # v11: profiles grew the `node` column (the meshNode kind). A column
        # ADDED to an existing table is exactly what `CREATE TABLE IF NOT
        # EXISTS` cannot express — the live walk caught a v9 database
        # upgrading to a stamped v11 with the column silently missing.
        if stored < 11:
            has_profiles = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='profiles'"
            ).fetchone()
            if has_profiles:
                cols = {r[1] for r in conn.execute("PRAGMA table_info(profiles)").fetchall()}
                if "node" not in cols:
                    conn.execute(
                        "ALTER TABLE profiles ADD COLUMN node TEXT NOT NULL DEFAULT ''"
                    )

    def _read_schema_version(self) -> Optional[int]:
        """Return the stored schema version, or None for a fresh/empty database."""
        return read_schema_version(self.db_path)

    def _apply_schema(self, conn: sqlite3.Connection) -> None:
        """Create the database schema.

        Phase 31 (HS-31-04) squashed the former 18-version migration ladder to a
        single canonical schema: SCHEMA_SQL builds the full current schema in one
        shot. Because every statement in SCHEMA_SQL is `CREATE TABLE/INDEX IF NOT
        EXISTS` (and the seed rows are `INSERT OR IGNORE/REPLACE`), re-applying it
        to an existing database is idempotent and only adds what is missing. So the
        migration FROM an older version IS re-applying SCHEMA_SQL: bumping
        SCHEMA_VERSION routes an older DB through `_ensure_schema`'s backup-then-apply
        path, which lands the new tables. v2 (the Primitive Framework) added
        notes/kbs/recipes/chains/workflows/directories/directory_memberships this way.
        """
        conn.executescript(SCHEMA_SQL)
        # Re-applying SCHEMA_SQL adds missing TABLES idempotently but not new COLUMNS on existing
        # tables. v4 (Phase 24) added profile_id — apply it here, guarded, so an upgraded
        # (backed-up) v3 database gains the column. Fresh DBs already have it from SCHEMA_SQL.
        # (v8 renamed the table agents -> recipes; the rename runs BEFORE this in
        # _migrate_renames, so both fresh and upgraded databases land here as `recipes`.)
        recipe_cols = {row[1] for row in conn.execute("PRAGMA table_info(recipes)").fetchall()}
        if "profile_id" not in recipe_cols:
            conn.execute("ALTER TABLE recipes ADD COLUMN profile_id TEXT")
        # v7 (Phase 77): the pinned-context columns, additive (the v4 recipe).
        if "manual_context" not in recipe_cols:
            conn.execute(
                "ALTER TABLE recipes ADD COLUMN manual_context TEXT NOT NULL DEFAULT ''"
            )
        if "use_zone_context" not in recipe_cols:
            conn.execute(
                "ALTER TABLE recipes ADD COLUMN use_zone_context INTEGER NOT NULL DEFAULT 0"
            )
        # v5 (Phase 72, HS-72-04): actuator proposals become owner-typed. The old
        # table pinned meeting_id NOT NULL, forcing desk sends through a hidden
        # 'companion' sentinel meeting. SQLite cannot drop NOT NULL in place, so an
        # upgraded (backed-up) v<=4 database gets the standard rebuild: copy into
        # the new shape (sentinel rows become origin='desk' with NULL meeting_id),
        # swap, and delete the sentinel meeting. FKs are suspended for the swap
        # (the documented SQLite rebuild recipe) — audit rows keep their proposal
        # ids and the ids are preserved verbatim. Fresh DBs skip this entirely.
        proposal_cols = {
            row[1] for row in conn.execute("PRAGMA table_info(actuator_proposals)").fetchall()
        }
        if proposal_cols and "origin" not in proposal_cols:
            conn.execute("PRAGMA foreign_keys = OFF")
            conn.executescript(
                """
                CREATE TABLE actuator_proposals_v5 (
                    id TEXT PRIMARY KEY,
                    meeting_id TEXT REFERENCES meetings(id) ON DELETE CASCADE,
                    origin TEXT NOT NULL DEFAULT 'meeting' CHECK (origin IN ('meeting', 'desk')),
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
                INSERT INTO actuator_proposals_v5 (
                    id, meeting_id, origin, window_id, plugin_id, plugin_version,
                    idempotency_key, status, target, action, preview, payload_json,
                    reversible, required_capabilities_json, decided_by, result_json,
                    error, created_at, decided_at, executed_at, updated_at)
                SELECT
                    id,
                    CASE WHEN meeting_id = 'companion' THEN NULL ELSE meeting_id END,
                    CASE WHEN meeting_id = 'companion' THEN 'desk' ELSE 'meeting' END,
                    window_id, plugin_id, plugin_version, idempotency_key, status,
                    target, action, preview, payload_json, reversible,
                    required_capabilities_json, decided_by, result_json, error,
                    created_at, decided_at, executed_at, updated_at
                FROM actuator_proposals;
                DROP TABLE actuator_proposals;
                ALTER TABLE actuator_proposals_v5 RENAME TO actuator_proposals;
                CREATE INDEX IF NOT EXISTS idx_actuator_proposals_meeting ON actuator_proposals(meeting_id, created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_actuator_proposals_status ON actuator_proposals(status, created_at DESC);
                DELETE FROM meetings WHERE id = 'companion';
                """
            )
            conn.execute("PRAGMA foreign_keys = ON")
        # v13 (Phase 92, HS-92-02): approval is bound to the complete material
        # effect. Additive nullable columns keep legacy rows readable; an
        # already-approved legacy row is deliberately non-executable until it
        # is re-approved and receives a complete binding.
        proposal_cols = {
            row[1] for row in conn.execute("PRAGMA table_info(actuator_proposals)").fetchall()
        }
        approval_binding_columns = {
            "approved_payload_hash": "TEXT",
            "approved_destination": "TEXT",
            "approved_preview_hash": "TEXT",
            "preview_renderer_version": "TEXT",
            "effect_class": "TEXT",
            "policy_version": "TEXT",
        }
        for column, sql_type in approval_binding_columns.items():
            if column not in proposal_cols:
                conn.execute(
                    f"ALTER TABLE actuator_proposals ADD COLUMN {column} {sql_type}"
                )
        # v15 (Phase 92, HS-92-04): a Meeting exists before the recorder accepts
        # audio and carries honest checkpoint/recovery state through interruption.
        # Legacy rows are completed desktop meetings, hence the non-lossy defaults.
        meeting_cols = {
            row[1] for row in conn.execute("PRAGMA table_info(meetings)").fetchall()
        }
        capture_columns = {
            "capture_status": "TEXT NOT NULL DEFAULT 'finalized'",
            "capture_failure": "TEXT",
            "capture_checkpoint_at": "TEXT",
            "capture_checkpoint_seconds": "REAL NOT NULL DEFAULT 0",
            "provenance": "TEXT NOT NULL DEFAULT 'desktop'",
            "sync_modified_at": "TEXT",
        }
        for column, sql_type in capture_columns.items():
            if column not in meeting_cols:
                conn.execute(f"ALTER TABLE meetings ADD COLUMN {column} {sql_type}")
        # v16: preserve every existing Meeting↔Project relationship in the
        # generic qualified edge store used by both Desks and grounding.
        conn.execute(
            """INSERT OR IGNORE INTO project_resources
               (project_id,resource_ref,relationship,source,confidence,
                created_at,last_modified,deleted)
               SELECT project_id,'meeting:' || meeting_id,'member',source,confidence,
                      detected_at,detected_at,0 FROM meeting_projects"""
        )
        # v6 (Phase 74, HS-74-01): artifacts become owner-typed the same way
        # proposals did in v5 — a run's output persists as an artifact with no
        # meeting anchor (origin='run', NULL meeting_id; lineage is the anchor).
        # SQLite cannot drop NOT NULL in place: the standard rebuild, FKs
        # suspended for the swap, ids preserved verbatim, existing rows all
        # origin='meeting'. Fresh DBs skip this entirely.
        artifact_cols = {
            row[1] for row in conn.execute("PRAGMA table_info(artifacts)").fetchall()
        }
        if artifact_cols and "origin" not in artifact_cols:
            conn.execute("PRAGMA foreign_keys = OFF")
            conn.executescript(
                """
                CREATE TABLE artifacts_v6 (
                    id TEXT PRIMARY KEY,
                    meeting_id TEXT REFERENCES meetings(id) ON DELETE CASCADE,
                    origin TEXT NOT NULL DEFAULT 'meeting' CHECK (origin IN ('meeting', 'run')),
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
                INSERT INTO artifacts_v6 (
                    id, meeting_id, origin, artifact_type, title, body_markdown,
                    structured_json, confidence, status, plugin_id, plugin_version,
                    created_at, updated_at)
                SELECT
                    id, meeting_id, 'meeting', artifact_type, title, body_markdown,
                    structured_json, confidence, status, plugin_id, plugin_version,
                    created_at, updated_at
                FROM artifacts;
                DROP TABLE artifacts;
                ALTER TABLE artifacts_v6 RENAME TO artifacts;
                CREATE INDEX IF NOT EXISTS idx_artifacts_meeting ON artifacts(meeting_id, created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_artifacts_type ON artifacts(artifact_type, created_at DESC);
                """
            )
            conn.execute("PRAGMA foreign_keys = ON")
        # v18 (HS-92-07): attempts retain the canonical actual target, boundary,
        # data classes, engine/model, and fallback reason as one additive JSON
        # receipt. ``destination`` remains the version-1 alias for old clients.
        attempt_cols = {
            row[1] for row in conn.execute("PRAGMA table_info(capability_attempts)").fetchall()
        }
        if attempt_cols and "actual_placement_json" not in attempt_cols:
            conn.execute(
                "ALTER TABLE capability_attempts "
                "ADD COLUMN actual_placement_json TEXT NOT NULL DEFAULT '{}'"
            )
        # v19 (HS-92-08): keep the legacy aggregate ``status`` as a projection
        # while making review, authorization, and execution independently
        # queryable. Existing rows are deterministically backfilled.
        actuator_cols = {
            row[1] for row in conn.execute("PRAGMA table_info(actuator_proposals)").fetchall()
        }
        authority_columns = {
            "review_decision": "TEXT NOT NULL DEFAULT 'unreviewed'",
            "authorization_state": "TEXT NOT NULL DEFAULT 'proposed'",
            "execution_state": "TEXT NOT NULL DEFAULT 'not_started'",
            "operation_json": "TEXT NOT NULL DEFAULT '{}'",
            "policy_snapshot_json": "TEXT NOT NULL DEFAULT '{}'",
            "grant_id": "TEXT",
        }
        for column, sql_type in authority_columns.items():
            if actuator_cols and column not in actuator_cols:
                conn.execute(f"ALTER TABLE actuator_proposals ADD COLUMN {column} {sql_type}")
        if actuator_cols:
            conn.execute(
                """UPDATE actuator_proposals SET
                    review_decision = 'unreviewed',
                    authorization_state = CASE
                        WHEN status IN ('approved','executed','failed') THEN 'approved'
                        WHEN status = 'rejected' THEN 'rejected'
                        ELSE 'proposed' END,
                    execution_state = CASE
                        WHEN status = 'executed' THEN 'succeeded'
                        WHEN status = 'failed' THEN 'failed'
                        ELSE 'not_started' END"""
            )
        # v22 (HS-93-07): the existing steering audit is also the source of
        # Coder Receipts. Preserve the exact operation and central policy
        # decision used by each new attempt; old rows retain honest empty
        # snapshots and continue projecting with their legacy grant basis.
        steering_cols = {
            row[1]
            for row in conn.execute("PRAGMA table_info(steering_audit)").fetchall()
        }
        steering_receipt_columns = {
            "operation_json": "TEXT NOT NULL DEFAULT '{}'",
            "policy_snapshot_json": "TEXT NOT NULL DEFAULT '{}'",
        }
        for column, sql_type in steering_receipt_columns.items():
            if steering_cols and column not in steering_cols:
                conn.execute(
                    f"ALTER TABLE steering_audit ADD COLUMN {column} {sql_type}"
                )
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
