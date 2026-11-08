"""KBs, recipes, chains, workflows, capability invocations, profiles, model manifests, mesh, directories, memberships, project items.

Part 6 of 17 of SCHEMA_SQL, in execution order (holdspeak/db/schema/__init__.py)."""

SQL = """
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
    -- HS-153-01: a mode is a recipe with kind='mode'; ordinary recipes keep ''.
    kind TEXT NOT NULL DEFAULT '' CHECK(kind IN ('', 'mode')),
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
    -- HS-158-01: semantic role and metadata for Project Room sources.
    semantic_role TEXT,
    metadata_json TEXT,
    revision INTEGER NOT NULL DEFAULT 0,
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

-- HS-158-01: Project-owned items (workstream, milestone, risk, dependency, signal).
CREATE TABLE IF NOT EXISTS project_items (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    item_type TEXT NOT NULL,
    title TEXT NOT NULL DEFAULT '',
    summary TEXT,
    lifecycle TEXT NOT NULL DEFAULT 'open',
    severity TEXT,
    owner_ref TEXT,
    due_at TEXT,
    sort_key REAL,
    details_json TEXT,
    provenance_kind TEXT,
    source_observation_id TEXT,
    created_by_ref TEXT,
    revision INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_project_items_project_type
ON project_items(project_id, item_type);

-- HS-158-01: Project aggregate change log (append-only).
CREATE TABLE IF NOT EXISTS project_changes (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    project_revision INTEGER NOT NULL,
    change_kind TEXT NOT NULL,
    target_ref TEXT,
    actor_ref TEXT,
    command_id TEXT,
    before_hash TEXT,
    after_hash TEXT,
    summary_json TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_project_changes_project_rev
ON project_changes(project_id, project_revision);

-- HS-158-01: Idempotent command ledger for Project writes (API-002, DOM-010).
CREATE TABLE IF NOT EXISTS project_commands (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    command_kind TEXT NOT NULL,
    request_hash TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    result_json TEXT,
    error_code TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_project_commands_project
ON project_commands(project_id, status);
"""
