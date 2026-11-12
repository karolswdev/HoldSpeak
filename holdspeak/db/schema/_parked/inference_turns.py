# Parked: no live readers or writers; existing databases keep this history unchanged.

SQL = """
-- HS-143-08: one parent and its declared inference route set.  The manifest is
-- content-free and immutable; child operation material is frozen only when a
-- real window/stage exists.
CREATE TABLE IF NOT EXISTS inference_parent_route_bundles (
    id TEXT PRIMARY KEY,
    command_id TEXT NOT NULL UNIQUE,
    request_sha256 TEXT NOT NULL,
    parent_operation_id TEXT NOT NULL UNIQUE REFERENCES kernel_parent_runs(operation_id),
    parent_deadline_at REAL NOT NULL,
    parent_child_budget INTEGER NOT NULL CHECK (parent_child_budget > 0),
    lifecycle_child_budget INTEGER NOT NULL CHECK (lifecycle_child_budget >= 0),
    feature_principal_sha256 TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    sha256 TEXT NOT NULL UNIQUE,
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS inference_parent_route_bundle_members (
    id TEXT PRIMARY KEY,
    bundle_id TEXT NOT NULL REFERENCES inference_parent_route_bundles(id),
    ordinal INTEGER NOT NULL CHECK (ordinal > 0),
    route_key TEXT NOT NULL,
    capability_id TEXT NOT NULL,
    route_plan_id TEXT NOT NULL UNIQUE REFERENCES inference_route_plans(id),
    route_plan_sha256 TEXT NOT NULL,
    principal_policy_sha256 TEXT NOT NULL,
    maximum_physical_attempts INTEGER NOT NULL CHECK (maximum_physical_attempts > 0),
    UNIQUE(bundle_id, ordinal),
    UNIQUE(bundle_id, route_key),
    UNIQUE(bundle_id, capability_id)
);
CREATE TRIGGER IF NOT EXISTS inference_parent_route_bundles_no_update
BEFORE UPDATE ON inference_parent_route_bundles BEGIN
    SELECT RAISE(ABORT, 'immutable inference parent route bundle');
END;
CREATE TRIGGER IF NOT EXISTS inference_parent_route_bundles_no_delete
BEFORE DELETE ON inference_parent_route_bundles BEGIN
    SELECT RAISE(ABORT, 'immutable inference parent route bundle');
END;
CREATE TRIGGER IF NOT EXISTS inference_parent_route_bundle_members_no_update
BEFORE UPDATE ON inference_parent_route_bundle_members BEGIN
    SELECT RAISE(ABORT, 'immutable inference parent route bundle member');
END;
CREATE TRIGGER IF NOT EXISTS inference_parent_route_bundle_members_no_delete
BEFORE DELETE ON inference_parent_route_bundle_members BEGIN
    SELECT RAISE(ABORT, 'immutable inference parent route bundle member');
END;

-- A durable Stop election can fence every exact active route before Meeting
-- enqueues displaced work.  Story 08's entrance cutover will attach the queue
-- effect; this tranche establishes the replay-safe authority and membership.
CREATE TABLE IF NOT EXISTS inference_parent_stop_handoffs (
    command_id TEXT PRIMARY KEY,
    request_sha256 TEXT NOT NULL,
    bundle_id TEXT NOT NULL REFERENCES inference_parent_route_bundles(id),
    parent_operation_id TEXT NOT NULL UNIQUE REFERENCES kernel_parent_runs(operation_id),
    evidence_provider_id TEXT NOT NULL,
    evidence_provider_revision INTEGER NOT NULL CHECK (evidence_provider_revision > 0),
    planning_reference TEXT NOT NULL,
    evidence_ref TEXT NOT NULL,
    evidence_sha256 TEXT NOT NULL,
    state TEXT NOT NULL CHECK (state IN ('committed','pending_physical_settlement')),
    effect_json TEXT NOT NULL,
    effect_sha256 TEXT NOT NULL,
    created_at REAL NOT NULL
);
-- Queue recovery scans unsettled adopter handoffs by provider/revision in
-- durable creation order; the settlement anti-join remains the authority.
CREATE INDEX IF NOT EXISTS idx_stop_handoffs_unsettled_provider
ON inference_parent_stop_handoffs(evidence_provider_id, evidence_provider_revision, created_at, command_id);
CREATE TABLE IF NOT EXISTS inference_parent_stop_handoff_executions (
    command_id TEXT NOT NULL REFERENCES inference_parent_stop_handoffs(command_id),
    ordinal INTEGER NOT NULL CHECK (ordinal > 0),
    execution_id TEXT NOT NULL REFERENCES inference_route_executions(id),
    stop_command_id TEXT NOT NULL UNIQUE REFERENCES inference_route_execution_commands(command_id),
    elected_state TEXT NOT NULL CHECK (elected_state IN ('stopping','stopped','terminal')),
    PRIMARY KEY(command_id, ordinal),
    UNIQUE(command_id, execution_id)
);
CREATE TABLE IF NOT EXISTS inference_parent_stop_handoff_settlements (
    command_id TEXT PRIMARY KEY REFERENCES inference_parent_stop_handoffs(command_id),
    effect_json TEXT NOT NULL,
    effect_sha256 TEXT NOT NULL,
    created_at REAL NOT NULL
);
CREATE TRIGGER IF NOT EXISTS inference_parent_stop_handoffs_no_update
BEFORE UPDATE ON inference_parent_stop_handoffs BEGIN
    SELECT RAISE(ABORT, 'immutable inference parent stop handoff');
END;
CREATE TRIGGER IF NOT EXISTS inference_parent_stop_handoffs_no_delete
BEFORE DELETE ON inference_parent_stop_handoffs BEGIN
    SELECT RAISE(ABORT, 'immutable inference parent stop handoff');
END;
CREATE TRIGGER IF NOT EXISTS inference_parent_stop_handoff_executions_no_update
BEFORE UPDATE ON inference_parent_stop_handoff_executions BEGIN
    SELECT RAISE(ABORT, 'immutable inference parent stop handoff execution');
END;
CREATE TRIGGER IF NOT EXISTS inference_parent_stop_handoff_executions_no_delete
BEFORE DELETE ON inference_parent_stop_handoff_executions BEGIN
    SELECT RAISE(ABORT, 'immutable inference parent stop handoff execution');
END;
CREATE TRIGGER IF NOT EXISTS inference_parent_stop_handoff_settlements_no_update
BEFORE UPDATE ON inference_parent_stop_handoff_settlements BEGIN
    SELECT RAISE(ABORT, 'immutable inference parent stop handoff settlement');
END;
CREATE TRIGGER IF NOT EXISTS inference_parent_stop_handoff_settlements_no_delete
BEFORE DELETE ON inference_parent_stop_handoff_settlements BEGIN
    SELECT RAISE(ABORT, 'immutable inference parent stop handoff settlement');
END;

-- HS-143-09: MODEL_TURN authority remains a private, hub-local ledger.  It
-- records identity, canonical hashes, reservations and immutable receipts only;
-- tool arguments, effect payloads, owner identity and provider dialect material
-- never appear in projections or sync rows.
CREATE TABLE IF NOT EXISTS turn_capability_leases (
    lease_id TEXT PRIMARY KEY,
    turn_id TEXT NOT NULL UNIQUE,
    terms_json TEXT NOT NULL,
    terms_sha256 TEXT NOT NULL UNIQUE,
    nonce_sha256 TEXT NOT NULL,
    epoch INTEGER NOT NULL CHECK (epoch > 0),
    created_at REAL NOT NULL,
    expires_at REAL NOT NULL,
    state TEXT NOT NULL CHECK (state IN ('active','revoked','expired','terminal')),
    revoked_at REAL,
    revocation_code TEXT NOT NULL DEFAULT '',
    CHECK (expires_at >= created_at)
);
CREATE TABLE IF NOT EXISTS tool_turns (
    turn_id TEXT PRIMARY KEY,
    command_id TEXT NOT NULL UNIQUE,
    parent_operation_id TEXT NOT NULL UNIQUE REFERENCES kernel_parent_runs(operation_id),
    parent_bundle_id TEXT NOT NULL UNIQUE REFERENCES inference_parent_route_bundles(id),
    route_plan_id TEXT NOT NULL REFERENCES inference_route_plans(id),
    route_plan_sha256 TEXT NOT NULL,
    lease_id TEXT NOT NULL UNIQUE REFERENCES turn_capability_leases(lease_id),
    lease_sha256 TEXT NOT NULL,
    budgets_json TEXT NOT NULL,
    budgets_sha256 TEXT NOT NULL,
    state TEXT NOT NULL CHECK (state IN ('reserved','model_running','tool_requested','tool_admitted','tool_receipted','result_ready','stopped','failed','indeterminate')),
    revision INTEGER NOT NULL DEFAULT 1 CHECK (revision > 0),
    terminal_code TEXT NOT NULL DEFAULT '',
    final_result_ref TEXT NOT NULL DEFAULT '',
    stop_provenance_ref TEXT NOT NULL DEFAULT '',
    deadline_at REAL NOT NULL,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_tool_turns_state ON tool_turns(state, deadline_at);
CREATE TABLE IF NOT EXISTS tool_turn_model_steps (
    id TEXT PRIMARY KEY,
    turn_id TEXT NOT NULL REFERENCES tool_turns(turn_id),
    ordinal INTEGER NOT NULL CHECK (ordinal > 0),
    operation_request_plan_id TEXT NOT NULL,
    operation_request_plan_sha256 TEXT NOT NULL,
    route_execution_id TEXT NOT NULL DEFAULT '',
    lease_sha256 TEXT NOT NULL,
    state TEXT NOT NULL CHECK (state IN ('reserved','running','receipted','failed','indeterminate')),
    child_receipt_id TEXT NOT NULL DEFAULT '',
    result_sha256 TEXT NOT NULL DEFAULT '',
    request_material_ref TEXT NOT NULL DEFAULT '',
    result_material_ref TEXT NOT NULL DEFAULT '',
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL,
    UNIQUE(turn_id, ordinal)
);
CREATE TABLE IF NOT EXISTS tool_turn_tool_calls (
    id TEXT PRIMARY KEY,
    turn_id TEXT NOT NULL REFERENCES tool_turns(turn_id),
    tool_ordinal INTEGER NOT NULL CHECK (tool_ordinal > 0),
    provider_tool_ordinal INTEGER NOT NULL CHECK (provider_tool_ordinal > 0),
    provider_tool_call_id TEXT NOT NULL,
    capability_id TEXT NOT NULL,
    capability_revision INTEGER NOT NULL CHECK (capability_revision > 0),
    lease_sha256 TEXT NOT NULL,
    canonical_args_sha256 TEXT NOT NULL,
    reserved_result_bytes INTEGER NOT NULL CHECK (reserved_result_bytes >= 0),
    reserved_result_tokens INTEGER NOT NULL CHECK (reserved_result_tokens >= 0),
    reserved_effects INTEGER NOT NULL CHECK (reserved_effects >= 0),
    state TEXT NOT NULL CHECK (state IN ('reserved','admitted','receipted','unavailable','denied','oversize','indeterminate')),
    broker_child_id TEXT NOT NULL DEFAULT '',
    receipt_id TEXT NOT NULL DEFAULT '',
    result_sha256 TEXT NOT NULL DEFAULT '',
    disposition TEXT NOT NULL DEFAULT '',
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL,
    UNIQUE(turn_id, tool_ordinal),
    UNIQUE(turn_id, provider_tool_ordinal),
    UNIQUE(turn_id, provider_tool_call_id),
    UNIQUE(turn_id, provider_tool_call_id, capability_revision, canonical_args_sha256)
);
CREATE INDEX IF NOT EXISTS idx_tool_turn_tool_calls_turn_state
ON tool_turn_tool_calls(turn_id, state, tool_ordinal);
CREATE TABLE IF NOT EXISTS tool_turn_tool_call_results (
    tool_call_id TEXT PRIMARY KEY REFERENCES tool_turn_tool_calls(id),
    turn_id TEXT NOT NULL REFERENCES tool_turns(turn_id),
    provider_tool_ordinal INTEGER NOT NULL CHECK (provider_tool_ordinal > 0),
    envelope_json TEXT NOT NULL,
    result_material_json TEXT NOT NULL DEFAULT '',
    result_material_sha256 TEXT NOT NULL DEFAULT '',
    created_at REAL NOT NULL,
    UNIQUE(turn_id, provider_tool_ordinal)
);
CREATE TABLE IF NOT EXISTS tool_turn_effect_children (
    id TEXT PRIMARY KEY,
    turn_id TEXT NOT NULL REFERENCES tool_turns(turn_id),
    tool_call_id TEXT NOT NULL UNIQUE REFERENCES tool_turn_tool_calls(id),
    broker_child_id TEXT NOT NULL,
    owner_intent_receipt_ref TEXT NOT NULL,
    policy_receipt_ref TEXT NOT NULL,
    disposition TEXT NOT NULL,
    state TEXT NOT NULL CHECK (state IN ('reserved','adopted','indeterminate','refused')),
    adopted_receipt_id TEXT NOT NULL DEFAULT '',
    result_sha256 TEXT NOT NULL DEFAULT '',
    created_at REAL NOT NULL,
    UNIQUE(turn_id, broker_child_id)
);
CREATE TABLE IF NOT EXISTS tool_turn_commands (
    command_id TEXT PRIMARY KEY,
    turn_id TEXT NOT NULL REFERENCES tool_turns(turn_id),
    kind TEXT NOT NULL CHECK (kind IN ('start','reserve_model_step','reserve_tool_call','stop','revoke','reconcile')),
    request_sha256 TEXT NOT NULL,
    result_sha256 TEXT NOT NULL,
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS tool_turn_transitions (
    id TEXT PRIMARY KEY,
    turn_id TEXT NOT NULL REFERENCES tool_turns(turn_id),
    ordinal INTEGER NOT NULL CHECK (ordinal > 0),
    from_state TEXT NOT NULL,
    to_state TEXT NOT NULL,
    code TEXT NOT NULL DEFAULT '',
    evidence_sha256 TEXT NOT NULL,
    created_at REAL NOT NULL,
    UNIQUE(turn_id, ordinal)
);
CREATE TRIGGER IF NOT EXISTS turn_capability_leases_no_delete
BEFORE DELETE ON turn_capability_leases BEGIN
    SELECT RAISE(ABORT, 'immutable turn capability lease');
END;
-- Step identity and frozen plan/lease material are immutable.  Receipt linkage is
-- deliberately a fenced lifecycle fact: it is filled once by the controller
-- after the separately owned route execution has durable evidence.
CREATE TRIGGER IF NOT EXISTS tool_turn_model_steps_no_update
BEFORE UPDATE ON tool_turn_model_steps
WHEN NEW.id IS NOT OLD.id
  OR NEW.turn_id IS NOT OLD.turn_id
  OR NEW.ordinal IS NOT OLD.ordinal
  OR NEW.operation_request_plan_id IS NOT OLD.operation_request_plan_id
  OR NEW.operation_request_plan_sha256 IS NOT OLD.operation_request_plan_sha256
  OR NEW.lease_sha256 IS NOT OLD.lease_sha256
  OR NEW.request_material_ref IS NOT OLD.request_material_ref
  OR (OLD.route_execution_id != '' AND NEW.route_execution_id IS NOT OLD.route_execution_id)
  OR (OLD.child_receipt_id != '' AND NEW.child_receipt_id IS NOT OLD.child_receipt_id)
  OR (OLD.result_sha256 != '' AND NEW.result_sha256 IS NOT OLD.result_sha256)
  OR OLD.state NOT IN ('reserved','running')
  OR (OLD.state='reserved' AND NEW.state NOT IN ('running','indeterminate'))
  OR (OLD.state='running' AND NEW.state NOT IN ('receipted','failed','indeterminate'))
BEGIN
    SELECT RAISE(ABORT, 'immutable tool turn model step');
END;
CREATE TRIGGER IF NOT EXISTS tool_turn_model_steps_no_delete
BEFORE DELETE ON tool_turn_model_steps BEGIN
    SELECT RAISE(ABORT, 'immutable tool turn model step');
END;
-- The effect-child identity binds a pre-dispatch reservation.  Its one terminal
-- adoption/refusal/indeterminate transition is the durable restart truth.
CREATE TRIGGER IF NOT EXISTS tool_turn_effect_children_no_update
BEFORE UPDATE ON tool_turn_effect_children
WHEN NEW.id IS NOT OLD.id
  OR NEW.turn_id IS NOT OLD.turn_id
  OR NEW.tool_call_id IS NOT OLD.tool_call_id
  OR NEW.broker_child_id IS NOT OLD.broker_child_id
  OR NEW.owner_intent_receipt_ref IS NOT OLD.owner_intent_receipt_ref
  OR NEW.policy_receipt_ref IS NOT OLD.policy_receipt_ref
  OR OLD.state != 'reserved'
  OR NEW.state NOT IN ('adopted','indeterminate','refused')
  OR (NEW.state != 'adopted' AND (NEW.adopted_receipt_id != '' OR NEW.result_sha256 != ''))
BEGIN
    SELECT RAISE(ABORT, 'immutable tool turn effect child');
END;
CREATE TRIGGER IF NOT EXISTS tool_turn_effect_children_no_delete
BEFORE DELETE ON tool_turn_effect_children BEGIN
    SELECT RAISE(ABORT, 'immutable tool turn effect child');
END;
CREATE TRIGGER IF NOT EXISTS tool_turn_commands_no_update
BEFORE UPDATE ON tool_turn_commands BEGIN
    SELECT RAISE(ABORT, 'immutable tool turn command');
END;
CREATE TRIGGER IF NOT EXISTS tool_turn_commands_no_delete
BEFORE DELETE ON tool_turn_commands BEGIN
    SELECT RAISE(ABORT, 'immutable tool turn command');
END;
CREATE TRIGGER IF NOT EXISTS tool_turn_transitions_no_update
BEFORE UPDATE ON tool_turn_transitions BEGIN
    SELECT RAISE(ABORT, 'immutable tool turn transition');
END;
CREATE TRIGGER IF NOT EXISTS tool_turn_transitions_no_delete
BEFORE DELETE ON tool_turn_transitions BEGIN
    SELECT RAISE(ABORT, 'immutable tool turn transition');
END;

"""
