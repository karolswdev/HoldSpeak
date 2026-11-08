"""Kernel operation journal, runner results, refinement continuity, pipeline events, Monday briefs.

Part 9 of 17 of SCHEMA_SQL, in execution order (holdspeak/db/schema/__init__.py)."""

SQL = """
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
    is_async INTEGER NOT NULL DEFAULT 0,
    -- HS-174: origin of the call (local stdio/in-process vs remote HTTP).
    origin TEXT NOT NULL DEFAULT 'local',
    -- HS-174: caller address for remote calls (e.g. tailnet IP).
    caller TEXT NOT NULL DEFAULT '',
    -- HS-174: credential identity label for remote calls.
    caller_identity TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_pipeline_events_timestamp
ON pipeline_events(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_pipeline_events_service_method
ON pipeline_events(service, method, timestamp DESC);

-- PERF-HUB 2026-10-28: the Room reads its receipts by method alone, and the
-- remote-host and remote-origin reads filter on origin. Without these two
-- indexes each of those reads scanned the whole table (1.4 M rows on the
-- owner's desk) on every needs-you, settings and projections read.
CREATE INDEX IF NOT EXISTS idx_pipeline_events_method
ON pipeline_events(method, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_pipeline_events_origin
ON pipeline_events(origin, timestamp DESC)
WHERE origin != 'local';

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
    priority INTEGER NOT NULL DEFAULT 0,
    created_at TEXT
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
"""
