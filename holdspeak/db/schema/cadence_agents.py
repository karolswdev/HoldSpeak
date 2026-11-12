"""Cadence engine, steering audit, agent session events, desk windows, tool-call gate, work attempts, receipts.

Part 8 of 17 of SCHEMA_SQL, in execution order (holdspeak/db/schema/__init__.py)."""

SQL = """
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

-- PHILO-14 C0: the agent session's event log, one row per hook event (the
-- session record in agent_sessions.json keeps only the last). The rider hook
-- spools each event to a file; the hub drains the spool into this table
-- (agent_context/event_log.py); the launch lane route reads it.
-- Heads are secret-redacted; the newest 2000 rows per session are kept.
CREATE TABLE IF NOT EXISTS agent_session_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    spool_id TEXT,
    session_key TEXT NOT NULL,
    ts TEXT NOT NULL,
    event TEXT NOT NULL,
    tool TEXT,
    head TEXT,
    text TEXT,
    detail_json TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_agent_session_events_key ON agent_session_events(session_key, id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_agent_session_events_spool ON agent_session_events(spool_id);

-- PHILO-16 (L1, L3, L5): the desk's windows. The hub owns them; every browser
-- is one view of the same desk and an agent reaches the same windows
-- (services/desk_window_service.py). One row per open window of the one
-- owner desk. Geometry is share+px values ({"x","y","w","h"}: a number of
-- pixels or a string like "50% + 10"), resolved by each view. Depth is a
-- counter the hub increments (desk_window_desk.highest_depth); front is
-- derived. A row's revision is the desk's revision at its last write
-- (compare-and-set).
CREATE TABLE IF NOT EXISTS desk_windows (
    id TEXT PRIMARY KEY,
    app TEXT NOT NULL,
    object_ref TEXT,
    geometry_json TEXT,
    depth INTEGER NOT NULL DEFAULT 0,
    minimized INTEGER NOT NULL DEFAULT 0,
    zoomed INTEGER NOT NULL DEFAULT 0,
    zoom_json TEXT,
    arranged INTEGER NOT NULL DEFAULT 0,
    room TEXT,
    revision INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
-- The desk-level window state: the depth counter, the ONE revision counter
-- of the desk's windows (every window write takes the next; a row keeps the
-- revision of its last write, so a reopened window never repeats one), Stage's
-- shelf side and its revision, and when the hub first held the desk's windows
-- (adopted_at: a browser seeds the hub from its cache only before it).
CREATE TABLE IF NOT EXISTS desk_window_desk (
    id TEXT PRIMARY KEY,
    highest_depth INTEGER NOT NULL DEFAULT 0,
    stage_shelf TEXT NOT NULL DEFAULT 'left',
    revision INTEGER NOT NULL DEFAULT 0,
    shelf_revision INTEGER NOT NULL DEFAULT 0,
    adopted_at TEXT,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- HS-104-02: the tool-call gate. A proposal is a RECORD, never authority --
-- nothing in this table can cause execution; only a live hook waiting on a
-- decision can proceed. Arguments are redacted at the edge (sha256 + first
-- 120 chars); a CUT call's whole redacted text is kept apart, in
-- gate_full_calls, only while it is held (PHILO-15 20).
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
-- PHILO-15 20 (B63): the whole redacted call of a HELD proposal whose head
-- is cut (over 120 chars), for the owner's Raw read only (GET
-- /api/gate/proposals/{id}/command). Never sent to an agent. Redacted of
-- secret shapes as the head is; removed when the proposal leaves held.
CREATE TABLE IF NOT EXISTS gate_full_calls (
    proposal_id TEXT PRIMARY KEY,
    args_full TEXT NOT NULL,
    stored_at REAL NOT NULL
);

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
    ended_at TEXT,
    origin_ref TEXT               -- kind:id of the desk object a launch works on
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
"""
