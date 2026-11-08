"""Meetings, transcripts, action items, deferred intel, MIR plugin runs and artifacts.

Part 1 of 17 of SCHEMA_SQL, in execution order (holdspeak/db/schema/__init__.py)."""

SQL = """
-- Enable foreign keys
PRAGMA foreign_keys = ON;

-- Informational schema stamp (nothing gates on it; the reconcile is shape-based)
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Meetings table (core entity)
CREATE TABLE IF NOT EXISTS meetings (
    id TEXT PRIMARY KEY,
    parked INTEGER NOT NULL DEFAULT 0,
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
    route_fence_pending INTEGER NOT NULL DEFAULT 0,
    route_fence_error TEXT,
    transcription_status TEXT NOT NULL DEFAULT 'active',
    transcription_status_detail_json TEXT,
    capture_checkpoint_at TEXT,
    capture_checkpoint_seconds REAL NOT NULL DEFAULT 0,
    provenance TEXT NOT NULL DEFAULT 'desktop',
    calendar_event_id TEXT,
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

-- PHILO-13 C3: one durable unseen marker for each newly-ready meeting.
-- Rows are created only by a real readiness producer; historical summaries
-- have no row and therefore never become Dock attention by migration.
CREATE TABLE IF NOT EXISTS meeting_ready_reads (
    meeting_id TEXT PRIMARY KEY REFERENCES meetings(id) ON DELETE CASCADE,
    ready_at TEXT NOT NULL,
    read_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_meeting_ready_reads_unread
ON meeting_ready_reads(read_at, ready_at DESC);

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
    meeting_id TEXT REFERENCES meetings(id) ON DELETE CASCADE,
    task TEXT NOT NULL,
    owner TEXT,
    due TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    review_state TEXT NOT NULL DEFAULT 'pending',
    reviewed_at TEXT,
    source_timestamp REAL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at TEXT,
    delegated_at TEXT,
    source_type TEXT NOT NULL DEFAULT 'meeting',
    source_ref TEXT NOT NULL DEFAULT '',
    -- Betterment D0: the due as the meeting said it ("Friday next week");
    -- `due` holds the ISO day it names, read against the meeting's date.
    due_said TEXT,
    -- Betterment D3: kept on arrival (a finished summary kept this promise
    -- with no press), and when he saw it in Needs you (NEW until then).
    arrived_at TEXT,
    arrival_seen_at TEXT
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

-- Deferred intel jobs for meetings that need later processing.  One Meeting may
-- retain historical jobs while a fresh immutable descriptor is queued.  Queue
-- state carries references and hashes only; never transcript bytes.
CREATE TABLE IF NOT EXISTS intel_jobs (
    job_id TEXT PRIMARY KEY,
    meeting_id TEXT NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    origin_job_id TEXT REFERENCES intel_jobs(job_id),
    work_descriptor_sha256 TEXT NOT NULL,
    transcript_hash TEXT NOT NULL,
    displaced_work TEXT NOT NULL DEFAULT '[]',
    status TEXT NOT NULL DEFAULT 'queued',
    lifecycle_posture TEXT NOT NULL DEFAULT 'queued',
    claim_id TEXT,
    parent_operation_id TEXT,
    bundle_id TEXT,
    bundle_sha256 TEXT,
    executor_lease_token TEXT,
    executor_lease_epoch INTEGER NOT NULL DEFAULT 0,
    executor_lease_expires_at REAL,
    model_host TEXT,
    planned_route_json TEXT,
    run_receipt_json TEXT,
    requested_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    attempts INTEGER NOT NULL DEFAULT 0,
    last_error TEXT
);

-- Append-only deferred-intel ledger.  meeting_id keeps pre-C rows readable;
-- job_id keys every new event to the immutable job that caused it.
CREATE TABLE IF NOT EXISTS intel_job_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meeting_id TEXT NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
    job_id TEXT REFERENCES intel_jobs(job_id),
    origin_job_id TEXT REFERENCES intel_jobs(job_id),
    claim_id TEXT,
    parent_operation_id TEXT,
    bundle_id TEXT,
    event_kind TEXT NOT NULL DEFAULT 'attempt',
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

-- HS-125-03: optional accountable action minted from an accepted decision.
CREATE TABLE IF NOT EXISTS decision_commitments (
    id          TEXT PRIMARY KEY,
    decision_id TEXT NOT NULL,
    action_item_id TEXT NOT NULL,
    owner       TEXT,
    due_at      TEXT,
    status      TEXT NOT NULL DEFAULT 'open',
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_decision_commitments_decision ON decision_commitments(decision_id);
CREATE INDEX IF NOT EXISTS idx_decision_commitments_status ON decision_commitments(status);

CREATE INDEX IF NOT EXISTS idx_topics_meeting ON topics(meeting_id);
CREATE INDEX IF NOT EXISTS idx_meetings_date ON meetings(started_at);
CREATE INDEX IF NOT EXISTS idx_intel_jobs_status ON intel_jobs(status, requested_at);
CREATE INDEX IF NOT EXISTS idx_intel_jobs_meeting_current ON intel_jobs(meeting_id, status, requested_at DESC);
CREATE INDEX IF NOT EXISTS idx_intel_job_attempts_meeting ON intel_job_attempts(meeting_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_intel_job_attempts_job ON intel_job_attempts(job_id, created_at DESC);
-- The queue-owned activation marker is the reserve-inert handoff provider's
-- independent lifecycle witness: one append-only marker per reservation.
CREATE UNIQUE INDEX IF NOT EXISTS uq_intel_job_handoff_activation
ON intel_job_attempts(job_id, event_kind) WHERE event_kind='handoff_activated';
-- A work descriptor can have one execution owner. Terminal history may coexist.
CREATE UNIQUE INDEX IF NOT EXISTS uq_intel_jobs_active_descriptor
ON intel_jobs(meeting_id, work_descriptor_sha256)
WHERE status IN ('reserved', 'queued', 'claimed', 'running');
CREATE UNIQUE INDEX IF NOT EXISTS uq_intel_job_claim
ON intel_jobs(claim_id) WHERE claim_id IS NOT NULL;
CREATE TRIGGER IF NOT EXISTS intel_jobs_immutable_descriptor
BEFORE UPDATE OF job_id, meeting_id, transcript_hash, displaced_work, work_descriptor_sha256 ON intel_jobs
WHEN OLD.work_descriptor_sha256 != ''
BEGIN SELECT RAISE(ABORT, 'intel job descriptor is immutable'); END;
CREATE TRIGGER IF NOT EXISTS intel_job_attempts_append_only_update
BEFORE UPDATE ON intel_job_attempts
BEGIN SELECT RAISE(ABORT, 'intel job attempts are append-only'); END;
-- Meeting deletion remains the existing foreign-key retention boundary; queue
-- code never deletes individual ledger events.
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
    -- persona/chain/workflow run's output) carry NULL -- their anchor is the
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
    source_run_id TEXT,
    source_item_id TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
-- NOTE (HS-137-01): the unique index was previously in migrations.py to handle
-- both fresh and upgrade paths; reconcile_schema now ensures columns exist first,
-- so the index is safe here.
CREATE UNIQUE INDEX IF NOT EXISTS idx_artifacts_source_run_item
ON artifacts(source_run_id, source_item_id)
WHERE source_run_id IS NOT NULL AND source_item_id IS NOT NULL;

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
