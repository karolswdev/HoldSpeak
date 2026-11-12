"""Project setup, watches, project sources, observations, proposals, review windows, updates, delivery and sends.

Part 14 of 17 of SCHEMA_SQL, in execution order (holdspeak/db/schema/__init__.py)."""

SQL = """
-- HS-159-01: Project setup interview (§9.1) — durable setup sessions.
CREATE TABLE IF NOT EXISTS project_setup_sessions (
    id TEXT PRIMARY KEY,
    state TEXT NOT NULL DEFAULT 'active',
    stage TEXT NOT NULL DEFAULT '',
    draft_schema TEXT NOT NULL DEFAULT '',
    draft_json TEXT NOT NULL DEFAULT '{}',
    project_id TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at TEXT,
    expires_at TEXT
);

-- HS-159-01: Setup answers (§9.1) — append-only, UNIQUE(session_id, question_id, revision).
CREATE TABLE IF NOT EXISTS project_setup_answers (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES project_setup_sessions(id),
    question_id TEXT NOT NULL,
    answer_schema TEXT NOT NULL DEFAULT '',
    answer_json TEXT NOT NULL DEFAULT '{}',
    revision INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(session_id, question_id, revision)
);
CREATE INDEX IF NOT EXISTS idx_project_setup_answers_session
    ON project_setup_answers(session_id, question_id);

-- HS-159-01: Watch setup proposals (§9.1).
CREATE TABLE IF NOT EXISTS watch_setup_proposals (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES project_setup_sessions(id),
    provider_id TEXT NOT NULL DEFAULT '',
    connection_id TEXT,
    spec_schema TEXT NOT NULL DEFAULT '',
    spec_json TEXT NOT NULL DEFAULT '{}',
    rationale_json TEXT NOT NULL DEFAULT '{}',
    state TEXT NOT NULL DEFAULT 'proposed',
    test_state TEXT NOT NULL DEFAULT '',
    test_result_json TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_watch_setup_proposals_session
    ON watch_setup_proposals(session_id, state);

-- HS-159-01: Watch provider connections (§9.2) — NO credential material (PROV-004).
CREATE TABLE IF NOT EXISTS watch_provider_connections (
    id TEXT PRIMARY KEY,
    provider_id TEXT NOT NULL DEFAULT '',
    transport TEXT NOT NULL DEFAULT '',
    external_connection_ref TEXT NOT NULL DEFAULT '',
    state TEXT NOT NULL DEFAULT '',
    capability_manifest_json TEXT NOT NULL DEFAULT '{}',
    capability_revision INTEGER NOT NULL DEFAULT 0,
    discovery_state TEXT NOT NULL DEFAULT '',
    last_checked_at TEXT,
    last_connected_at TEXT,
    last_error_code TEXT,
    last_error_detail TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_watch_provider_connections_provider
    ON watch_provider_connections(provider_id, state);

-- A removal claim blocks every gh edge before native credential dispatch.
CREATE TABLE IF NOT EXISTS github_connection_removals (
    connection_id TEXT PRIMARY KEY REFERENCES watch_provider_connections(id),
    operation_id TEXT NOT NULL,
    account_ref TEXT NOT NULL,
    checked_at TEXT NOT NULL,
    state TEXT NOT NULL CHECK (state IN ('pending','removed','uncertain')),
    updated_at TEXT NOT NULL
);

-- HS-159-01: Watch rules (§9.4) — UNIQUE(watch_id, ordinal).
CREATE TABLE IF NOT EXISTS watch_rules (
    id TEXT PRIMARY KEY,
    watch_id TEXT NOT NULL REFERENCES connector_watches(id) ON DELETE CASCADE,
    ordinal INTEGER NOT NULL DEFAULT 0,
    condition_schema TEXT NOT NULL DEFAULT '',
    condition_json TEXT NOT NULL DEFAULT '{}',
    action_schema TEXT NOT NULL DEFAULT '',
    action_json TEXT NOT NULL DEFAULT '{}',
    enabled INTEGER NOT NULL DEFAULT 1,
    revision INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(watch_id, ordinal)
);
CREATE INDEX IF NOT EXISTS idx_watch_rules_watch
    ON watch_rules(watch_id, enabled);

-- HS-159-01: Watch evaluations (§9.4) — UNIQUE(watch_id, watch_revision, source_revision).
CREATE TABLE IF NOT EXISTS watch_evaluations (
    id TEXT PRIMARY KEY,
    watch_id TEXT NOT NULL REFERENCES connector_watches(id) ON DELETE CASCADE,
    watch_revision INTEGER NOT NULL DEFAULT 0,
    provider_capability_revision INTEGER NOT NULL DEFAULT 0,
    source_revision TEXT NOT NULL DEFAULT '',
    trigger_kind TEXT NOT NULL DEFAULT '',
    state TEXT NOT NULL DEFAULT '',
    matched_rule_ids_json TEXT NOT NULL DEFAULT '[]',
    observation_ids_json TEXT NOT NULL DEFAULT '[]',
    started_at TEXT,
    completed_at TEXT,
    error_code TEXT,
    error_detail TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    UNIQUE(watch_id, watch_revision, source_revision)
);
CREATE INDEX IF NOT EXISTS idx_watch_evaluations_watch
    ON watch_evaluations(watch_id, watch_revision);

-- HS-159-01: Watch effects (§9.4) — idempotency_key UNIQUE.
CREATE TABLE IF NOT EXISTS watch_effects (
    id TEXT PRIMARY KEY,
    evaluation_id TEXT NOT NULL REFERENCES watch_evaluations(id) ON DELETE CASCADE,
    rule_id TEXT NOT NULL REFERENCES watch_rules(id),
    action_kind TEXT NOT NULL DEFAULT '',
    target_ref TEXT NOT NULL DEFAULT '',
    idempotency_key TEXT NOT NULL UNIQUE,
    arguments_sha256 TEXT NOT NULL DEFAULT '',
    state TEXT NOT NULL DEFAULT '',
    operation_id TEXT,
    receipt_id TEXT,
    result_ref TEXT,
    verification_state TEXT NOT NULL DEFAULT '',
    error_code TEXT,
    error_detail TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_watch_effects_evaluation
    ON watch_effects(evaluation_id);
CREATE INDEX IF NOT EXISTS idx_watch_effects_idempotency
    ON watch_effects(idempotency_key);

-- HS-159-01: Project sources (§5.4 / DOM-013 by shape — no query/cadence/baseline columns).
CREATE TABLE IF NOT EXISTS project_sources (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id),
    source_ref TEXT NOT NULL DEFAULT '',
    label TEXT NOT NULL DEFAULT '',
    semantic_role TEXT NOT NULL DEFAULT '',
    materiality_policy_json TEXT NOT NULL DEFAULT '{}',
    enabled INTEGER NOT NULL DEFAULT 1,
    freshness_state TEXT NOT NULL DEFAULT '',
    last_observed_at TEXT,
    revision INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_project_sources_project
    ON project_sources(project_id, enabled);
CREATE INDEX IF NOT EXISTS idx_project_sources_ref
    ON project_sources(source_ref);

-- HS-160-01: Append-only normalized observations (§5.5, DB-003).
-- Identity is deterministic from (adapter, source_id, source_version, fact_key)
-- via generate_pobs_id; the PK is the hash so adapter retries no-op (INSERT OR IGNORE).
CREATE TABLE IF NOT EXISTS project_observations (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    source_id TEXT NOT NULL DEFAULT '',
    observation_kind TEXT NOT NULL DEFAULT '',
    subject_ref TEXT,
    source_version TEXT NOT NULL DEFAULT '',
    observed_at TEXT NOT NULL DEFAULT (datetime('now')),
    captured_at TEXT NOT NULL DEFAULT (datetime('now')),
    fact_json TEXT NOT NULL DEFAULT '{}',
    content_hash TEXT NOT NULL DEFAULT '',
    supersedes_observation_id TEXT,
    coverage_state TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_project_observations_source
    ON project_observations(project_id, source_id, observed_at);

-- HS-160-01: Evidence links (§5.6) — from assessment/proposal/item to evidence.
CREATE TABLE IF NOT EXISTS project_evidence_links (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    target_ref TEXT NOT NULL DEFAULT '',
    evidence_ref TEXT NOT NULL DEFAULT '',
    relation TEXT NOT NULL DEFAULT '',
    observation_id TEXT,
    excerpt_locator_json TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_project_evidence_links_target
    ON project_evidence_links(project_id, target_ref);

-- HS-160-01: Proposals with full decision lifecycle (§5.7).
-- Identity is deterministic from (project_id, review_window_key, proposal_kind,
-- target_ref, normalized_patch) via generate_pprop_id; PK is the hash.
CREATE TABLE IF NOT EXISTS project_proposals (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    review_window_key TEXT NOT NULL DEFAULT '',
    proposal_kind TEXT NOT NULL DEFAULT '',
    target_ref TEXT NOT NULL DEFAULT '',
    title TEXT NOT NULL DEFAULT '',
    rationale TEXT,
    patch_json TEXT NOT NULL DEFAULT '{}',
    materiality TEXT,
    confidence REAL,
    producer_kind TEXT,
    model_receipt_ref TEXT,
    lifecycle TEXT NOT NULL DEFAULT 'open',
    deferred_until TEXT,
    dismissal_basis_hash TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    decided_at TEXT,
    decided_by_ref TEXT,
    -- Conductor K4: the observation's change class (added, changed,
    -- closed, overdue, blocked, contradicted, coverage_degraded), so the
    -- weekly update reports a merged or resolved item as closed.
    change_class TEXT
);
CREATE INDEX IF NOT EXISTS idx_project_proposals_window
    ON project_proposals(project_id, review_window_key, lifecycle);

-- HS-160-01: Frozen review windows (§5.8).
CREATE TABLE IF NOT EXISTS project_reviews (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'open',
    from_sequence INTEGER,
    through_sequence INTEGER,
    source_manifest_json TEXT NOT NULL DEFAULT '{}',
    project_revision_opened INTEGER,
    project_revision_accepted INTEGER,
    opened_at TEXT NOT NULL DEFAULT (datetime('now')),
    accepted_at TEXT,
    accepted_by_ref TEXT,
    summary_json TEXT
);
CREATE INDEX IF NOT EXISTS idx_project_reviews_status
    ON project_reviews(project_id, status);

-- HS-162-01: Project updates (§8, UPD-004).
-- A draft pins the project_revision and source_manifest it was built over.
-- Publishing sets lifecycle='published' + published_at; published rows are
-- IMMUTABLE (the repo layer refuses any write).  Regeneration creates a new
-- draft (draft_revision+1) that supersedes the previous unaccepted draft.
CREATE TABLE IF NOT EXISTS project_updates (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    project_revision INTEGER NOT NULL,
    review_id TEXT,
    lifecycle TEXT NOT NULL DEFAULT 'draft',
    draft_revision INTEGER NOT NULL DEFAULT 1,
    body_md TEXT NOT NULL DEFAULT '',
    claims_json TEXT NOT NULL DEFAULT '{}',
    source_manifest_json TEXT NOT NULL DEFAULT '{}',
    generator TEXT NOT NULL DEFAULT 'deterministic',
    generator_host TEXT,
    generator_model TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    published_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_project_updates_project
    ON project_updates(project_id, lifecycle);
CREATE INDEX IF NOT EXISTS idx_project_updates_review
    ON project_updates(project_id, review_id);

-- Betterment P1: the engine pass behind Write update. One row per pass: the
-- records draft it improves (base_update_id), its state, and, when it
-- finished, the engine's composed draft (result_json) or its reason. The
-- draft is saved to project_updates only when the owner's draft allows it.
CREATE TABLE IF NOT EXISTS project_update_jobs (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    base_update_id TEXT NOT NULL,
    base_body_sha TEXT NOT NULL DEFAULT '',
    state TEXT NOT NULL DEFAULT 'running',
    reason TEXT,
    detail TEXT,
    result_json TEXT,
    applied_update_id TEXT,
    started_at TEXT NOT NULL DEFAULT (datetime('now')),
    finished_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_project_update_jobs_project
    ON project_update_jobs(project_id, started_at);

-- PHILO-9-01: delivery by copy and confirm (the owner's Q0 ruling, "Several
-- per update").  One row per confirmation that the owner delivered a
-- PUBLISHED update himself; the product sends nothing.  delivered_at is his
-- confirmation time; delivered_to is optional free text.  operation_id is the
-- kernel operation that admitted the mark (PHILO-9-02 writes it with the
-- terminal receipt in one transaction).  A row is final: no update, no
-- delete, no cascade; project_updates is never written by a delivery.
CREATE TABLE IF NOT EXISTS project_update_deliveries (
    id TEXT PRIMARY KEY,
    update_id TEXT NOT NULL REFERENCES project_updates(id),
    project_id TEXT NOT NULL,
    delivered_at TEXT NOT NULL,
    delivered_to TEXT,
    operation_id TEXT NOT NULL UNIQUE REFERENCES kernel_operations(operation_id),
    -- PHILO-10-01 (additive): how it left.  'manual' is the copy and confirm
    -- above; a channel send writes its row when it settles sent or unknown,
    -- in the settle transaction.  outcome: confirmed (manual), sent, unknown.
    channel TEXT NOT NULL DEFAULT 'manual',
    send_id TEXT,
    outcome TEXT NOT NULL DEFAULT 'confirmed',
    proof_json TEXT
);
CREATE INDEX IF NOT EXISTS idx_project_update_deliveries_update
    ON project_update_deliveries(update_id);

-- PHILO-10-01: the saved destinations (design/send-lifecycle.md section 1).
-- No secret.  A row never changes its target: Edit parks the old row and makes
-- a new one; Remove parks the row.  target_digest = sha256 of channel +
-- account + target_json (canonical JSON).
CREATE TABLE IF NOT EXISTS channel_destinations (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    channel TEXT NOT NULL,
    account_json TEXT NOT NULL DEFAULT '{}',
    target_json TEXT NOT NULL,
    target_digest TEXT NOT NULL,
    synced INTEGER NOT NULL DEFAULT 0,
    state TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL,
    parked_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_channel_destinations_state
    ON channel_destinations(state, created_at);

-- PHILO-10-01: one row per send, from prepare to its end.  States: prepared ->
-- dispatching -> sent | failed | unknown; prepared -> discarded.  The frozen
-- target and the exact transport bytes (payload) with their digest.  The
-- dispatch boundary (state dispatching + send_operation_id) commits BEFORE any
-- effect; recovery never dispatches again.  PHILO-10-04 (additive): dispatch_seq
-- is the order sends LEFT in, allocated inside the boundary transaction
-- (MAX + 1 under BEGIN IMMEDIATE); the face's "latest" reads it.
CREATE TABLE IF NOT EXISTS channel_sends (
    id TEXT PRIMARY KEY,
    document_ref TEXT NOT NULL,
    destination_id TEXT NOT NULL REFERENCES channel_destinations(id),
    channel TEXT NOT NULL,
    account_json TEXT NOT NULL DEFAULT '{}',
    target_json TEXT NOT NULL,
    target_digest TEXT NOT NULL,
    payload BLOB NOT NULL,
    payload_digest TEXT NOT NULL,
    -- PHILO-11-01: frozen source naming provenance. NULL is the legacy
    -- Phase 10 shape and keeps its naming fallback.
    document_json TEXT,
    prepared_by_kind TEXT NOT NULL DEFAULT '',
    prepared_by_identity TEXT NOT NULL DEFAULT '',
    prepare_operation_id TEXT UNIQUE,
    send_operation_id TEXT UNIQUE,
    state TEXT NOT NULL,
    proof_json TEXT,
    reason TEXT,
    file_path TEXT,
    created_at TEXT NOT NULL,
    dispatch_started_at TEXT,
    settled_at TEXT,
    dispatch_seq INTEGER,
    -- The built-in HoldSpeak folder (2026-10-05, additive): where the file goes
    -- past this device, judged ONCE at the dispatch boundary (the sync
    -- provider: 'icloud', 'dropbox', 'googledrive', 'onedrive' or 'synced';
    -- NULL: it stays here). The settle copies
    -- it into the proof, whichever path settles (dispatch, take-over, reaper).
    egress TEXT
);
CREATE INDEX IF NOT EXISTS idx_channel_sends_document
    ON channel_sends(document_ref, created_at);
"""
