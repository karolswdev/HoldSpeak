"""Inference runtime leases and durable kernel parents.

Part 11 of 17 of SCHEMA_SQL, in execution order (holdspeak/db/schema/__init__.py)."""

SQL = """
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
    kind TEXT NOT NULL CHECK (kind IN ('sequence','workflow','workbench','decision.promotion-draft','delivery.pr-review-draft','voice_reference_resolve','meeting.session','meeting.deferred-intel-job','dictation.session','wake.session','cadence.next-action-draft','rails.observer-batch','tool.turn')),
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
"""
