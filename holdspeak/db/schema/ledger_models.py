"""Domain event ledger, projections, deployments, installed models, model identity, bindings, capability assignment.

Part 10 of 17 of SCHEMA_SQL, in execution order (holdspeak/db/schema/__init__.py)."""

SQL = """
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
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    -- HS-159-01: WatchSpec@1 graduation columns (§9.3).
    schema_version TEXT NOT NULL DEFAULT '',
    project_id TEXT,
    intent TEXT NOT NULL DEFAULT '',
    provider_connection_id TEXT,
    subject_kind TEXT NOT NULL DEFAULT '',
    trigger_kind TEXT NOT NULL DEFAULT '',
    trigger_json TEXT NOT NULL DEFAULT '{}',
    mode TEXT NOT NULL DEFAULT '',
    state TEXT NOT NULL DEFAULT '',
    revision INTEGER NOT NULL DEFAULT 0,
    baseline_state TEXT NOT NULL DEFAULT '',
    test_state TEXT NOT NULL DEFAULT '',
    test_result_json TEXT,
    last_test_at TEXT,
    next_evaluation_at TEXT,
    last_evaluated_at TEXT,
    -- HS-164-01: unattended bookkeeping (cadence + circuit).
    evaluation_cadence_minutes INTEGER NOT NULL DEFAULT 60,
    circuit_state TEXT NOT NULL DEFAULT 'closed',
    circuit_failure_streak INTEGER NOT NULL DEFAULT 0,
    circuit_opened_at TEXT
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

-- HS-143-12: provider commands reserve a nonsecret request fingerprint before
-- writing private target/deployment/key custody. A pending row makes a delayed
-- key-store confirmation retriable; a completed owner-safe receipt makes the
-- exact command restart-safe. Credentials and endpoints are never stored here.
CREATE TABLE IF NOT EXISTS model_library_provider_commands (
    request_id TEXT PRIMARY KEY,
    command_kind TEXT NOT NULL CHECK (command_kind IN ('connect_hosted','define_endpoint','connect_paired')),
    request_sha256 TEXT NOT NULL,
    profile_id TEXT NOT NULL,
    state TEXT NOT NULL CHECK (state IN ('pending','completed')),
    response_json TEXT,
    response_sha256 TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
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
    -- Who made this revision, durable with it (owner ruling 2026-10-05):
    -- 'owner' = an owner press; 'holdspeak_default' = the batteries-included
    -- default HoldSpeak wrote by itself (services/inference_default_service.py).
    made_by TEXT NOT NULL DEFAULT 'owner',
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
-- The owner turned one capability OFF (PHILO-15 01 ruling: "off" must
-- hold).  A service route that reads this capability (the meeting-intel
-- queue) resolves OFF before any group or global head, so no summary runs on
-- the Default for AI work.  An exact assignment of the capability removes the
-- row (services/inference_assignment_service.py).
CREATE TABLE IF NOT EXISTS inference_capability_off (
    capability_id TEXT PRIMARY KEY,
    set_at TEXT NOT NULL
);
-- A network or cloud engine HoldSpeak found while no "Default for AI work"
-- exists.  It is never assigned by itself: the owner's "Use it" press assigns
-- it (services/inference_default_service.py; owner ruling 2026-10-05).
-- A meeting saved while NO engine could summarise it (meeting.deferred_analysis
-- had no ready route at Stop).  The summary backlog queues exactly these once
-- an engine can; an explicit Skip or a queued job removes the row
-- (services/meeting_backlog_service.py; owner ruling 2026-10-05).
CREATE TABLE IF NOT EXISTS meeting_summary_backlog (
    meeting_id TEXT PRIMARY KEY REFERENCES meetings(id) ON DELETE CASCADE,
    reason TEXT NOT NULL CHECK (reason IN ('summary_deferred_no_engine')),
    marked_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS inference_default_proposals (
    engine_id TEXT PRIMARY KEY,
    lamp TEXT NOT NULL CHECK (lamp IN ('private_network','mesh','cloud')),
    label TEXT NOT NULL,
    host TEXT NOT NULL DEFAULT '',
    profile_id TEXT NOT NULL DEFAULT '',
    profile_revision INTEGER NOT NULL DEFAULT 0,
    state TEXT NOT NULL CHECK (state IN ('open','used')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
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
"""
