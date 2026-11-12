"""Workbench, resourceful policies, schedule delegations, skills, constitutional context.

Part 7 of 17 of SCHEMA_SQL, in execution order (holdspeak/db/schema/__init__.py)."""

SQL = """
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
    deleted INTEGER NOT NULL DEFAULT 0,
    -- Betterment A2: one automation = one instruction + sources. A run of an
    -- automation with an instruction makes one occurrence item (one result).
    -- An empty instruction keeps the old queue run. ``sources_json`` is a list
    -- of qualified refs (note:<id>, meeting:<id>, ...). ``output_target`` is
    -- inbox | needs_you | destination:<id>.
    instruction TEXT NOT NULL DEFAULT '',
    sources_json TEXT NOT NULL DEFAULT '[]',
    output_target TEXT NOT NULL DEFAULT 'inbox',
    -- Betterment A4: the Spend limit per run for this automation (US dollars).
    -- NULL keeps the engine's own limit.
    spend_limit_usd REAL,
    -- Betterment A4: the When he chose, as JSON ({"kind": "schedule" | "event"
    -- | "manual", "reaction_id"}); '' for an automation from before A4.
    when_json TEXT NOT NULL DEFAULT '',
    -- Betterment AG14: hand each source item to an installed agent.
    do_kind TEXT NOT NULL DEFAULT 'run',
    agent_profile TEXT NOT NULL DEFAULT '',
    review_by TEXT NOT NULL DEFAULT '',
    -- Programs PG14: Do kind run_program. Each run makes one Program from
    -- the template, with this control level and Runs on, and starts it.
    program_template TEXT NOT NULL DEFAULT '',
    program_control TEXT NOT NULL DEFAULT '',
    program_runs_on_json TEXT NOT NULL DEFAULT '[]',
    program_may_call INTEGER NOT NULL DEFAULT 0,
    program_may_handoff INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS workbench_items (
    id TEXT PRIMARY KEY,
    parked INTEGER NOT NULL DEFAULT 0,
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
-- Retained pre-Program run metadata. New runs write programs and program_steps.
-- Keep this shape until legacy result joins can read absent retired history.
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
-- PHILO-7-02: device-local owner delegation of desk filing and decisions to
-- one agent identity (R1, R5). Never sync. One LIVE row per identity.
CREATE TABLE IF NOT EXISTS kernel_desk_delegations (
    id TEXT PRIMARY KEY,
    agent_identity TEXT NOT NULL,
    delegator_kind TEXT NOT NULL, delegator_identity TEXT NOT NULL,
    operations_json TEXT NOT NULL,
    terms_sha256 TEXT NOT NULL, expires_at REAL,
    state TEXT NOT NULL CHECK (state IN ('LIVE','REVOKED','EXPIRED')),
    revoked_at REAL, revocation_reason TEXT NOT NULL DEFAULT '',
    grant_operation_id TEXT NOT NULL,
    created_at REAL NOT NULL, updated_at REAL NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_desk_delegation_one_live
ON kernel_desk_delegations(agent_identity) WHERE state='LIVE';
CREATE INDEX IF NOT EXISTS idx_desk_delegations_agent_state
ON kernel_desk_delegations(agent_identity, state);
-- PHILO-9-07: the owner's project delegation grant (the Q2 ruling): Phase 7's
-- desk grant columns plus project_id; one LIVE row per (agent, project); the
-- terms, with the operations, stored in the row. Never sync.
CREATE TABLE IF NOT EXISTS kernel_project_delegations (
    id TEXT PRIMARY KEY,
    agent_identity TEXT NOT NULL,
    project_id TEXT NOT NULL,
    delegator_kind TEXT NOT NULL, delegator_identity TEXT NOT NULL,
    operations_json TEXT NOT NULL,
    terms_sha256 TEXT NOT NULL, expires_at REAL,
    state TEXT NOT NULL CHECK (state IN ('LIVE','REVOKED','EXPIRED')),
    revoked_at REAL, revocation_reason TEXT NOT NULL DEFAULT '',
    grant_operation_id TEXT NOT NULL,
    created_at REAL NOT NULL, updated_at REAL NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_project_delegation_one_live
ON kernel_project_delegations(agent_identity, project_id) WHERE state='LIVE';
CREATE INDEX IF NOT EXISTS idx_project_delegations_agent_project_state
ON kernel_project_delegations(agent_identity, project_id, state);
-- Conductor R2: the hub's agent credentials outlive a hub restart. The token
-- is stored only as its SHA-256; expires_at is wall-clock seconds and
-- mono_expires_at the monotonic deadline of boot boot_id. A revoked
-- row keeps revoked_at (never deleted). Device-local; never sync.
CREATE TABLE IF NOT EXISTS agent_credentials (
    id TEXT PRIMARY KEY,
    token_sha256 TEXT NOT NULL UNIQUE,
    identity TEXT NOT NULL,
    palette_json TEXT,
    palette_name TEXT,
    launch_id TEXT,
    project_id TEXT,
    targets_json TEXT NOT NULL DEFAULT '[]',
    expires_at REAL NOT NULL,
    mono_expires_at REAL,
    boot_id TEXT NOT NULL DEFAULT '',
    revoked_at REAL,
    revocation_reason TEXT NOT NULL DEFAULT '',
    created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_agent_credentials_live
ON agent_credentials(revoked_at, expires_at);
-- Conductor R2: what a launch-bound credential may change (its origin item and
-- what the agent created), keyed by the credential, so it ends with it.
CREATE TABLE IF NOT EXISTS agent_launch_ownership (
    credential_id TEXT NOT NULL,
    ref TEXT NOT NULL,
    created INTEGER NOT NULL DEFAULT 0,
    recorded_at REAL NOT NULL,
    PRIMARY KEY (credential_id, ref)
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
"""
