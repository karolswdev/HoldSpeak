"""Schema SQL and version constant for the HoldSpeak persistence layer.

Extracted from core.py (HS-117-10) so the schema definition is navigable
independently of the Database container.
"""

# Informational stamp only. Nothing gates on it: `reconcile_schema` detects
# missing tables and columns by comparing the live database against this
# SCHEMA_SQL shape directly, so you do NOT need to bump this to have a shape
# change take effect. Just edit SCHEMA_SQL; the reconcile applies it on open.
SCHEMA_VERSION = 64  # informational; owner's real DB is stamped 64

# SQL Schema
SCHEMA_SQL = """
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

-- HS-109-01: durable memory projected one-way from decisions artifacts. Source
-- keys deliberately are not foreign keys: deleting a meeting severs provenance
-- without deleting the memory. Sync-shaped clocks/tombstones are reserved for a
-- later wire contract with explicit lifecycle conflict semantics.
CREATE TABLE IF NOT EXISTS decisions (
    id TEXT PRIMARY KEY,
    text TEXT NOT NULL,
    rationale TEXT,
    decided_at TEXT NOT NULL,
    date_basis TEXT NOT NULL DEFAULT 'meeting_date',
    source_timestamp REAL,
    provenance_label TEXT
        CHECK (provenance_label IN ('reported','anchored')),
    source_artifact_id TEXT NOT NULL,
    source_meeting_id TEXT NOT NULL,
    source_state TEXT NOT NULL DEFAULT 'linked'
        CHECK (source_state IN ('linked','source_deleted')),
    project_key TEXT,
    lifecycle TEXT NOT NULL DEFAULT 'recorded'
        CHECK (lifecycle IN ('recorded','accepted','superseded','rejected')),
    superseded_by TEXT REFERENCES decisions(id),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    last_modified TEXT NOT NULL DEFAULT (datetime('now')),
    deleted INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_decisions_project
ON decisions(project_key, lifecycle, decided_at DESC);
CREATE INDEX IF NOT EXISTS idx_decisions_meeting
ON decisions(source_meeting_id, decided_at DESC);
CREATE INDEX IF NOT EXISTS idx_decisions_lifecycle
ON decisions(lifecycle, decided_at DESC);
CREATE INDEX IF NOT EXISTS idx_decisions_superseded_by
ON decisions(superseded_by);
CREATE TRIGGER IF NOT EXISTS decisions_sever_meeting_source
AFTER DELETE ON meetings BEGIN
    UPDATE decisions
       SET source_state = 'source_deleted',
           updated_at = datetime('now'),
           last_modified = datetime('now')
     WHERE source_meeting_id = OLD.id AND deleted = 0;
END;

-- Phase 37 (HS-37-02): actuator proposals -- a proposed external side effect
-- awaiting human approval. Lifecycle: proposed -> approved -> executed |
-- rejected | failed (a failed proposal may be re-approved for retry).
-- `payload_json` is the parity source-of-truth the guarded executor checks
-- before acting (HS-37-04); every transition is recorded in
-- actuator_proposal_audit so "no silent egress" is provable after the fact.
CREATE TABLE IF NOT EXISTS actuator_proposals (
    id TEXT PRIMARY KEY,
    -- v5 (Phase 72): a proposal is owner-typed. origin='meeting' rows carry a
    -- real meeting_id; origin='desk' rows (the iPad desk relay) carry NULL --
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
    control_mode TEXT NOT NULL DEFAULT 'yolo'
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
-- home for the in-process `CorrectionStore` ring -- corrections written through
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
-- back to setup-mode. Opaque keys only -- no payload, no secrets.
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
-- record of each dictation/dry-run pipeline run -- what was said, how it routed,
-- what got typed, and per-stage latency -- so the daily-driver dictation loop
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

-- -- Primitive Framework: the desk's synced first-class primitives --------
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

-- HS-141-01: one immutable raw capture plus one ordinary editable Note.  The
-- aggregate owns lifecycle/revision; no status or ownership column is added to
-- notes, so ordinary Note metadata never becomes a second state machine.
CREATE TABLE IF NOT EXISTS refinement_thoughts (
    id TEXT PRIMARY KEY,
    create_request_id TEXT NOT NULL UNIQUE,
    create_payload_sha256 TEXT NOT NULL,
    raw_utf8 BLOB NOT NULL,
    raw_sha256 TEXT NOT NULL,
    raw_source_kind TEXT NOT NULL,
    raw_source_ref TEXT,
    raw_captured_at TEXT NOT NULL,
    working_note_id TEXT NOT NULL UNIQUE REFERENCES notes(id),
    working_revision INTEGER NOT NULL CHECK (working_revision >= 1),
    lifecycle_revision INTEGER NOT NULL DEFAULT 1 CHECK (lifecycle_revision >= 1),
    attachment_revision INTEGER NOT NULL DEFAULT 0 CHECK (attachment_revision >= 0),
    attachment_sha256 TEXT NOT NULL DEFAULT '',
    aggregate_revision INTEGER NOT NULL DEFAULT 1 CHECK (aggregate_revision >= 1),
    continuity_revision INTEGER NOT NULL DEFAULT 0 CHECK (continuity_revision >= 0),
    resume_order INTEGER NOT NULL DEFAULT 0,
    state TEXT NOT NULL CHECK (state IN ('working', 'completed', 'tombstoned')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    completed_at TEXT,
    tombstoned_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_refinement_thoughts_resume
ON refinement_thoughts(state, resume_order DESC, id DESC);
CREATE TABLE IF NOT EXISTS refinement_resume_sequence (
    id INTEGER PRIMARY KEY CHECK (id=1),
    value INTEGER NOT NULL
);
INSERT OR IGNORE INTO refinement_resume_sequence(id,value) VALUES(1,0);

CREATE TABLE IF NOT EXISTS refinement_working_revisions (
    thought_id TEXT NOT NULL REFERENCES refinement_thoughts(id),
    revision INTEGER NOT NULL CHECK (revision >= 1),
    title TEXT NOT NULL,
    body_markdown TEXT NOT NULL,
    tags_json TEXT NOT NULL,
    content_sha256 TEXT NOT NULL,
    accepted_at TEXT NOT NULL,
    PRIMARY KEY (thought_id, revision)
);

CREATE TABLE IF NOT EXISTS refinement_lifecycle_revisions (
    thought_id TEXT NOT NULL REFERENCES refinement_thoughts(id),
    lifecycle_revision INTEGER NOT NULL,
    aggregate_revision INTEGER NOT NULL,
    prior_state TEXT,
    state TEXT NOT NULL,
    command TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    entry_sha256 TEXT NOT NULL,
    PRIMARY KEY (thought_id, lifecycle_revision),
    UNIQUE (thought_id, aggregate_revision)
);

CREATE TABLE IF NOT EXISTS refinement_aggregate_commands (
    thought_id TEXT NOT NULL REFERENCES refinement_thoughts(id),
    aggregate_revision INTEGER NOT NULL,
    command_kind TEXT NOT NULL,
    prior_working_revision INTEGER NOT NULL,
    next_working_revision INTEGER NOT NULL,
    prior_lifecycle_revision INTEGER NOT NULL,
    next_lifecycle_revision INTEGER NOT NULL,
    prior_attachment_revision INTEGER NOT NULL,
    next_attachment_revision INTEGER NOT NULL,
    canonical_version INTEGER NOT NULL DEFAULT 1 CHECK (canonical_version IN (1,2)),
    attachment_sha256 TEXT,
    canonical_sha256 TEXT NOT NULL,
    lifecycle_sha256 TEXT,
    accepted_at TEXT NOT NULL,
    PRIMARY KEY (thought_id, aggregate_revision)
);

CREATE TABLE IF NOT EXISTS refinement_attachment_revisions (
    thought_id TEXT NOT NULL REFERENCES refinement_thoughts(id),
    attachment_revision INTEGER NOT NULL CHECK (attachment_revision >= 1),
    aggregate_revision INTEGER NOT NULL,
    attachment_sha256 TEXT NOT NULL,
    visible_count INTEGER NOT NULL CHECK (visible_count >= 0),
    leaf_count INTEGER NOT NULL CHECK (leaf_count >= 0),
    created_at TEXT NOT NULL,
    PRIMARY KEY (thought_id, attachment_revision),
    UNIQUE (thought_id, aggregate_revision)
);
CREATE TABLE IF NOT EXISTS refinement_attachment_visible (
    thought_id TEXT NOT NULL,
    attachment_revision INTEGER NOT NULL,
    ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
    visible_ref TEXT NOT NULL,
    visible_kind TEXT NOT NULL CHECK (visible_kind IN ('note','knowledge')),
    visible_title TEXT NOT NULL,
    source_last_modified TEXT NOT NULL,
    visible_sha256 TEXT NOT NULL,
    PRIMARY KEY (thought_id, attachment_revision, ordinal),
    UNIQUE (thought_id, attachment_revision, visible_ref),
    FOREIGN KEY (thought_id, attachment_revision)
      REFERENCES refinement_attachment_revisions(thought_id, attachment_revision)
);
CREATE TABLE IF NOT EXISTS refinement_attachment_leaves (
    thought_id TEXT NOT NULL,
    attachment_revision INTEGER NOT NULL,
    visible_ordinal INTEGER NOT NULL CHECK (visible_ordinal >= 0),
    leaf_ordinal INTEGER NOT NULL CHECK (leaf_ordinal >= 0),
    leaf_ref TEXT NOT NULL,
    leaf_title TEXT NOT NULL,
    source_last_modified TEXT NOT NULL,
    membership_last_modified TEXT NOT NULL,
    leaf_content_sha256 TEXT NOT NULL,
    leaf_metadata_sha256 TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (thought_id, attachment_revision, visible_ordinal, leaf_ordinal),
    UNIQUE (thought_id, attachment_revision, visible_ordinal, leaf_ref),
    FOREIGN KEY (thought_id, attachment_revision, visible_ordinal)
      REFERENCES refinement_attachment_visible(thought_id, attachment_revision, ordinal)
);
CREATE TABLE IF NOT EXISTS refinement_context_actions (
    action_id TEXT PRIMARY KEY,
    request_id TEXT NOT NULL UNIQUE,
    request_sha256 TEXT NOT NULL,
    thought_id TEXT NOT NULL REFERENCES refinement_thoughts(id),
    action_kind TEXT NOT NULL CHECK (action_kind IN ('attach','detach','refresh')),
    visible_ref TEXT NOT NULL,
    prior_aggregate_revision INTEGER NOT NULL,
    prior_attachment_revision INTEGER NOT NULL,
    post_aggregate_revision INTEGER NOT NULL,
    post_attachment_revision INTEGER NOT NULL,
    post_attachment_sha256 TEXT NOT NULL,
    receipt_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);

-- HS-141-05A: hub-local owner policy for the complete default AI-context SET.
-- Policy and mutation receipts never sync; each locally born Thought separately
-- records the exact policy head it observed and the attachment result.
CREATE TABLE IF NOT EXISTS refinement_default_context_revisions (
    revision INTEGER PRIMARY KEY CHECK (revision >= 0),
    configuration_sha256 TEXT NOT NULL,
    refs_json TEXT NOT NULL,
    labels_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS refinement_default_context_current (
    id INTEGER PRIMARY KEY CHECK (id=1),
    revision INTEGER NOT NULL REFERENCES refinement_default_context_revisions(revision),
    configuration_sha256 TEXT NOT NULL,
    refs_json TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS refinement_default_context_actions (
    action_id TEXT PRIMARY KEY,
    request_id TEXT NOT NULL UNIQUE,
    request_sha256 TEXT NOT NULL,
    prior_revision INTEGER NOT NULL,
    post_revision INTEGER NOT NULL,
    post_configuration_sha256 TEXT NOT NULL,
    receipt_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS refinement_default_context_applications (
    application_id TEXT PRIMARY KEY,
    thought_id TEXT NOT NULL UNIQUE REFERENCES refinement_thoughts(id),
    create_request_id TEXT NOT NULL UNIQUE,
    default_revision INTEGER NOT NULL,
    default_configuration_sha256 TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('empty','applied','not_applied')),
    attachment_zero_sha256 TEXT NOT NULL,
    attachment_revision INTEGER NOT NULL CHECK (attachment_revision >= 0),
    attachment_sha256 TEXT NOT NULL,
    error_code TEXT NOT NULL DEFAULT '',
    failure_json TEXT NOT NULL DEFAULT 'null',
    failure_sha256 TEXT NOT NULL DEFAULT '74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b',
    receipt_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
INSERT OR IGNORE INTO refinement_default_context_revisions
    (revision,configuration_sha256,refs_json,labels_json,created_at)
VALUES
    (0,'4e04806a2695b3ac90e3ed39b69cb2ffa41f94f7af6cc55d262764c240c6a778','[]','[]',datetime('now'));
INSERT OR IGNORE INTO refinement_default_context_current
    (id,revision,configuration_sha256,refs_json,updated_at)
VALUES
    (1,0,'4e04806a2695b3ac90e3ed39b69cb2ffa41f94f7af6cc55d262764c240c6a778','[]',datetime('now'));

-- HS-141-06: a local Good-enough receipt is retry proof for one owner
-- completion request. It is not sync state or a second lifecycle.
CREATE TABLE IF NOT EXISTS refinement_completion_receipts (
    receipt_id TEXT PRIMARY KEY,
    thought_id TEXT NOT NULL REFERENCES refinement_thoughts(id),
    request_id TEXT NOT NULL UNIQUE,
    request_sha256 TEXT NOT NULL,
    aggregate_revision INTEGER NOT NULL,
    lifecycle_revision INTEGER NOT NULL,
    continuity_revision INTEGER NOT NULL DEFAULT 0,
    committed_hub_id TEXT NOT NULL DEFAULT '',
    working_note_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE (thought_id, aggregate_revision)
);

-- A peer can receive a sync tombstone before its live aggregate. Preserve the
-- high-water fence so a delayed live bundle cannot resurrect custody.
CREATE TABLE IF NOT EXISTS refinement_thought_sync_tombstones (
    thought_id TEXT PRIMARY KEY,
    expected_revision INTEGER NOT NULL DEFAULT 0,
    aggregate_revision INTEGER NOT NULL DEFAULT 0,
    lifecycle_revision INTEGER NOT NULL DEFAULT 0,
    lifecycle_sha256 TEXT NOT NULL DEFAULT '',
    terminal_working_note_id TEXT NOT NULL DEFAULT '',
    terminal_fingerprint TEXT NOT NULL DEFAULT '',
    last_modified TEXT NOT NULL,
    tombstoned_at TEXT NOT NULL
);

-- HS-113-08: authored Architecture Decision Records. Deliberately separate
-- from the HS-109 meeting-derived `decisions` memory projection.
CREATE TABLE IF NOT EXISTS desk_decisions (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'proposed'
        CHECK (status IN ('proposed','accepted','superseded','deprecated')),
    deciders_json TEXT NOT NULL DEFAULT '[]',
    decided_at TEXT,
    context_markdown TEXT NOT NULL DEFAULT '',
    decision_markdown TEXT NOT NULL DEFAULT '',
    alternatives_json TEXT NOT NULL DEFAULT '[]',
    consequences_markdown TEXT NOT NULL DEFAULT '',
    superseded_by TEXT REFERENCES desk_decisions(id),
    tags_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    deleted INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_desk_decisions_status
ON desk_decisions(status, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_desk_decisions_superseded_by
ON desk_decisions(superseded_by);

-- HS-127-01 / HS-130-08: durable, source-neutral decision records. A decision
-- record preserves a decision's canonical governing document while sources,
-- follow-through, and edits remain separately traceable. "Receipt" is reserved
-- for immutable kernel evidence (Constitution Art. XI); this mutable governing
-- document is a Decision Record.
CREATE TABLE IF NOT EXISTS decision_records (
    id TEXT PRIMARY KEY,
    decision_text TEXT NOT NULL,
    rationale TEXT,
    alternatives TEXT,
    owner TEXT,
    review_date TEXT,
    lifecycle TEXT NOT NULL DEFAULT 'active',
    source_type TEXT NOT NULL,
    source_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deleted INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS decision_record_sources (
    id TEXT PRIMARY KEY,
    record_id TEXT NOT NULL REFERENCES decision_records(id),
    source_type TEXT NOT NULL,
    source_ref TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_decision_record_sources
ON decision_record_sources(record_id);

CREATE TABLE IF NOT EXISTS decision_record_work (
    id TEXT PRIMARY KEY,
    record_id TEXT NOT NULL REFERENCES decision_records(id),
    work_type TEXT NOT NULL,
    work_ref TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_decision_record_work
ON decision_record_work(record_id);

CREATE TABLE IF NOT EXISTS decision_record_revisions (
    id TEXT PRIMARY KEY,
    record_id TEXT NOT NULL REFERENCES decision_records(id),
    field_name TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_decision_record_revisions
ON decision_record_revisions(record_id);

-- HS-109-04: one retrieval contract, three separately ranked FTS corpora.
-- Internal-content tables retain stable text source ids directly; this avoids
-- pretending the stores' TEXT primary keys are FTS integer content_rowids.
CREATE VIRTUAL TABLE IF NOT EXISTS decisions_memory_fts USING fts5(
    source_id UNINDEXED, text, rationale
);
CREATE VIRTUAL TABLE IF NOT EXISTS artifacts_memory_fts USING fts5(
    source_id UNINDEXED, title, body_markdown
);
CREATE VIRTUAL TABLE IF NOT EXISTS notes_memory_fts USING fts5(
    source_id UNINDEXED, title, body_markdown
);

CREATE TRIGGER IF NOT EXISTS decisions_memory_ai AFTER INSERT ON decisions
WHEN NEW.deleted = 0 AND NEW.source_state = 'linked' BEGIN
    INSERT INTO decisions_memory_fts(source_id,text,rationale)
    VALUES(NEW.id,NEW.text,COALESCE(NEW.rationale,''));
END;
CREATE TRIGGER IF NOT EXISTS decisions_memory_ad AFTER DELETE ON decisions BEGIN
    DELETE FROM decisions_memory_fts WHERE source_id=OLD.id;
END;
CREATE TRIGGER IF NOT EXISTS decisions_memory_au AFTER UPDATE ON decisions BEGIN
    DELETE FROM decisions_memory_fts WHERE source_id=OLD.id;
    INSERT INTO decisions_memory_fts(source_id,text,rationale)
    SELECT NEW.id,NEW.text,COALESCE(NEW.rationale,'')
    WHERE NEW.deleted=0 AND NEW.source_state='linked';
END;

CREATE TRIGGER IF NOT EXISTS artifacts_memory_ai AFTER INSERT ON artifacts BEGIN
    INSERT INTO artifacts_memory_fts(source_id,title,body_markdown)
    VALUES(NEW.id,NEW.title,NEW.body_markdown);
END;
CREATE TRIGGER IF NOT EXISTS artifacts_memory_ad AFTER DELETE ON artifacts BEGIN
    DELETE FROM artifacts_memory_fts WHERE source_id=OLD.id;
END;
CREATE TRIGGER IF NOT EXISTS artifacts_memory_au AFTER UPDATE ON artifacts BEGIN
    DELETE FROM artifacts_memory_fts WHERE source_id=OLD.id;
    INSERT INTO artifacts_memory_fts(source_id,title,body_markdown)
    VALUES(NEW.id,NEW.title,NEW.body_markdown);
END;

CREATE TRIGGER IF NOT EXISTS notes_memory_ai AFTER INSERT ON notes
WHEN NEW.deleted = 0 BEGIN
    INSERT INTO notes_memory_fts(source_id,title,body_markdown)
    VALUES(NEW.id,NEW.title,NEW.body_markdown);
END;
CREATE TRIGGER IF NOT EXISTS notes_memory_ad AFTER DELETE ON notes BEGIN
    DELETE FROM notes_memory_fts WHERE source_id=OLD.id;
END;
CREATE TRIGGER IF NOT EXISTS notes_memory_au AFTER UPDATE ON notes BEGIN
    DELETE FROM notes_memory_fts WHERE source_id=OLD.id;
    INSERT INTO notes_memory_fts(source_id,title,body_markdown)
    SELECT NEW.id,NEW.title,NEW.body_markdown WHERE NEW.deleted=0;
END;

-- KB (organization/synced): the desk's knowledge container -- a named bag of
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
        CHECK (state IN ('running','succeeded','failed','cancelled','unavailable','empty','unknown')),
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
        CHECK (state IN ('running','succeeded','failed','cancelled','empty','unknown')),
    error TEXT,
    result_ref TEXT,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    UNIQUE(invocation_id, attempt_index)
);
CREATE INDEX IF NOT EXISTS idx_capability_attempts_invocation
ON capability_attempts(invocation_id, attempt_index);

-- Runtime profile (capability/synced, Phase 24): a named "where intelligence runs"
-- target. SHAPE ONLY -- the API key NEVER lives here and never syncs; the hub joins
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

-- Model manifest (capability/synced, HSM-16-08): "this node has this model" --
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

-- Mesh relay queue (HS-85-01): HUB-LOCAL run rows -- a run addressed to one
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
    completed_at TEXT,
    -- v59 (HS-131-16): explicit hub-local relay proof. The stable destination
    -- identity and the EXACT enqueue-time credential generation are captured
    -- here, not recomputed from a name, so a rotated or re-paired credential
    -- can never claim work addressed to its predecessor. The signed offer and
    -- the content-free worker terminal report are stored beside them rather
    -- than tunnelled through the legacy `task_kind` JSON field.
    destination_node_id TEXT NOT NULL DEFAULT '',
    destination_generation INTEGER NOT NULL DEFAULT 0,
    claimed_by_node_id TEXT NOT NULL DEFAULT '',
    claimed_generation INTEGER NOT NULL DEFAULT 0,
    claim_nonce TEXT NOT NULL DEFAULT '',
    dispatch_offer_json TEXT NOT NULL DEFAULT '',
    worker_terminal_json TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_mesh_relay_jobs_node_status
    ON mesh_relay_jobs(node, status);

-- Mesh worker liveness (HS-85-01): last claim-poll per node. Liveness is
-- born from the worker's own polling; the mesh has no other heartbeat.
CREATE TABLE IF NOT EXISTS mesh_workers (
    node TEXT PRIMARY KEY,
    last_seen TEXT NOT NULL DEFAULT (datetime('now')),
    -- v59 (HS-131-16): liveness belongs to the exact credential that polled, not
    -- to a name. The claim leg stamps the authenticated `(node_id, generation)`
    -- pair, so activity under one generation can never make its replacement — or
    -- its predecessor — look alive.
    node_id TEXT NOT NULL DEFAULT '',
    credential_generation INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_mesh_workers_identity
    ON mesh_workers(node_id, credential_generation);

-- Worker-local replay reservations (HS-131-16, design §4.1). The WORKER's own
-- database, never the hub's: one row elects the single executor of one signed
-- offer. `INSERT ... ON CONFLICT DO NOTHING` on the primary key is the whole
-- election, so a replayed offer, a concurrent second worker, and a process
-- restart all refuse `mesh_offer_replayed` BEFORE revision persistence, runner
-- construction, or provider dispatch. Reservation residue left by a crash
-- reconciles to `indeterminate` and is never rerun under the same authority.
CREATE TABLE IF NOT EXISTS mesh_worker_reservations (
    hub_key_id TEXT NOT NULL,
    hub_operation_id TEXT NOT NULL,
    first_ordinal INTEGER NOT NULL,
    offer_id TEXT NOT NULL DEFAULT '',
    job_id TEXT NOT NULL DEFAULT '',
    state TEXT NOT NULL DEFAULT 'reserved', -- reserved | settled | indeterminate
    terminal_outcome TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    settled_at TEXT,
    PRIMARY KEY (hub_key_id, hub_operation_id, first_ordinal)
);

-- Directory (organization/synced): the canonical organization container; the
-- iPad renders it spatially as a "zone". Only identity + nesting sync here
-- (`id, name, parent_id`); the zone's geometry/paint is per-device layout and
-- stays on the surface, never canonical. `parent_id` chains = nested directories.
CREATE TABLE IF NOT EXISTS directories (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL DEFAULT '',
    name_normalized TEXT NOT NULL DEFAULT '',
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
CREATE UNIQUE INDEX IF NOT EXISTS idx_directory_name_norm
ON directories(name_normalized) WHERE deleted = 0;
CREATE INDEX IF NOT EXISTS idx_directory_memberships_dir ON directory_memberships(directory_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_memberships_resource ON knowledge_memberships(resource_ref, deleted);
CREATE INDEX IF NOT EXISTS idx_knowledge_memberships_modified ON knowledge_memberships(last_modified);
CREATE INDEX IF NOT EXISTS idx_project_resources_resource ON project_resources(resource_ref, deleted);
CREATE INDEX IF NOT EXISTS idx_project_resources_modified ON project_resources(last_modified);

-- -- Workbench (HS-116-01) ------------------------------------------------
-- A Workbench is a DeskPrimitive: one agent, one target, one schedule, N items.
CREATE TABLE IF NOT EXISTS workbenches (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL DEFAULT '',
    recipe_id TEXT,
    profile_id TEXT,
    resolver_profile_id TEXT,
    schedule TEXT,
    schedule_enabled INTEGER NOT NULL DEFAULT 0,
    schedule_revision INTEGER NOT NULL DEFAULT 1,
    item_order_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    last_modified TEXT NOT NULL DEFAULT (datetime('now')),
    deleted INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS workbench_items (
    id TEXT PRIMARY KEY,
    workbench_id TEXT NOT NULL,
    title TEXT NOT NULL DEFAULT '',
    body TEXT NOT NULL DEFAULT '',
    priority INTEGER NOT NULL DEFAULT 3,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'claimed', 'done', 'failed', 'dismissed')),
    grounding_json TEXT NOT NULL DEFAULT '{}',
    context_json TEXT NOT NULL DEFAULT '{}',
    result TEXT,
    result_egress_json TEXT,
    result_artifact_id TEXT,
    mint_attempted INTEGER NOT NULL DEFAULT 0,
    tokens_consumed INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    last_modified TEXT NOT NULL DEFAULT (datetime('now')),
    claimed_at TEXT,
    completed_at TEXT
);
CREATE TABLE IF NOT EXISTS workbench_runs (
    id TEXT PRIMARY KEY,
    workbench_id TEXT NOT NULL,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    items_attempted INTEGER NOT NULL DEFAULT 0,
    items_completed INTEGER NOT NULL DEFAULT 0,
    items_failed INTEGER NOT NULL DEFAULT 0,
    mint_failures INTEGER NOT NULL DEFAULT 0,
    total_tokens INTEGER NOT NULL DEFAULT 0,
    egress_boundary TEXT NOT NULL DEFAULT '',
    model TEXT NOT NULL DEFAULT '',
    constitutional_context_revision INTEGER NOT NULL DEFAULT 0,
    constitutional_context_hash TEXT NOT NULL DEFAULT '',
    skills_injected_json TEXT NOT NULL DEFAULT '[]',
    parent_operation_id TEXT NOT NULL DEFAULT '',
    parent_receipt_id TEXT NOT NULL DEFAULT '',
    child_links_json TEXT NOT NULL DEFAULT '[]',
    status TEXT NOT NULL DEFAULT 'running'
        CHECK (status IN ('running', 'completed', 'failed', 'cancelled', 'indeterminate'))
);
CREATE INDEX IF NOT EXISTS idx_workbenches_modified ON workbenches(last_modified DESC);
CREATE INDEX IF NOT EXISTS idx_workbench_items_workbench ON workbench_items(workbench_id, priority ASC);
CREATE INDEX IF NOT EXISTS idx_workbench_items_status ON workbench_items(workbench_id, status);
CREATE INDEX IF NOT EXISTS idx_workbench_runs_workbench ON workbench_runs(workbench_id, started_at DESC);

-- Intrinsic resourcefulness (v63). A policy observes one Workbench's negative
-- space and admits at most one causally scoped maintenance item per dispatch.
-- Candidate revisions are durable so restart/retry can never rediscover the
-- exact same opportunity as novel work.
CREATE TABLE IF NOT EXISTS resourceful_policies (
    workbench_id TEXT PRIMARY KEY REFERENCES workbenches(id) ON DELETE CASCADE,
    enabled INTEGER NOT NULL DEFAULT 0,
    idle_after_minutes INTEGER NOT NULL DEFAULT 30,
    cooldown_hours INTEGER NOT NULL DEFAULT 6,
    nightly_target INTEGER NOT NULL DEFAULT 2,
    night_only INTEGER NOT NULL DEFAULT 1,
    night_start_hour INTEGER NOT NULL DEFAULT 22,
    night_end_hour INTEGER NOT NULL DEFAULT 7,
    routines_json TEXT NOT NULL DEFAULT '["loose_ideas","failed_work"]',
    idle_since TEXT,
    idle_epoch INTEGER NOT NULL DEFAULT 0,
    last_checked_at TEXT,
    last_fired_at TEXT,
    night_key TEXT NOT NULL DEFAULT '',
    nightly_count INTEGER NOT NULL DEFAULT 0,
    last_outcome TEXT NOT NULL DEFAULT '',
    last_error TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS resourceful_dispatches (
    workbench_id TEXT NOT NULL REFERENCES resourceful_policies(workbench_id) ON DELETE CASCADE,
    candidate_key TEXT NOT NULL,
    routine TEXT NOT NULL,
    source_ref TEXT NOT NULL,
    event_id TEXT NOT NULL REFERENCES service_events(id) ON DELETE CASCADE,
    item_id TEXT NOT NULL REFERENCES workbench_items(id),
    operation_id TEXT,
    receipt_id TEXT,
    outcome TEXT NOT NULL DEFAULT 'admitted',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at TEXT,
    PRIMARY KEY (workbench_id, candidate_key)
);

CREATE INDEX IF NOT EXISTS idx_resourceful_policies_enabled
    ON resourceful_policies(enabled, updated_at);
CREATE INDEX IF NOT EXISTS idx_resourceful_dispatches_workbench
    ON resourceful_dispatches(workbench_id, created_at DESC);

-- Device-local owner authority for scheduled Workbench inference. Never sync.
CREATE TABLE IF NOT EXISTS kernel_schedule_delegations (
    id TEXT PRIMARY KEY, workbench_id TEXT NOT NULL,
    delegator_kind TEXT NOT NULL, delegator_identity TEXT NOT NULL,
    recipe_id TEXT NOT NULL, recipe_revision TEXT NOT NULL,
    workbench_revision TEXT NOT NULL, schedule_revision TEXT NOT NULL,
    cadence TEXT NOT NULL, deployment_revision_id TEXT NOT NULL,
    terms_sha256 TEXT NOT NULL, expires_at REAL,
    state TEXT NOT NULL CHECK (state IN ('LIVE','REVOKED','EXPIRED')),
    revoked_at REAL, revocation_reason TEXT NOT NULL DEFAULT '',
    created_at REAL NOT NULL, updated_at REAL NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_schedule_delegation_one_live
ON kernel_schedule_delegations(workbench_id) WHERE state='LIVE';
CREATE INDEX IF NOT EXISTS idx_schedule_delegations_workbench_state
ON kernel_schedule_delegations(workbench_id, state);
CREATE TABLE IF NOT EXISTS kernel_schedule_ticks (
    workbench_id TEXT NOT NULL, due_minute INTEGER NOT NULL,
    delegation_id TEXT NOT NULL, created_at REAL NOT NULL,
    PRIMARY KEY(workbench_id, due_minute)
);

-- Skills (HS-116-06): reusable procedural knowledge agents learn and apply.
CREATE TABLE IF NOT EXISTS skills (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL DEFAULT '',
    body TEXT NOT NULL DEFAULT '',
    source TEXT NOT NULL DEFAULT 'owner-authored'
        CHECK (source IN ('agent-proposed', 'owner-authored')),
    status TEXT NOT NULL DEFAULT 'active'
        CHECK (status IN ('draft', 'active', 'archived')),
    recipe_ids_json TEXT NOT NULL DEFAULT '[]',
    created_by TEXT NOT NULL DEFAULT '',
    version INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    last_modified TEXT NOT NULL DEFAULT (datetime('now')),
    deleted INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_skills_modified ON skills(last_modified DESC);
CREATE INDEX IF NOT EXISTS idx_skills_status ON skills(status);

-- Constitutional context (HS-116-13): migrated from file to DB.
CREATE TABLE IF NOT EXISTS constitutional_context (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    content TEXT NOT NULL DEFAULT '',
    revision INTEGER NOT NULL DEFAULT 0,
    content_hash TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS constitutional_context_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL DEFAULT '',
    revision INTEGER NOT NULL DEFAULT 0,
    content_hash TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- -- Cadence Engine (CAD-1-01) --------------------------------------------
-- Open Loops are source-PROJECTED entities: the collector idempotently upserts
-- one row per (source_type, source_id); the user's lifecycle decisions
-- (snoozed/killed/nudge_count) live only here and survive re-collection (a
-- killed loop stays killed). The engine is off by default and writes ONLY these
-- cadence_* tables -- it never performs an external side effect (that goes through
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

-- HS-104-02: the tool-call gate. A proposal is a RECORD, never authority --
-- nothing in this table can cause execution; only a live hook waiting on a
-- decision can proceed. Arguments are redacted at the edge (sha256 + first
-- 120 chars), never stored in full.
CREATE TABLE IF NOT EXISTS gate_proposals (
    id TEXT PRIMARY KEY,
    session_key TEXT NOT NULL,
    agent TEXT NOT NULL DEFAULT '',
    tool TEXT NOT NULL,
    args_sha256 TEXT NOT NULL,
    args_head TEXT NOT NULL DEFAULT '',
    cwd TEXT NOT NULL DEFAULT '',
    operation_json TEXT NOT NULL DEFAULT '{}',
    policy_snapshot_json TEXT NOT NULL DEFAULT '{}',
    created_at REAL NOT NULL,
    expires_at REAL NOT NULL,
    state TEXT NOT NULL DEFAULT 'held',
    decided_by TEXT,
    decided_at REAL,
    reason TEXT
);
CREATE INDEX IF NOT EXISTS idx_gate_proposals_state ON gate_proposals(state);
CREATE INDEX IF NOT EXISTS idx_gate_proposals_session ON gate_proposals(session_key);

CREATE TABLE IF NOT EXISTS gate_audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL DEFAULT (datetime('now')),
    proposal_id TEXT NOT NULL,
    session_key TEXT NOT NULL,
    tool TEXT NOT NULL,
    args_sha256 TEXT NOT NULL,
    event TEXT NOT NULL,
    detail TEXT,
    decided_by TEXT
);
CREATE INDEX IF NOT EXISTS idx_gate_audit_ts ON gate_audit(ts);
CREATE INDEX IF NOT EXISTS idx_gate_audit_proposal ON gate_audit(proposal_id);

-- HS-104-05: the REPORTED tier of a session receipt. One row per
-- session, replaced on every report; each cache figure stays its own
-- column (never summed into one number). Rows exist only for
-- adapters whose ledger standing for usage_tokens is authoritative.
CREATE TABLE IF NOT EXISTS session_usage (
    session_key TEXT PRIMARY KEY,
    model TEXT NOT NULL DEFAULT '',
    input_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    cache_read_tokens INTEGER NOT NULL DEFAULT 0,
    cache_creation_tokens INTEGER NOT NULL DEFAULT 0,
    reported_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Work attempts (HS-94-04, PLATFORM-CONTRACT 4.2): one bounded undertaking
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

-- Command receipts, hub half (HS-94-06, PLATFORM-CONTRACT 8): one row per
-- dispatched command envelope. Privacy 8.1: the payload's sha256 + bounded
-- head only -- full steer text is never retained merely because it crossed
-- the node link. receipt_json joins the node's stored receipt by command_id.
CREATE TABLE IF NOT EXISTS delivery_command_receipts (
    command_id TEXT PRIMARY KEY,
    node_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    target_generation TEXT NOT NULL,
    operation_family TEXT NOT NULL,
    operation_verb TEXT NOT NULL,
    payload_sha256 TEXT NOT NULL,
    payload_head TEXT NOT NULL DEFAULT '',
    expected_sequence INTEGER,
    issued_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    dispatch_epoch TEXT,
    hub_state TEXT NOT NULL DEFAULT 'sent'
        CHECK (hub_state IN ('sent','claimed','unknown','complete',
                             'not_executed','indeterminate_after_node_reset')),
    receipt_id TEXT,
    receipt_json TEXT NOT NULL DEFAULT '{}',
    authority_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_delivery_command_receipts_node
ON delivery_command_receipts(node_id, hub_state);

-- Desktop typing native receipts (HS-107-02). The effect is durable; its text is not.
CREATE TABLE IF NOT EXISTS desktop_type_receipts (
    native_id TEXT PRIMARY KEY,
    operation_id TEXT NOT NULL UNIQUE,
    target_ref TEXT NOT NULL,
    payload_sha256 TEXT NOT NULL,
    text_bytes INTEGER NOT NULL,
    submit INTEGER NOT NULL CHECK (submit IN (0, 1)),
    head TEXT NOT NULL DEFAULT '',
    authority_basis TEXT NOT NULL,
    gesture TEXT NOT NULL,
    outcome TEXT NOT NULL,
    result_ref TEXT NOT NULL DEFAULT '',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Kernel operation journal (HS-106-04). Domain content remains in native tables.
CREATE TABLE IF NOT EXISTS kernel_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS kernel_operations (
    operation_id TEXT PRIMARY KEY,
    request_id TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    name TEXT NOT NULL,
    version INTEGER NOT NULL,
    principal_kind TEXT NOT NULL,
    principal_identity TEXT NOT NULL,
    target_ref TEXT NOT NULL,
    placement TEXT NOT NULL,
    envelope_sha256 TEXT NOT NULL,
    policy_version TEXT NOT NULL,
    authority_basis TEXT NOT NULL,
    delegator_kind TEXT NOT NULL DEFAULT '',
    delegator_identity TEXT NOT NULL DEFAULT '',
    state TEXT NOT NULL CHECK (state IN (
        'admitting','awaiting_decision','awaiting_execution','claimed',
        'succeeded','failed','refused','cancelled','indeterminate'
    )),
    revision INTEGER NOT NULL DEFAULT 1,
    native_id TEXT NOT NULL,
    parent_operation_id TEXT NOT NULL DEFAULT '',
    correlation_id TEXT NOT NULL DEFAULT '',
    decision TEXT,
    warrant_json TEXT NOT NULL DEFAULT '{}',
    warrant_revoked INTEGER NOT NULL DEFAULT 0,
    claimed_by TEXT,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL,
    UNIQUE(principal_identity, idempotency_key)
);
CREATE INDEX IF NOT EXISTS idx_kernel_operations_state
ON kernel_operations(state, created_at);
CREATE TABLE IF NOT EXISTS kernel_receipts (
    receipt_id TEXT PRIMARY KEY,
    operation_id TEXT NOT NULL UNIQUE REFERENCES kernel_operations(operation_id),
    state TEXT NOT NULL CHECK (state IN ('succeeded','failed','refused','cancelled','indeterminate')),
    outcome TEXT NOT NULL,
    result_ref TEXT NOT NULL DEFAULT '',
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS kernel_inference_receipt_attestations (
    receipt_id TEXT PRIMARY KEY REFERENCES kernel_receipts(receipt_id),
    operation_id TEXT NOT NULL UNIQUE REFERENCES kernel_operations(operation_id),
    material_json TEXT NOT NULL,
    signature TEXT NOT NULL,
    created_at REAL NOT NULL
);
CREATE TRIGGER IF NOT EXISTS kernel_inference_receipt_attestations_no_update
BEFORE UPDATE ON kernel_inference_receipt_attestations BEGIN
    SELECT RAISE(ABORT, 'immutable kernel inference receipt attestation');
END;
CREATE TRIGGER IF NOT EXISTS kernel_inference_receipt_attestations_no_delete
BEFORE DELETE ON kernel_inference_receipt_attestations BEGIN
    SELECT RAISE(ABORT, 'immutable kernel inference receipt attestation');
END;
CREATE TABLE IF NOT EXISTS kernel_journal (
    hub_sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    stream TEXT NOT NULL,
    stream_sequence INTEGER NOT NULL,
    event_id TEXT NOT NULL UNIQUE,
    operation_id TEXT NOT NULL,
    process_id TEXT NOT NULL DEFAULT '',
    correlation_id TEXT NOT NULL DEFAULT '',
    causation_id TEXT NOT NULL DEFAULT '',
    event_type TEXT NOT NULL,
    event_version INTEGER NOT NULL,
    refs_json TEXT NOT NULL DEFAULT '[]',
    privacy_class TEXT NOT NULL,
    head TEXT NOT NULL DEFAULT '',
    timestamp REAL NOT NULL,
    previous_sha256 TEXT NOT NULL,
    record_sha256 TEXT NOT NULL,
    UNIQUE(stream, stream_sequence)
);
CREATE INDEX IF NOT EXISTS idx_kernel_journal_operation
ON kernel_journal(operation_id, hub_sequence);

-- HS-131-03: runner results stage before their terminal receipt and materialize
-- only after that receipt is durable. Domain tables carry the corresponding
-- projection_stage_id unique key in their registered materializers.
CREATE TABLE IF NOT EXISTS kernel_projection_stages (
    stage_id TEXT PRIMARY KEY,
    invocation_id TEXT NOT NULL,
    operation_id TEXT NOT NULL REFERENCES kernel_operations(operation_id),
    kind TEXT NOT NULL,
    projection_json TEXT NOT NULL,
    projection_sha256 TEXT NOT NULL,
    result_ref TEXT NOT NULL UNIQUE,
    state TEXT NOT NULL CHECK (state IN ('STAGED','FINALIZING','PUBLISHED','DISCARDED')),
    final_result_json TEXT NOT NULL DEFAULT '',
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL,
    UNIQUE(invocation_id, kind)
);
CREATE INDEX IF NOT EXISTS idx_kernel_projection_stages_recovery
ON kernel_projection_stages(state, updated_at);

-- HS-131-03: Ask has no caller-owned write window. The response itself is a
-- receipt-gated native projection and may be replayed after a lost response.
CREATE TABLE IF NOT EXISTS ask_results (
    projection_stage_id TEXT PRIMARY KEY REFERENCES kernel_projection_stages(stage_id),
    invocation_id TEXT NOT NULL UNIQUE,
    operation_id TEXT NOT NULL UNIQUE REFERENCES kernel_operations(operation_id),
    receipt_id TEXT NOT NULL UNIQUE REFERENCES kernel_receipts(receipt_id),
    payload_json TEXT NOT NULL,
    created_at REAL NOT NULL
);

-- HS-141-02: hub-local refinement continuity. These rows deliberately point at
-- local kernel/Ask proof and are not carried by paired primitive sync.
CREATE TABLE IF NOT EXISTS refinement_hosts (
    host_id TEXT PRIMARY KEY,
    host_kind TEXT NOT NULL CHECK (host_kind IN ('web','mcp','test')),
    lease_epoch INTEGER NOT NULL CHECK (lease_epoch >= 1),
    heartbeat_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS refinement_invocations (
    id TEXT PRIMARY KEY,
    request_id TEXT NOT NULL UNIQUE,
    request_sha256 TEXT NOT NULL,
    thought_id TEXT NOT NULL REFERENCES refinement_thoughts(id),
    frozen_aggregate_revision INTEGER NOT NULL,
    frozen_working_revision INTEGER NOT NULL,
    frozen_attachment_revision INTEGER NOT NULL,
    frozen_attachment_sha256 TEXT NOT NULL DEFAULT '',
    admission_json TEXT NOT NULL DEFAULT '{}',
    admission_sha256 TEXT NOT NULL DEFAULT '',
    route_plan_id TEXT,
    operation_plan_id TEXT,
    route_execution_id TEXT,
    review_result_id TEXT UNIQUE,
    state TEXT NOT NULL CHECK (state IN (
        'reserved','in_flight','awaiting_projection','review_ready',
        'failed','refused','cancelled','indeterminate','unknown','stale','superseded'
    )),
    terminal_code TEXT NOT NULL DEFAULT '',
    dispatch_host_id TEXT REFERENCES refinement_hosts(host_id),
    dispatch_lease_epoch INTEGER,
    cancel_requested_at TEXT,
    cancel_observed_at TEXT,
    cancel_disposition TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    terminal_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_refinement_invocations_resume
ON refinement_invocations(thought_id,state,updated_at DESC);
CREATE UNIQUE INDEX IF NOT EXISTS one_live_refinement_invocation
ON refinement_invocations(thought_id)
WHERE state IN ('reserved','in_flight','awaiting_projection','review_ready');

CREATE TABLE IF NOT EXISTS refinement_invocation_attempts (
    invocation_id TEXT NOT NULL REFERENCES refinement_invocations(id),
    attempt_ordinal INTEGER NOT NULL CHECK (attempt_ordinal >= 1),
    ask_invocation_id TEXT NOT NULL UNIQUE,
    kernel_operation_id TEXT UNIQUE,
    projection_stage_id TEXT UNIQUE REFERENCES kernel_projection_stages(stage_id),
    ask_result_stage_id TEXT UNIQUE REFERENCES ask_results(projection_stage_id),
    receipt_id TEXT UNIQUE REFERENCES kernel_receipts(receipt_id),
    result_ref TEXT UNIQUE,
    state TEXT NOT NULL CHECK (state IN (
        'reserved','kernel_bound','in_flight','succeeded','failed','refused',
        'cancelled','indeterminate','orphaned_before_dispatch_binding'
    )),
    terminal_code TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    bound_at TEXT,
    terminal_at TEXT,
    PRIMARY KEY (invocation_id,attempt_ordinal),
    UNIQUE (invocation_id,ask_invocation_id)
);

CREATE TABLE IF NOT EXISTS refinement_retry_plans (
    invocation_id TEXT NOT NULL REFERENCES refinement_invocations(id),
    parent_attempt_ordinal INTEGER NOT NULL,
    child_attempt_ordinal INTEGER NOT NULL,
    child_ask_invocation_id TEXT NOT NULL UNIQUE,
    reason TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY(invocation_id,parent_attempt_ordinal),
    UNIQUE(invocation_id,child_attempt_ordinal)
);

CREATE TABLE IF NOT EXISTS refinement_review_results (
    id TEXT PRIMARY KEY,
    invocation_id TEXT NOT NULL UNIQUE REFERENCES refinement_invocations(id),
    attempt_ordinal INTEGER NOT NULL,
    ask_result_stage_id TEXT NOT NULL UNIQUE REFERENCES ask_results(projection_stage_id),
    ask_invocation_id TEXT NOT NULL UNIQUE,
    kernel_operation_id TEXT NOT NULL UNIQUE,
    receipt_id TEXT NOT NULL UNIQUE REFERENCES kernel_receipts(receipt_id),
    result_ref TEXT NOT NULL UNIQUE,
    frozen_aggregate_revision INTEGER NOT NULL,
    frozen_working_revision INTEGER NOT NULL,
    frozen_attachment_revision INTEGER NOT NULL,
    result_sha256 TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (invocation_id,attempt_ordinal)
      REFERENCES refinement_invocation_attempts(invocation_id,attempt_ordinal)
);

-- HS-141-04: one durable owner decision may consume one receipt-gated review.
CREATE TABLE IF NOT EXISTS refinement_review_actions (
    action_id TEXT PRIMARY KEY,
    request_id TEXT NOT NULL UNIQUE,
    request_sha256 TEXT NOT NULL,
    thought_id TEXT NOT NULL REFERENCES refinement_thoughts(id),
    review_result_id TEXT NOT NULL UNIQUE REFERENCES refinement_review_results(id),
    action_kind TEXT NOT NULL CHECK (action_kind IN ('answer','accept','reject')),
    aggregate_revision INTEGER NOT NULL,
    working_revision INTEGER NOT NULL,
    lifecycle_revision INTEGER NOT NULL,
    attachment_revision INTEGER NOT NULL,
    post_aggregate_revision INTEGER NOT NULL,
    post_working_revision INTEGER NOT NULL,
    post_lifecycle_revision INTEGER NOT NULL,
    post_continuity_revision INTEGER NOT NULL DEFAULT 0,
    committed_hub_id TEXT NOT NULL DEFAULT '',
    append_effect_json TEXT NOT NULL DEFAULT '',
    append_effect_sha256 TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);

-- Thought Workbench: hub-local ordering and the atomic answer+next-turn proof.
-- Neither table is part of primitive sync.  The identity is provisioned while
-- schema reconciliation runs, so the read-only Workbench projection never
-- creates authority as a side effect.
CREATE TABLE IF NOT EXISTS refinement_workspace_identity (
    id INTEGER PRIMARY KEY CHECK (id=1),
    hub_id TEXT NOT NULL UNIQUE
);
INSERT OR IGNORE INTO refinement_workspace_identity(id,hub_id)
VALUES(1,'hub_' || lower(hex(randomblob(16))));

CREATE TABLE IF NOT EXISTS refinement_answer_continue_commands (
    command_id TEXT PRIMARY KEY,
    request_sha256 TEXT NOT NULL,
    thought_id TEXT NOT NULL REFERENCES refinement_thoughts(id),
    review_result_id TEXT NOT NULL UNIQUE REFERENCES refinement_review_results(id),
    action_id TEXT NOT NULL UNIQUE REFERENCES refinement_review_actions(action_id),
    child_invocation_id TEXT NOT NULL UNIQUE REFERENCES refinement_invocations(id),
    append_effect_json TEXT NOT NULL,
    post_aggregate_revision INTEGER NOT NULL,
    post_working_revision INTEGER NOT NULL,
    post_continuity_revision INTEGER NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS recipe_results (
    projection_stage_id TEXT PRIMARY KEY REFERENCES kernel_projection_stages(stage_id),
    invocation_id TEXT NOT NULL UNIQUE,
    operation_id TEXT NOT NULL UNIQUE REFERENCES kernel_operations(operation_id),
    receipt_id TEXT NOT NULL UNIQUE REFERENCES kernel_receipts(receipt_id),
    artifact_id TEXT NOT NULL UNIQUE REFERENCES artifacts(id)
);
CREATE TABLE IF NOT EXISTS recipe_chat_results (
    projection_stage_id TEXT PRIMARY KEY REFERENCES kernel_projection_stages(stage_id),
    invocation_id TEXT NOT NULL UNIQUE,
    operation_id TEXT NOT NULL UNIQUE REFERENCES kernel_operations(operation_id),
    receipt_id TEXT NOT NULL UNIQUE REFERENCES kernel_receipts(receipt_id),
    payload_json TEXT NOT NULL,
    created_at REAL NOT NULL
);

-- Phase 124: pipeline observer events. Append-only structured event log
-- for every public service method call.
CREATE TABLE IF NOT EXISTS pipeline_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT NOT NULL UNIQUE,
    timestamp REAL NOT NULL,
    service TEXT NOT NULL,
    method TEXT NOT NULL,
    principal_kind TEXT NOT NULL,
    principal_identity TEXT NOT NULL DEFAULT '',
    args_summary TEXT NOT NULL DEFAULT '{}',
    result_summary TEXT NOT NULL DEFAULT '',
    error TEXT,
    error_code TEXT,
    duration_ms REAL NOT NULL DEFAULT 0,
    correlation_id TEXT NOT NULL DEFAULT '',
    is_async INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_pipeline_events_timestamp
ON pipeline_events(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_pipeline_events_service_method
ON pipeline_events(service, method, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_pipeline_events_principal
ON pipeline_events(principal_kind, principal_identity, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_pipeline_events_correlation
ON pipeline_events(correlation_id)
WHERE correlation_id != '';

-- HS-126-01: persisted, window-keyed Monday briefs. Items are deliberately
-- separate so collectors can add them without changing the brief identity.
CREATE TABLE IF NOT EXISTS monday_briefs (
    id TEXT PRIMARY KEY,
    period_start TEXT NOT NULL,
    period_end TEXT NOT NULL,
    headline TEXT NOT NULL DEFAULT '',
    generated_at TEXT NOT NULL,
    spoken INTEGER NOT NULL DEFAULT 0,
    disposition TEXT
);

CREATE TABLE IF NOT EXISTS monday_brief_items (
    id TEXT PRIMARY KEY,
    brief_id TEXT NOT NULL REFERENCES monday_briefs(id),
    section TEXT NOT NULL,
    text TEXT NOT NULL,
    detail TEXT,
    source_ref TEXT,
    priority INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_monday_brief_items_brief ON monday_brief_items(brief_id);

-- HS-132-08: the brief-item triage shelf. Acknowledge/Defer are owner verbs
-- over a brief item, so they outlive the pullout that pressed them. One row
-- per item; the row's absence is the untouched state.
CREATE TABLE IF NOT EXISTS monday_brief_item_shelf (
    item_id TEXT PRIMARY KEY REFERENCES monday_brief_items(id) ON DELETE CASCADE,
    brief_id TEXT NOT NULL,
    state TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_monday_brief_shelf_brief ON monday_brief_item_shelf(brief_id);

-- v61: services publish typed domain facts into a shared event ledger;
-- Reactions project matching events into one configured Workbench.
CREATE TABLE IF NOT EXISTS connector_watches (
    id TEXT PRIMARY KEY,
    connector_id TEXT NOT NULL,
    query_kind TEXT NOT NULL,
    name TEXT NOT NULL DEFAULT '',
    query_json TEXT NOT NULL DEFAULT '{}',
    snapshot_json TEXT,
    enabled INTEGER NOT NULL DEFAULT 1,
    last_success_at TEXT,
    last_error TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_connector_watches_connector
    ON connector_watches(connector_id, enabled);

CREATE TABLE IF NOT EXISTS service_events (
    id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    event_version INTEGER NOT NULL DEFAULT 1,
    producer TEXT NOT NULL,
    subject_ref TEXT NOT NULL,
    source_revision TEXT NOT NULL DEFAULT '',
    facts_json TEXT NOT NULL DEFAULT '{}',
    refs_json TEXT NOT NULL DEFAULT '[]',
    principal_kind TEXT NOT NULL,
    principal_identity TEXT NOT NULL DEFAULT '',
    correlation_id TEXT NOT NULL DEFAULT '',
    causation_id TEXT NOT NULL DEFAULT '',
    privacy_class TEXT NOT NULL DEFAULT 'private',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_service_events_type
    ON service_events(event_type, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_service_events_correlation
    ON service_events(correlation_id, created_at DESC);

CREATE TABLE IF NOT EXISTS connector_reactions (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL DEFAULT '',
    watch_id TEXT REFERENCES connector_watches(id) ON DELETE CASCADE,
    event_pattern TEXT NOT NULL,
    workbench_id TEXT NOT NULL REFERENCES workbenches(id),
    title_template TEXT NOT NULL DEFAULT '{event_type}: {entity_title}',
    auto_run INTEGER NOT NULL DEFAULT 0,
    enabled INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_connector_reactions_match
    ON connector_reactions(watch_id, event_pattern, enabled);

-- A projection row says only that one event was materialized into one item and,
-- optionally, one kernel operation. Execution outcome belongs to the immutable
-- kernel receipt, never to a second mutable delivery state machine.
CREATE TABLE IF NOT EXISTS reaction_event_projections (
    reaction_id TEXT NOT NULL REFERENCES connector_reactions(id) ON DELETE CASCADE,
    event_id TEXT NOT NULL REFERENCES service_events(id) ON DELETE CASCADE,
    item_id TEXT NOT NULL REFERENCES workbench_items(id),
    operation_id TEXT,
    receipt_id TEXT,
    projected_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (reaction_id, event_id)
);

-- Immutable admitted deployment specifications. ``secret_slot`` identifies a
-- device-local credential lookup location; credentials never enter this table.
CREATE TABLE IF NOT EXISTS deployment_revisions (
    id TEXT PRIMARY KEY,
    schema_version INTEGER NOT NULL DEFAULT 1,
    destination_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    engine TEXT NOT NULL,
    model TEXT NOT NULL,
    node TEXT NOT NULL DEFAULT '',
    boundary TEXT NOT NULL,
    endpoint TEXT NOT NULL DEFAULT '',
    model_path TEXT,
    secret_slot TEXT NOT NULL DEFAULT '',
    runtime_id TEXT NOT NULL DEFAULT '',
    runtime_revision TEXT NOT NULL DEFAULT '',
    artifact_id TEXT NOT NULL DEFAULT '',
    manifest_sha256 TEXT NOT NULL DEFAULT '',
    format TEXT NOT NULL DEFAULT '',
    architecture TEXT NOT NULL DEFAULT '',
    context_ceiling INTEGER NOT NULL DEFAULT 0,
    capability_sha256 TEXT NOT NULL DEFAULT ''
);

-- HS-142-02: installed model bytes and acquisition jobs are hub-local. Public
-- projections never expose either locator; immutable deployment v2 revisions
-- refer to an artifact id and resolve the locator only inside this hub.
CREATE TABLE IF NOT EXISTS inference_model_artifacts (
    artifact_id TEXT PRIMARY KEY,
    format TEXT NOT NULL CHECK (format IN ('gguf','mlx_safetensors')),
    source_kind TEXT NOT NULL,
    source_repository TEXT NOT NULL,
    source_revision TEXT NOT NULL,
    manifest_json TEXT NOT NULL,
    manifest_sha256 TEXT NOT NULL,
    installed_bytes INTEGER NOT NULL CHECK (installed_bytes > 0),
    state TEXT NOT NULL CHECK (state IN ('verified','quarantined','removed')),
    local_locator TEXT NOT NULL,
    created_at TEXT NOT NULL,
    verified_at TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_inference_artifact_manifest
    ON inference_model_artifacts(manifest_sha256) WHERE state='verified';

CREATE TABLE IF NOT EXISTS inference_model_acquisitions (
    job_id TEXT PRIMARY KEY,
    request_id TEXT NOT NULL UNIQUE,
    request_sha256 TEXT NOT NULL,
    preset_id TEXT NOT NULL,
    catalog_revision INTEGER NOT NULL,
    source_plan_json TEXT NOT NULL,
    source_plan_sha256 TEXT NOT NULL,
    source_claim_sha256 TEXT NOT NULL DEFAULT '',
    state TEXT NOT NULL CHECK (state IN ('requested','resolving_source','downloading','verifying','installing','ready','cancelled','failed','indeterminate')),
    verified_bytes INTEGER NOT NULL DEFAULT 0,
    transport_bytes INTEGER NOT NULL DEFAULT 0,
    bytes_total INTEGER NOT NULL,
    artifact_id TEXT,
    activation_state TEXT NOT NULL DEFAULT 'pending' CHECK (activation_state IN ('pending','in_use','failed','not_requested')),
    expected_route_revision TEXT NOT NULL,
    receipt_json TEXT,
    error_code TEXT,
    error_message TEXT,
    resumable INTEGER NOT NULL DEFAULT 0,
    revision INTEGER NOT NULL DEFAULT 1,
    cancel_requested INTEGER NOT NULL DEFAULT 0,
    cancel_request_id TEXT,
    cancel_request_sha256 TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_inference_acquisition_state
    ON inference_model_acquisitions(state, updated_at);

CREATE TABLE IF NOT EXISTS inference_deployments (
    deployment_id TEXT PRIMARY KEY,
    destination_id TEXT NOT NULL,
    runtime_id TEXT NOT NULL,
    runtime_revision TEXT NOT NULL,
    artifact_id TEXT NOT NULL REFERENCES inference_model_artifacts(artifact_id),
    model_identity TEXT NOT NULL,
    context_ceiling INTEGER NOT NULL,
    recommended_context INTEGER NOT NULL,
    capability_json TEXT NOT NULL,
    capability_sha256 TEXT NOT NULL,
    execution_revision_id TEXT NOT NULL REFERENCES deployment_revisions(id),
    configuration_revision INTEGER NOT NULL,
    active INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Phase 143: reusable model identity is deliberately separate from the
-- hub-local facts that make it executable.  These records are not sync
-- primitives: a profile revision never carries a locator, endpoint, secret,
-- or live readiness fact, while a binding references the existing Phase 142
-- deployment head and immutable DeploymentRevision by id only.
CREATE TABLE IF NOT EXISTS model_profile_revisions (
    profile_id TEXT NOT NULL,
    revision INTEGER NOT NULL CHECK (revision > 0),
    sha256 TEXT NOT NULL UNIQUE,
    label TEXT NOT NULL,
    provider_family TEXT NOT NULL,
    runtime_family TEXT NOT NULL,
    model_or_artifact_identity TEXT NOT NULL,
    supported_modalities_json TEXT NOT NULL,
    context_support TEXT NOT NULL CHECK (context_support IN ('exact','bounded','unavailable')),
    tokenizer_template_requirements_json TEXT NOT NULL,
    capability_manifest_json TEXT NOT NULL,
    safe_presentation_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (profile_id, revision)
);

-- Each mutation writes a new immutable binding revision.  The small head row
-- is the single CAS authority for the profile's current binding; it does not
-- recreate a deployment registry or duplicate DeploymentRevision content.
CREATE TABLE IF NOT EXISTS model_profile_binding_revisions (
    binding_id TEXT NOT NULL,
    revision INTEGER NOT NULL CHECK (revision > 0),
    profile_id TEXT NOT NULL,
    profile_revision INTEGER NOT NULL,
    deployment_head_id TEXT NOT NULL,
    deployment_configuration_revision INTEGER NOT NULL,
    deployment_revision_id TEXT NOT NULL REFERENCES deployment_revisions(id),
    secret_slot TEXT NOT NULL DEFAULT '',
    enabled INTEGER NOT NULL CHECK (enabled IN (0,1)),
    readiness_observation_id TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    PRIMARY KEY (binding_id, revision),
    FOREIGN KEY (profile_id, profile_revision)
      REFERENCES model_profile_revisions(profile_id, revision)
);

CREATE TABLE IF NOT EXISTS model_profile_binding_heads (
    binding_id TEXT PRIMARY KEY,
    profile_id TEXT NOT NULL UNIQUE,
    revision INTEGER NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (binding_id, revision)
      REFERENCES model_profile_binding_revisions(binding_id, revision)
);

-- Probe observations are server-minted, hub-local, and pinned to the exact
-- deployment head/configuration/execution revision they observed.  A client
-- may name an observation while binding, but can never manufacture it.
CREATE TABLE IF NOT EXISTS model_profile_readiness_observations (
    observation_id TEXT PRIMARY KEY,
    deployment_head_id TEXT NOT NULL,
    deployment_configuration_revision INTEGER NOT NULL,
    deployment_revision_id TEXT NOT NULL REFERENCES deployment_revisions(id),
    state TEXT NOT NULL CHECK (state IN ('ready','unavailable')),
    reason_code TEXT NOT NULL,
    observed_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_model_profile_readiness_head
    ON model_profile_readiness_observations(
        deployment_head_id, deployment_configuration_revision, deployment_revision_id
    );

-- Deletion is a hub-local tombstone.  Historical revision/binding evidence is
-- retained for receipts and future frozen-plan inspection; it is never synced.
CREATE TABLE IF NOT EXISTS model_profile_tombstones (
    profile_id TEXT PRIMARY KEY,
    deleted_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_model_profile_binding_profile
    ON model_profile_binding_revisions(profile_id, profile_revision, revision DESC);

-- HS-143-04: sparse, hub-local capability assignment authority.  Revisions
-- are immutable; one narrow head row is the only mutable pointer.  Entries
-- are normalized so profile deletion can name exact dependent assignments
-- without searching JSON blobs.
CREATE TABLE IF NOT EXISTS inference_assignment_revisions (
    assignment_id TEXT NOT NULL,
    revision INTEGER NOT NULL,
    assignment_key TEXT NOT NULL,
    scope_kind TEXT NOT NULL CHECK (scope_kind IN ('invocation','subject','global')),
    scope_id TEXT NOT NULL DEFAULT '',
    subject_kind TEXT NOT NULL DEFAULT '',
    selector_kind TEXT NOT NULL CHECK (selector_kind IN ('capability','group','global')),
    capability_id TEXT NOT NULL DEFAULT '',
    group_id TEXT NOT NULL DEFAULT '',
    retry_policy_id TEXT,
    payload_json TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    created_at TEXT NOT NULL,
    CHECK (
      (scope_kind='global' AND scope_id='' AND subject_kind='') OR
      (scope_kind='invocation' AND scope_id<>'' AND subject_kind='') OR
      (scope_kind='subject' AND scope_id<>'' AND subject_kind IN ('thought','workbench','agent','recipe','project'))
    ),
    CHECK (
      (selector_kind='global' AND capability_id='' AND group_id='') OR
      (selector_kind='capability' AND capability_id<>'' AND group_id='') OR
      (selector_kind='group' AND capability_id='' AND group_id<>'')
    ),
    CHECK (
      (scope_kind IN ('invocation','subject') AND selector_kind='capability') OR
      (scope_kind='global' AND selector_kind IN ('global','group','capability'))
    ),
    PRIMARY KEY (assignment_id, revision),
    UNIQUE (assignment_key, revision)
);
CREATE TABLE IF NOT EXISTS inference_assignment_heads (
    assignment_key TEXT PRIMARY KEY,
    assignment_id TEXT NOT NULL,
    revision INTEGER NOT NULL,
    cleared INTEGER NOT NULL DEFAULT 0 CHECK (cleared IN (0,1)),
    updated_at TEXT NOT NULL,
    FOREIGN KEY (assignment_id, revision)
      REFERENCES inference_assignment_revisions(assignment_id, revision)
);
CREATE TABLE IF NOT EXISTS inference_assignments (
    id TEXT PRIMARY KEY,
    assignment_id TEXT NOT NULL,
    assignment_revision INTEGER NOT NULL,
    profile_id TEXT NOT NULL,
    profile_revision INTEGER NOT NULL,
    profile_schema_version INTEGER NOT NULL DEFAULT 2 CHECK (profile_schema_version IN (1,2)),
    ordinal INTEGER NOT NULL CHECK (ordinal BETWEEN 1 AND 4),
    UNIQUE (assignment_id, assignment_revision, ordinal),
    FOREIGN KEY (assignment_id, assignment_revision)
      REFERENCES inference_assignment_revisions(assignment_id, revision)
);
CREATE INDEX IF NOT EXISTS idx_inference_assignments_profile
    ON inference_assignments(profile_id, profile_revision);
CREATE TABLE IF NOT EXISTS inference_assignment_commands (
    command_id TEXT PRIMARY KEY,
    request_sha256 TEXT NOT NULL,
    response_json TEXT NOT NULL,
    response_sha256 TEXT NOT NULL,
    resolution_context_json TEXT NOT NULL,
    resolution_context_sha256 TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS inference_assignment_migrations (
    family TEXT PRIMARY KEY,
    marker_revision INTEGER NOT NULL,
    source_sha256 TEXT NOT NULL,
    result_json TEXT NOT NULL,
    result_sha256 TEXT NOT NULL,
    committed_at TEXT NOT NULL
);

-- HS-143-05: immutable, content-free routing evidence.  Resolution happens
-- from one SQLite snapshot before these rows are written; execution and
-- fallback never consult mutable assignment/profile heads again.
CREATE TABLE IF NOT EXISTS inference_route_plans (
    id TEXT PRIMARY KEY,
    sha256 TEXT NOT NULL UNIQUE,
    capability_id TEXT NOT NULL,
    capability_revision INTEGER NOT NULL CHECK (capability_revision > 0),
    capability_schema_sha256 TEXT NOT NULL,
    assignment_id TEXT NOT NULL,
    assignment_revision INTEGER NOT NULL CHECK (assignment_revision > 0),
    assignment_sha256 TEXT NOT NULL,
    inherited_from TEXT NOT NULL CHECK (inherited_from IN ('invocation','subject','capability','group','global','legacy_override')),
    retry_policy_id TEXT NOT NULL,
    retry_policy_revision INTEGER NOT NULL CHECK (retry_policy_revision > 0),
    operation_policy_revision TEXT NOT NULL,
    principal_policy_sha256 TEXT,
    payload_json TEXT NOT NULL,
    state TEXT NOT NULL DEFAULT 'frozen' CHECK (state='frozen'),
    deadline_at TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS inference_route_plan_entries (
    id TEXT PRIMARY KEY,
    plan_id TEXT NOT NULL REFERENCES inference_route_plans(id),
    route_leg_ordinal INTEGER NOT NULL CHECK (route_leg_ordinal BETWEEN 1 AND 4),
    profile_id TEXT NOT NULL,
    profile_revision INTEGER NOT NULL CHECK (profile_revision > 0),
    profile_schema_version INTEGER NOT NULL CHECK (profile_schema_version IN (1,2)),
    binding_id TEXT NOT NULL,
    binding_revision INTEGER NOT NULL CHECK (binding_revision > 0),
    deployment_head_id TEXT NOT NULL,
    deployment_configuration_revision INTEGER NOT NULL CHECK (deployment_configuration_revision > 0),
    deployment_revision_id TEXT NOT NULL,
    capability_manifest_sha256 TEXT NOT NULL,
    boundary TEXT NOT NULL CHECK (boundary IN ('local','private_network','mesh','cloud')),
    context_support_json TEXT NOT NULL,
    UNIQUE (plan_id, route_leg_ordinal)
);
CREATE INDEX IF NOT EXISTS idx_inference_route_plan_entries_profile
    ON inference_route_plan_entries(profile_id, profile_revision);
CREATE TABLE IF NOT EXISTS inference_route_plan_commands (
    command_id TEXT PRIMARY KEY,
    request_sha256 TEXT NOT NULL,
    plan_id TEXT NOT NULL REFERENCES inference_route_plans(id),
    plan_sha256 TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS inference_route_plan_commands_no_update
BEFORE UPDATE ON inference_route_plan_commands BEGIN
    SELECT RAISE(ABORT, 'immutable inference route command');
END;
CREATE TRIGGER IF NOT EXISTS inference_route_plan_commands_no_delete
BEFORE DELETE ON inference_route_plan_commands BEGIN
    SELECT RAISE(ABORT, 'immutable inference route command');
END;
CREATE TABLE IF NOT EXISTS inference_route_plan_authority_evidence (
    plan_id TEXT PRIMARY KEY REFERENCES inference_route_plans(id),
    capability_definition_json TEXT NOT NULL,
    capability_definition_sha256 TEXT NOT NULL,
    retry_policy_definition_json TEXT NOT NULL,
    retry_policy_definition_sha256 TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS inference_route_plan_authority_no_update
BEFORE UPDATE ON inference_route_plan_authority_evidence BEGIN
    SELECT RAISE(ABORT, 'immutable inference route authority evidence');
END;
CREATE TRIGGER IF NOT EXISTS inference_route_plan_authority_no_delete
BEFORE DELETE ON inference_route_plan_authority_evidence BEGIN
    SELECT RAISE(ABORT, 'immutable inference route authority evidence');
END;
CREATE TABLE IF NOT EXISTS inference_route_plan_principal_evidence (
    plan_id TEXT PRIMARY KEY REFERENCES inference_route_plans(id),
    payload_json TEXT NOT NULL,
    sha256 TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS inference_route_plan_principal_evidence_no_update
BEFORE UPDATE ON inference_route_plan_principal_evidence BEGIN
    SELECT RAISE(ABORT, 'immutable inference route principal evidence');
END;
CREATE TRIGGER IF NOT EXISTS inference_route_plan_principal_evidence_no_delete
BEFORE DELETE ON inference_route_plan_principal_evidence BEGIN
    SELECT RAISE(ABORT, 'immutable inference route principal evidence');
END;
CREATE TABLE IF NOT EXISTS inference_route_plan_preflight_evidence (
    plan_id TEXT NOT NULL REFERENCES inference_route_plans(id),
    route_leg_ordinal INTEGER NOT NULL CHECK (route_leg_ordinal BETWEEN 1 AND 4),
    eligibility TEXT NOT NULL CHECK (eligibility IN ('executable','known_preflight_unavailable')),
    reason_code TEXT,
    PRIMARY KEY (plan_id, route_leg_ordinal)
);
CREATE TRIGGER IF NOT EXISTS inference_route_plan_preflight_no_update
BEFORE UPDATE ON inference_route_plan_preflight_evidence BEGIN
    SELECT RAISE(ABORT, 'immutable inference route preflight evidence');
END;
CREATE TRIGGER IF NOT EXISTS inference_route_plan_preflight_no_delete
BEFORE DELETE ON inference_route_plan_preflight_evidence BEGIN
    SELECT RAISE(ABORT, 'immutable inference route preflight evidence');
END;

-- Private request planning retains hashes and frozen per-leg eligibility, not
-- owner material.  Story 06 consumes these rows but owns controller advance.
CREATE TABLE IF NOT EXISTS inference_operation_route_request_plans (
    id TEXT PRIMARY KEY,
    sha256 TEXT NOT NULL UNIQUE,
    route_plan_id TEXT NOT NULL REFERENCES inference_route_plans(id),
    operation_id TEXT NOT NULL,
    evidence_provider_id TEXT NOT NULL,
    evidence_provider_revision INTEGER NOT NULL CHECK (evidence_provider_revision > 0),
    planning_reference TEXT NOT NULL,
    admission_evidence_ref TEXT NOT NULL,
    admission_evidence_sha256 TEXT NOT NULL,
    material_snapshot_sha256 TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    deadline_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS inference_operation_route_request_plan_entries (
    id TEXT PRIMARY KEY,
    operation_plan_id TEXT NOT NULL REFERENCES inference_operation_route_request_plans(id),
    route_leg_ordinal INTEGER NOT NULL CHECK (route_leg_ordinal BETWEEN 1 AND 4),
    eligibility TEXT NOT NULL CHECK (eligibility IN ('executable','known_preflight_unavailable','known_context_overflow')),
    reason_code TEXT,
    admitted_request_id TEXT,
    admitted_request_sha256 TEXT,
    context_plan_sha256 TEXT,
    serialized_request_sha256 TEXT,
    CHECK (
      (eligibility='executable' AND reason_code IS NULL AND admitted_request_id IS NOT NULL AND admitted_request_sha256 IS NOT NULL AND context_plan_sha256 IS NOT NULL AND serialized_request_sha256 IS NOT NULL) OR
      (eligibility<>'executable' AND reason_code IS NOT NULL AND admitted_request_id IS NULL AND admitted_request_sha256 IS NULL AND context_plan_sha256 IS NULL AND serialized_request_sha256 IS NULL)
    ),
    UNIQUE (operation_plan_id, route_leg_ordinal)
);
CREATE TABLE IF NOT EXISTS inference_operation_route_request_plan_commands (
    command_id TEXT PRIMARY KEY,
    request_sha256 TEXT NOT NULL,
    route_plan_id TEXT NOT NULL REFERENCES inference_route_plans(id),
    route_plan_sha256 TEXT NOT NULL,
    operation_plan_id TEXT NOT NULL REFERENCES inference_operation_route_request_plans(id),
    operation_plan_sha256 TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS inference_operation_route_commands_no_update
BEFORE UPDATE ON inference_operation_route_request_plan_commands BEGIN
    SELECT RAISE(ABORT, 'immutable operation route command');
END;
CREATE TRIGGER IF NOT EXISTS inference_operation_route_commands_no_delete
BEFORE DELETE ON inference_operation_route_request_plan_commands BEGIN
    SELECT RAISE(ABORT, 'immutable operation route command');
END;
CREATE UNIQUE INDEX IF NOT EXISTS idx_inference_operation_route_request_operation
    ON inference_operation_route_request_plans(operation_id);
CREATE TABLE IF NOT EXISTS inference_operation_route_attempt_budget_evidence (
    operation_plan_id TEXT PRIMARY KEY REFERENCES inference_operation_route_request_plans(id),
    provider_id TEXT NOT NULL,
    provider_revision INTEGER NOT NULL CHECK (provider_revision > 0),
    evidence_ref TEXT NOT NULL,
    material_snapshot_sha256 TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    sha256 TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS inference_operation_route_attempt_budgets_no_update
BEFORE UPDATE ON inference_operation_route_attempt_budget_evidence BEGIN
    SELECT RAISE(ABORT, 'immutable operation route attempt budgets');
END;
CREATE TRIGGER IF NOT EXISTS inference_operation_route_attempt_budgets_no_delete
BEFORE DELETE ON inference_operation_route_attempt_budget_evidence BEGIN
    SELECT RAISE(ABORT, 'immutable operation route attempt budgets');
END;

-- HS-143-07: application-owned private material and exact per-leg request
-- serialization. These rows are local-only and immutable: route planning may
-- reconstruct their hashes, but sync and public route receipts never expose
-- prompt/context bytes.
CREATE TABLE IF NOT EXISTS inference_adoption_material_snapshots (
    planning_reference TEXT PRIMARY KEY,
    capability_id TEXT NOT NULL,
    operation_id TEXT NOT NULL UNIQUE,
    contract TEXT NOT NULL,
    contract_revision TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    payload_sha256 TEXT NOT NULL,
    material_snapshot_sha256 TEXT NOT NULL UNIQUE,
    reserved_output_tokens INTEGER NOT NULL CHECK (reserved_output_tokens >= 0),
    reserved_tool_calls INTEGER NOT NULL CHECK (reserved_tool_calls >= 0),
    created_at TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS inference_adoption_material_no_update
BEFORE UPDATE ON inference_adoption_material_snapshots BEGIN
    SELECT RAISE(ABORT, 'immutable inference adoption material');
END;
CREATE TRIGGER IF NOT EXISTS inference_adoption_material_no_delete
BEFORE DELETE ON inference_adoption_material_snapshots BEGIN
    SELECT RAISE(ABORT, 'immutable inference adoption material');
END;
CREATE TABLE IF NOT EXISTS inference_adoption_route_evidence (
    evidence_ref TEXT PRIMARY KEY,
    planning_reference TEXT NOT NULL UNIQUE
        REFERENCES inference_adoption_material_snapshots(planning_reference),
    operation_id TEXT NOT NULL UNIQUE,
    capability_id TEXT NOT NULL,
    material_snapshot_sha256 TEXT NOT NULL,
    evidence_json TEXT NOT NULL,
    evidence_sha256 TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS inference_adoption_route_evidence_no_update
BEFORE UPDATE ON inference_adoption_route_evidence BEGIN
    SELECT RAISE(ABORT, 'immutable inference adoption route evidence');
END;
CREATE TRIGGER IF NOT EXISTS inference_adoption_route_evidence_no_delete
BEFORE DELETE ON inference_adoption_route_evidence BEGIN
    SELECT RAISE(ABORT, 'immutable inference adoption route evidence');
END;
CREATE TABLE IF NOT EXISTS inference_adoption_composites (
    composite_id TEXT PRIMARY KEY,
    command_id TEXT NOT NULL UNIQUE,
    request_sha256 TEXT NOT NULL,
    operation_plan_ids_json TEXT NOT NULL,
    result_sha256 TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS inference_adoption_composites_no_update
BEFORE UPDATE ON inference_adoption_composites BEGIN
    SELECT RAISE(ABORT, 'immutable inference adoption composite');
END;
CREATE TRIGGER IF NOT EXISTS inference_adoption_composites_no_delete
BEFORE DELETE ON inference_adoption_composites BEGIN
    SELECT RAISE(ABORT, 'immutable inference adoption composite');
END;
CREATE TABLE IF NOT EXISTS inference_adoption_attempt_results (
    attempt_id TEXT PRIMARY KEY,
    child_invocation_id TEXT NOT NULL UNIQUE,
    producer_result_ref TEXT NOT NULL UNIQUE,
    result_json TEXT NOT NULL,
    result_sha256 TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS inference_adoption_attempt_results_no_update
BEFORE UPDATE ON inference_adoption_attempt_results BEGIN
    SELECT RAISE(ABORT, 'immutable inference adoption attempt result');
END;
CREATE TRIGGER IF NOT EXISTS inference_adoption_attempt_results_no_delete
BEFORE DELETE ON inference_adoption_attempt_results BEGIN
    SELECT RAISE(ABORT, 'immutable inference adoption attempt result');
END;

-- HS-143-06: one durable fallback-controller state machine above the physical
-- inference waist.  A row is the terminal-election authority for one frozen
-- operation request plan; attempts are reservations, not provider retries.
CREATE TABLE IF NOT EXISTS inference_route_executions (
    id TEXT PRIMARY KEY,
    route_plan_id TEXT NOT NULL REFERENCES inference_route_plans(id),
    route_plan_sha256 TEXT NOT NULL,
    operation_plan_id TEXT NOT NULL UNIQUE REFERENCES inference_operation_route_request_plans(id),
    operation_plan_sha256 TEXT NOT NULL,
    budget_evidence_provider_id TEXT NOT NULL,
    budget_evidence_provider_revision INTEGER NOT NULL CHECK (budget_evidence_provider_revision > 0),
    budget_evidence_sha256 TEXT NOT NULL,
    state TEXT NOT NULL CHECK (state IN ('active','stopping','stopped','terminal')),
    revision INTEGER NOT NULL CHECK (revision > 0),
    total_attempt_limit INTEGER NOT NULL CHECK (total_attempt_limit > 0),
    per_leg_attempt_limit INTEGER NOT NULL CHECK (per_leg_attempt_limit > 0),
    attempts_reserved INTEGER NOT NULL DEFAULT 0 CHECK (attempts_reserved >= 0),
    token_budget INTEGER,
    cost_budget INTEGER,
    tool_call_budget INTEGER,
    tokens_reserved INTEGER NOT NULL DEFAULT 0 CHECK (tokens_reserved >= 0),
    cost_reserved INTEGER NOT NULL DEFAULT 0 CHECK (cost_reserved >= 0),
    tool_calls_reserved INTEGER NOT NULL DEFAULT 0 CHECK (tool_calls_reserved >= 0),
    stop_requested INTEGER NOT NULL DEFAULT 0 CHECK (stop_requested IN (0,1)),
    stop_command_id TEXT UNIQUE,
    terminal_disposition TEXT CHECK (terminal_disposition IS NULL OR terminal_disposition IN ('preflight_unavailable','known_no_generation_transient','dispatch_outcome_unknown','provider_permanent','invalid_typed_output','invalid_tool_call','context_overflow','local_capacity_unavailable','tool_unavailable_or_stale','permission_denied','policy_refused','owner_cancelled','deadline_exhausted','physical_outcome_unknown','effect_indeterminate','owner_terminal')),
    terminal_outcome TEXT CHECK (terminal_outcome IS NULL OR terminal_outcome IN ('succeeded','failed','refused','cancelled','indeterminate')),
    result_ref TEXT,
    winning_attempt_id TEXT,
    started_at TEXT NOT NULL,
    terminal_at TEXT,
    CHECK (
      (state='active' AND stop_requested=0 AND stop_command_id IS NULL AND terminal_disposition IS NULL AND terminal_outcome IS NULL AND winning_attempt_id IS NULL AND terminal_at IS NULL) OR
      (state='stopping' AND stop_requested=1 AND stop_command_id IS NOT NULL AND terminal_disposition IS NULL AND terminal_outcome IS NULL AND winning_attempt_id IS NULL AND terminal_at IS NULL) OR
      (state='stopped' AND stop_requested=1 AND stop_command_id IS NOT NULL AND terminal_disposition='owner_cancelled' AND terminal_outcome='cancelled' AND winning_attempt_id IS NULL AND terminal_at IS NOT NULL) OR
      (state='terminal' AND terminal_outcome IS NOT NULL AND terminal_at IS NOT NULL)
    ),
    CHECK (
      terminal_outcome<>'succeeded' OR
      (winning_attempt_id IS NOT NULL AND result_ref IS NOT NULL AND result_ref<>'')
    )
);
CREATE TRIGGER IF NOT EXISTS inference_route_execution_stop_provenance_immutable
BEFORE UPDATE ON inference_route_executions
WHEN OLD.stop_command_id IS NOT NULL AND NEW.stop_command_id IS NOT OLD.stop_command_id
BEGIN
    SELECT RAISE(ABORT, 'immutable inference route Stop provenance');
END;
CREATE TABLE IF NOT EXISTS inference_route_attempts (
    id TEXT PRIMARY KEY,
    execution_id TEXT NOT NULL REFERENCES inference_route_executions(id),
    route_leg_ordinal INTEGER NOT NULL CHECK (route_leg_ordinal BETWEEN 1 AND 4),
    physical_attempt_ordinal INTEGER NOT NULL CHECK (physical_attempt_ordinal > 0),
    leg_attempt_ordinal INTEGER NOT NULL CHECK (leg_attempt_ordinal > 0),
    purpose TEXT NOT NULL CHECK (purpose IN ('primary','retry','fallback','compatibility')),
    deployment_revision_id TEXT NOT NULL,
    boundary TEXT NOT NULL CHECK (boundary IN ('local','private_network','mesh','cloud')),
    state TEXT NOT NULL CHECK (state IN ('reserved','admitted','dispatch_intent','terminal')),
    child_invocation_id TEXT NOT NULL UNIQUE,
    reservation_command_id TEXT NOT NULL UNIQUE,
    admission_nonce_sha256 TEXT NOT NULL,
    budget_evidence_provider_id TEXT NOT NULL,
    budget_evidence_provider_revision INTEGER NOT NULL CHECK (budget_evidence_provider_revision > 0),
    budget_evidence_sha256 TEXT NOT NULL,
    child_operation_id TEXT UNIQUE,
    disposition TEXT CHECK (disposition IS NULL OR disposition IN ('preflight_unavailable','known_no_generation_transient','dispatch_outcome_unknown','provider_permanent','invalid_typed_output','invalid_tool_call','context_overflow','local_capacity_unavailable','tool_unavailable_or_stale','permission_denied','policy_refused','owner_cancelled','deadline_exhausted','physical_outcome_unknown','effect_indeterminate','owner_terminal')),
    outcome TEXT CHECK (outcome IS NULL OR outcome IN ('succeeded','failed','refused','cancelled','indeterminate')),
    result_ref TEXT,
    child_receipt_sha256 TEXT,
    disposition_evidence_json TEXT,
    disposition_evidence_sha256 TEXT,
    classifier_revision TEXT,
    send_phase TEXT CHECK (send_phase IS NULL OR send_phase IN ('pre_send','dispatch_intent','provider_no_generation','provider_returned')),
    reserved_token_budget INTEGER NOT NULL DEFAULT 0 CHECK (reserved_token_budget >= 0),
    reserved_cost_budget INTEGER NOT NULL DEFAULT 0 CHECK (reserved_cost_budget >= 0),
    reserved_tool_call_budget INTEGER NOT NULL DEFAULT 0 CHECK (reserved_tool_call_budget >= 0),
    reserved_at TEXT NOT NULL,
    admitted_at TEXT,
    dispatch_intent_at TEXT,
    terminal_at TEXT,
    CHECK (
      (state='terminal' AND disposition IS NOT NULL AND outcome IS NOT NULL
       AND disposition_evidence_sha256 IS NOT NULL AND terminal_at IS NOT NULL
       AND (
         child_receipt_sha256 IS NOT NULL OR
         (disposition='dispatch_outcome_unknown' AND outcome='indeterminate'
          AND send_phase='dispatch_intent')
       )) OR
      (state<>'terminal' AND disposition IS NULL AND outcome IS NULL
       AND child_receipt_sha256 IS NULL AND disposition_evidence_sha256 IS NULL
       AND classifier_revision IS NULL AND send_phase IS NULL AND terminal_at IS NULL)
    ),
    UNIQUE (execution_id, physical_attempt_ordinal),
    UNIQUE (execution_id, route_leg_ordinal, leg_attempt_ordinal)
);
CREATE INDEX IF NOT EXISTS idx_inference_route_attempts_execution
    ON inference_route_attempts(execution_id, physical_attempt_ordinal);
CREATE TRIGGER IF NOT EXISTS inference_route_attempt_authority_immutable
BEFORE UPDATE ON inference_route_attempts
WHEN NEW.execution_id IS NOT OLD.execution_id
  OR NEW.route_leg_ordinal IS NOT OLD.route_leg_ordinal
  OR NEW.physical_attempt_ordinal IS NOT OLD.physical_attempt_ordinal
  OR NEW.leg_attempt_ordinal IS NOT OLD.leg_attempt_ordinal
  OR NEW.purpose IS NOT OLD.purpose
  OR NEW.deployment_revision_id IS NOT OLD.deployment_revision_id
  OR NEW.boundary IS NOT OLD.boundary
  OR NEW.child_invocation_id IS NOT OLD.child_invocation_id
  OR NEW.reservation_command_id IS NOT OLD.reservation_command_id
  OR NEW.admission_nonce_sha256 IS NOT OLD.admission_nonce_sha256
  OR NEW.budget_evidence_provider_id IS NOT OLD.budget_evidence_provider_id
  OR NEW.budget_evidence_provider_revision IS NOT OLD.budget_evidence_provider_revision
  OR NEW.budget_evidence_sha256 IS NOT OLD.budget_evidence_sha256
  OR NEW.reserved_token_budget IS NOT OLD.reserved_token_budget
  OR NEW.reserved_cost_budget IS NOT OLD.reserved_cost_budget
  OR NEW.reserved_tool_call_budget IS NOT OLD.reserved_tool_call_budget
BEGIN
    SELECT RAISE(ABORT, 'immutable inference route attempt authority');
END;
CREATE TRIGGER IF NOT EXISTS inference_route_attempt_terminal_immutable
BEFORE UPDATE ON inference_route_attempts
WHEN OLD.state='terminal'
BEGIN
    SELECT RAISE(ABORT, 'immutable terminal inference route attempt');
END;
CREATE TABLE IF NOT EXISTS inference_route_execution_skips (
    id TEXT PRIMARY KEY,
    execution_id TEXT NOT NULL REFERENCES inference_route_executions(id),
    route_leg_ordinal INTEGER NOT NULL CHECK (route_leg_ordinal BETWEEN 1 AND 4),
    disposition TEXT NOT NULL CHECK (disposition IN ('preflight_unavailable','context_overflow')),
    reason_code TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE (execution_id, route_leg_ordinal)
);
CREATE TRIGGER IF NOT EXISTS inference_route_execution_skips_no_update
BEFORE UPDATE ON inference_route_execution_skips BEGIN
    SELECT RAISE(ABORT, 'immutable inference route execution skip');
END;
CREATE TRIGGER IF NOT EXISTS inference_route_execution_skips_no_delete
BEFORE DELETE ON inference_route_execution_skips BEGIN
    SELECT RAISE(ABORT, 'immutable inference route execution skip');
END;
CREATE TABLE IF NOT EXISTS inference_route_execution_commands (
    command_id TEXT PRIMARY KEY,
    action TEXT NOT NULL CHECK (action IN ('start','reserve','claim','bind','dispatch_intent','settle','stop','reconcile')),
    request_sha256 TEXT NOT NULL,
    execution_id TEXT NOT NULL REFERENCES inference_route_executions(id),
    effect_json TEXT NOT NULL,
    effect_sha256 TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS inference_route_execution_commands_no_update
BEFORE UPDATE ON inference_route_execution_commands BEGIN
    SELECT RAISE(ABORT, 'immutable inference route execution command');
END;
CREATE TRIGGER IF NOT EXISTS inference_route_execution_commands_no_delete
BEFORE DELETE ON inference_route_execution_commands BEGIN
    SELECT RAISE(ABORT, 'immutable inference route execution command');
END;
CREATE TABLE IF NOT EXISTS inference_route_execution_transitions (
    transition_id TEXT PRIMARY KEY,
    execution_id TEXT NOT NULL REFERENCES inference_route_executions(id),
    ordinal INTEGER NOT NULL CHECK (ordinal > 0),
    action TEXT NOT NULL CHECK (action IN ('start','reserve','stop','settle','reconcile')),
    command_id TEXT NOT NULL UNIQUE REFERENCES inference_route_execution_commands(command_id),
    prior_revision INTEGER NOT NULL CHECK (prior_revision >= 0),
    post_revision INTEGER NOT NULL CHECK (post_revision > 0),
    prior_state TEXT NOT NULL CHECK (prior_state IN ('none','active','stopping','stopped','terminal')),
    post_state TEXT NOT NULL CHECK (post_state IN ('active','stopping','stopped','terminal')),
    effect_sha256 TEXT NOT NULL,
    previous_sha256 TEXT NOT NULL,
    sha256 TEXT NOT NULL UNIQUE,
    UNIQUE (execution_id, ordinal),
    UNIQUE (execution_id, post_revision)
);
CREATE TRIGGER IF NOT EXISTS inference_route_execution_transitions_no_update
BEFORE UPDATE ON inference_route_execution_transitions BEGIN
    SELECT RAISE(ABORT, 'immutable inference route execution transition');
END;
CREATE TRIGGER IF NOT EXISTS inference_route_execution_transitions_no_delete
BEFORE DELETE ON inference_route_execution_transitions BEGIN
    SELECT RAISE(ABORT, 'immutable inference route execution transition');
END;

CREATE TABLE IF NOT EXISTS inference_runtime_leases (
    lease_id TEXT PRIMARY KEY,
    operation_id TEXT NOT NULL UNIQUE,
    deployment_revision_id TEXT NOT NULL,
    state TEXT NOT NULL CHECK (state IN ('active','released','expired','indeterminate')),
    process_id TEXT NOT NULL,
    expires_at REAL NOT NULL,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_inference_one_local_lease
    ON inference_runtime_leases(state) WHERE state='active';

-- HS-131-04: the graph/sequence controller is durable independently of its
-- admitted children.  The JSON fields are canonical snapshots, never a
-- transport capability or provider secret.
CREATE TABLE IF NOT EXISTS kernel_parent_runs (
    operation_id TEXT PRIMARY KEY REFERENCES kernel_operations(operation_id),
    native_id TEXT NOT NULL UNIQUE,
    kind TEXT NOT NULL CHECK (kind IN ('sequence','workflow','workbench','decision.promotion-draft','delivery.pr-review-draft','voice_reference_resolve','meeting.session','meeting.deferred-intel-job','dictation.session','wake.session','cadence.next-action-draft')),
    definition_ref TEXT NOT NULL,
    definition_revision TEXT NOT NULL,
    input_json TEXT NOT NULL,
    deadline_at REAL NOT NULL,
    execution_epoch INTEGER NOT NULL DEFAULT 1,
    planned_node TEXT NOT NULL DEFAULT '',
    active_child_invocation_id TEXT NOT NULL DEFAULT '',
    child_budget INTEGER NOT NULL,
    children_json TEXT NOT NULL DEFAULT '[]',
    state TEXT NOT NULL CHECK (state IN ('OPEN','CANCELLING','SUCCEEDED','FAILED','CANCELLED','REFUSED','INDETERMINATE')),
    lease_process_id TEXT NOT NULL DEFAULT '',
    lease_heartbeat_at REAL,
    publication_claim_id TEXT NOT NULL DEFAULT '',
    publication_claimed_at REAL,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_kernel_parent_runs_state ON kernel_parent_runs(state, updated_at);

-- HS-143-08: one parent and its declared inference route set.  The manifest is
-- content-free and immutable; child operation material is frozen only when a
-- real window/stage exists.
CREATE TABLE IF NOT EXISTS inference_parent_route_bundles (
    id TEXT PRIMARY KEY,
    command_id TEXT NOT NULL UNIQUE,
    request_sha256 TEXT NOT NULL,
    parent_operation_id TEXT NOT NULL UNIQUE REFERENCES kernel_parent_runs(operation_id),
    parent_deadline_at REAL NOT NULL,
    parent_child_budget INTEGER NOT NULL CHECK (parent_child_budget > 0),
    lifecycle_child_budget INTEGER NOT NULL CHECK (lifecycle_child_budget >= 0),
    feature_principal_sha256 TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    sha256 TEXT NOT NULL UNIQUE,
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS inference_parent_route_bundle_members (
    id TEXT PRIMARY KEY,
    bundle_id TEXT NOT NULL REFERENCES inference_parent_route_bundles(id),
    ordinal INTEGER NOT NULL CHECK (ordinal > 0),
    route_key TEXT NOT NULL,
    capability_id TEXT NOT NULL,
    route_plan_id TEXT NOT NULL UNIQUE REFERENCES inference_route_plans(id),
    route_plan_sha256 TEXT NOT NULL,
    principal_policy_sha256 TEXT NOT NULL,
    maximum_physical_attempts INTEGER NOT NULL CHECK (maximum_physical_attempts > 0),
    UNIQUE(bundle_id, ordinal),
    UNIQUE(bundle_id, route_key),
    UNIQUE(bundle_id, capability_id)
);
CREATE TRIGGER IF NOT EXISTS inference_parent_route_bundles_no_update
BEFORE UPDATE ON inference_parent_route_bundles BEGIN
    SELECT RAISE(ABORT, 'immutable inference parent route bundle');
END;
CREATE TRIGGER IF NOT EXISTS inference_parent_route_bundles_no_delete
BEFORE DELETE ON inference_parent_route_bundles BEGIN
    SELECT RAISE(ABORT, 'immutable inference parent route bundle');
END;
CREATE TRIGGER IF NOT EXISTS inference_parent_route_bundle_members_no_update
BEFORE UPDATE ON inference_parent_route_bundle_members BEGIN
    SELECT RAISE(ABORT, 'immutable inference parent route bundle member');
END;
CREATE TRIGGER IF NOT EXISTS inference_parent_route_bundle_members_no_delete
BEFORE DELETE ON inference_parent_route_bundle_members BEGIN
    SELECT RAISE(ABORT, 'immutable inference parent route bundle member');
END;

-- A durable Stop election can fence every exact active route before Meeting
-- enqueues displaced work.  Story 08's entrance cutover will attach the queue
-- effect; this tranche establishes the replay-safe authority and membership.
CREATE TABLE IF NOT EXISTS inference_parent_stop_handoffs (
    command_id TEXT PRIMARY KEY,
    request_sha256 TEXT NOT NULL,
    bundle_id TEXT NOT NULL REFERENCES inference_parent_route_bundles(id),
    parent_operation_id TEXT NOT NULL UNIQUE REFERENCES kernel_parent_runs(operation_id),
    evidence_provider_id TEXT NOT NULL,
    evidence_provider_revision INTEGER NOT NULL CHECK (evidence_provider_revision > 0),
    planning_reference TEXT NOT NULL,
    evidence_ref TEXT NOT NULL,
    evidence_sha256 TEXT NOT NULL,
    state TEXT NOT NULL CHECK (state IN ('committed','pending_physical_settlement')),
    effect_json TEXT NOT NULL,
    effect_sha256 TEXT NOT NULL,
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS inference_parent_stop_handoff_executions (
    command_id TEXT NOT NULL REFERENCES inference_parent_stop_handoffs(command_id),
    ordinal INTEGER NOT NULL CHECK (ordinal > 0),
    execution_id TEXT NOT NULL REFERENCES inference_route_executions(id),
    stop_command_id TEXT NOT NULL UNIQUE REFERENCES inference_route_execution_commands(command_id),
    elected_state TEXT NOT NULL CHECK (elected_state IN ('stopping','stopped','terminal')),
    PRIMARY KEY(command_id, ordinal),
    UNIQUE(command_id, execution_id)
);
CREATE TABLE IF NOT EXISTS inference_parent_stop_handoff_settlements (
    command_id TEXT PRIMARY KEY REFERENCES inference_parent_stop_handoffs(command_id),
    effect_json TEXT NOT NULL,
    effect_sha256 TEXT NOT NULL,
    created_at REAL NOT NULL
);
CREATE TRIGGER IF NOT EXISTS inference_parent_stop_handoffs_no_update
BEFORE UPDATE ON inference_parent_stop_handoffs BEGIN
    SELECT RAISE(ABORT, 'immutable inference parent stop handoff');
END;
CREATE TRIGGER IF NOT EXISTS inference_parent_stop_handoffs_no_delete
BEFORE DELETE ON inference_parent_stop_handoffs BEGIN
    SELECT RAISE(ABORT, 'immutable inference parent stop handoff');
END;
CREATE TRIGGER IF NOT EXISTS inference_parent_stop_handoff_executions_no_update
BEFORE UPDATE ON inference_parent_stop_handoff_executions BEGIN
    SELECT RAISE(ABORT, 'immutable inference parent stop handoff execution');
END;
CREATE TRIGGER IF NOT EXISTS inference_parent_stop_handoff_executions_no_delete
BEFORE DELETE ON inference_parent_stop_handoff_executions BEGIN
    SELECT RAISE(ABORT, 'immutable inference parent stop handoff execution');
END;
CREATE TRIGGER IF NOT EXISTS inference_parent_stop_handoff_settlements_no_update
BEFORE UPDATE ON inference_parent_stop_handoff_settlements BEGIN
    SELECT RAISE(ABORT, 'immutable inference parent stop handoff settlement');
END;
CREATE TRIGGER IF NOT EXISTS inference_parent_stop_handoff_settlements_no_delete
BEFORE DELETE ON inference_parent_stop_handoff_settlements BEGIN
    SELECT RAISE(ABORT, 'immutable inference parent stop handoff settlement');
END;

-- Publication-guard triggers (HS-137-01: moved from migrations.py).
-- A publication callback may terminalize its own parent only by clearing
-- the exact claim in that same update; every ordinary state transition
-- and warrant revocation must wait.
CREATE TRIGGER IF NOT EXISTS kernel_parent_publication_blocks_transition
BEFORE UPDATE OF state ON kernel_parent_runs
WHEN OLD.publication_claim_id != ''
  AND NEW.state != OLD.state
  AND NEW.publication_claim_id = OLD.publication_claim_id
BEGIN
    SELECT RAISE(ABORT, 'kernel_parent_publication_in_progress');
END;

CREATE TRIGGER IF NOT EXISTS kernel_parent_publication_blocks_warrant_revocation
BEFORE UPDATE OF warrant_revoked ON kernel_operations
WHEN OLD.warrant_revoked = 0
  AND NEW.warrant_revoked = 1
  AND EXISTS (
      SELECT 1 FROM kernel_parent_runs p
      WHERE p.operation_id = OLD.operation_id
        AND p.publication_claim_id != ''
  )
BEGIN
    SELECT RAISE(ABORT, 'kernel_parent_publication_in_progress');
END;

-- A receipt-gated, durable domain checkpoint for each admitted model child.
-- ``advanced`` says whether the child won the parent tuple CAS; stale stages are
-- retained as truthful receipt-linked facts but never become graph input.
CREATE TABLE IF NOT EXISTS kernel_parent_checkpoints (
    stage_id TEXT PRIMARY KEY REFERENCES kernel_projection_stages(stage_id),
    parent_operation_id TEXT NOT NULL REFERENCES kernel_parent_runs(operation_id),
    child_invocation_id TEXT NOT NULL,
    execution_epoch INTEGER NOT NULL,
    planned_node TEXT NOT NULL,
    checkpoint_json TEXT NOT NULL,
    advanced INTEGER NOT NULL CHECK (advanced IN (0,1)),
    created_at REAL NOT NULL,
    UNIQUE(parent_operation_id, child_invocation_id)
);
CREATE INDEX IF NOT EXISTS idx_kernel_parent_checkpoints_parent
ON kernel_parent_checkpoints(parent_operation_id, execution_epoch);

-- v61 (HS-136-01): Scheduled recordings — owner-set cron-driven capture.
CREATE TABLE IF NOT EXISTS scheduled_recordings (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL DEFAULT '',
    cron_expr TEXT NOT NULL,
    tz TEXT NOT NULL DEFAULT 'UTC',
    one_shot INTEGER NOT NULL DEFAULT 0 CHECK (one_shot IN (0,1)),
    duration_minutes INTEGER NOT NULL DEFAULT 60,
    enabled INTEGER NOT NULL DEFAULT 0 CHECK (enabled IN (0,1)),
    revision INTEGER NOT NULL DEFAULT 1,
    created_at REAL NOT NULL,
    last_fired_at REAL,
    next_fire_at REAL,
    armed_at REAL,
    deadline_at REAL,
    state TEXT NOT NULL DEFAULT 'idle'
        CHECK (state IN ('idle','arming','recording','stopped','cancelled','refused','missed')),
    last_outcome TEXT NOT NULL DEFAULT '',
    last_receipt_id TEXT NOT NULL DEFAULT '',
    delegation_receipt_id TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_scheduled_recordings_enabled
ON scheduled_recordings(enabled, next_fire_at) WHERE enabled=1;
"""
