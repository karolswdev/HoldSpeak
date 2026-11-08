"""Activity intelligence, connector runs, dictation corrections and journal, milestones, onboarding.

Part 3 of 17 of SCHEMA_SQL, in execution order (holdspeak/db/schema/__init__.py)."""

SQL = """
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
-- HS-176-02 (ruling R5) splits the two facts: `corrected` keeps its meaning
-- ("he taught FROM this row"), and `corrections_applied` is a JSON array of
-- the correction ids that FIRED ON this row.
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
    correction_id INTEGER,
    corrections_applied TEXT NOT NULL DEFAULT '[]'
);

CREATE INDEX IF NOT EXISTS idx_dictation_journal_recent
ON dictation_journal(created_at DESC, id DESC);
"""
