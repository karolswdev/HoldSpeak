"""Decision memory projection, actuator proposals, authority grants, desk projection state, projects.

Part 2 of 17 of SCHEMA_SQL, in execution order (holdspeak/db/schema/__init__.py)."""

SQL = """
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
    -- HS-158-01: Project Room aggregate identity, lifecycle, and cadence.
    purpose TEXT,
    outcome_text TEXT,
    owner_ref TEXT,
    lifecycle TEXT NOT NULL DEFAULT 'active',
    posture TEXT,
    posture_reason TEXT,
    start_at TEXT,
    target_at TEXT,
    review_cadence_json TEXT,
    next_review_at TEXT,
    template_key TEXT,
    modules_json TEXT,
    revision INTEGER NOT NULL DEFAULT 0,
    last_review_id TEXT,
    last_review_at TEXT,
    -- HS-169-04: per-project read marker for the Room's "since you looked".
    room_read_at TEXT,
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
"""
