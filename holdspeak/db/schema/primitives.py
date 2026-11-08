"""The synced primitives: notes, refinement thoughts, desk decisions, decision records.

Part 4 of 17 of SCHEMA_SQL, in execution order (holdspeak/db/schema/__init__.py)."""

SQL = """
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
    deleted INTEGER NOT NULL DEFAULT 0,
    -- PHILO-15 08: what the record IS. A confirmed action writes a record
    -- as the Room's join anchor for its commitment; every reader asks this
    -- field before it calls a record a decision.
    kind TEXT NOT NULL DEFAULT 'decision'
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
"""
