"""Inference routing evidence, request planning, private material, fallback and graph controllers.

Part 11 of 17 of SCHEMA_SQL, in execution order (holdspeak/db/schema/__init__.py)."""

SQL = """
-- HS-143-05: immutable, content-free routing evidence.  Resolution happens
-- from one SQLite snapshot before these rows are written; execution and
-- fallback never consult mutable assignment/profile heads again.
CREATE TABLE IF NOT EXISTS inference_route_plans (
    id TEXT PRIMARY KEY,
    sha256 TEXT NOT NULL UNIQUE,
    capability_id TEXT NOT NULL,
    capability_revision INTEGER NOT NULL CHECK (capability_revision > 0),
    capability_schema_sha256 TEXT NOT NULL,
    assignment_id TEXT NOT NULL,
    assignment_revision INTEGER NOT NULL CHECK (assignment_revision > 0),
    assignment_sha256 TEXT NOT NULL,
    inherited_from TEXT NOT NULL CHECK (inherited_from IN ('invocation','subject','capability','group','global','legacy_override')),
    retry_policy_id TEXT NOT NULL,
    retry_policy_revision INTEGER NOT NULL CHECK (retry_policy_revision > 0),
    operation_policy_revision TEXT NOT NULL,
    principal_policy_sha256 TEXT,
    payload_json TEXT NOT NULL,
    state TEXT NOT NULL DEFAULT 'frozen' CHECK (state='frozen'),
    deadline_at TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS inference_route_plan_entries (
    id TEXT PRIMARY KEY,
    plan_id TEXT NOT NULL REFERENCES inference_route_plans(id),
    route_leg_ordinal INTEGER NOT NULL CHECK (route_leg_ordinal BETWEEN 1 AND 4),
    profile_id TEXT NOT NULL,
    profile_revision INTEGER NOT NULL CHECK (profile_revision > 0),
    profile_schema_version INTEGER NOT NULL CHECK (profile_schema_version IN (1,2)),
    binding_id TEXT NOT NULL,
    binding_revision INTEGER NOT NULL CHECK (binding_revision > 0),
    deployment_head_id TEXT NOT NULL,
    deployment_configuration_revision INTEGER NOT NULL CHECK (deployment_configuration_revision > 0),
    deployment_revision_id TEXT NOT NULL,
    capability_manifest_sha256 TEXT NOT NULL,
    boundary TEXT NOT NULL CHECK (boundary IN ('local','private_network','mesh','cloud')),
    context_support_json TEXT NOT NULL,
    UNIQUE (plan_id, route_leg_ordinal)
);
CREATE INDEX IF NOT EXISTS idx_inference_route_plan_entries_profile
    ON inference_route_plan_entries(profile_id, profile_revision);
CREATE TABLE IF NOT EXISTS inference_route_plan_commands (
    command_id TEXT PRIMARY KEY,
    request_sha256 TEXT NOT NULL,
    plan_id TEXT NOT NULL REFERENCES inference_route_plans(id),
    plan_sha256 TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS inference_route_plan_commands_no_update
BEFORE UPDATE ON inference_route_plan_commands BEGIN
    SELECT RAISE(ABORT, 'immutable inference route command');
END;
CREATE TRIGGER IF NOT EXISTS inference_route_plan_commands_no_delete
BEFORE DELETE ON inference_route_plan_commands BEGIN
    SELECT RAISE(ABORT, 'immutable inference route command');
END;
CREATE TABLE IF NOT EXISTS inference_route_plan_authority_evidence (
    plan_id TEXT PRIMARY KEY REFERENCES inference_route_plans(id),
    capability_definition_json TEXT NOT NULL,
    capability_definition_sha256 TEXT NOT NULL,
    retry_policy_definition_json TEXT NOT NULL,
    retry_policy_definition_sha256 TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS inference_route_plan_authority_no_update
BEFORE UPDATE ON inference_route_plan_authority_evidence BEGIN
    SELECT RAISE(ABORT, 'immutable inference route authority evidence');
END;
CREATE TRIGGER IF NOT EXISTS inference_route_plan_authority_no_delete
BEFORE DELETE ON inference_route_plan_authority_evidence BEGIN
    SELECT RAISE(ABORT, 'immutable inference route authority evidence');
END;
CREATE TABLE IF NOT EXISTS inference_route_plan_principal_evidence (
    plan_id TEXT PRIMARY KEY REFERENCES inference_route_plans(id),
    payload_json TEXT NOT NULL,
    sha256 TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS inference_route_plan_principal_evidence_no_update
BEFORE UPDATE ON inference_route_plan_principal_evidence BEGIN
    SELECT RAISE(ABORT, 'immutable inference route principal evidence');
END;
CREATE TRIGGER IF NOT EXISTS inference_route_plan_principal_evidence_no_delete
BEFORE DELETE ON inference_route_plan_principal_evidence BEGIN
    SELECT RAISE(ABORT, 'immutable inference route principal evidence');
END;
CREATE TABLE IF NOT EXISTS inference_route_plan_preflight_evidence (
    plan_id TEXT NOT NULL REFERENCES inference_route_plans(id),
    route_leg_ordinal INTEGER NOT NULL CHECK (route_leg_ordinal BETWEEN 1 AND 4),
    eligibility TEXT NOT NULL CHECK (eligibility IN ('executable','known_preflight_unavailable')),
    reason_code TEXT,
    PRIMARY KEY (plan_id, route_leg_ordinal)
);
CREATE TRIGGER IF NOT EXISTS inference_route_plan_preflight_no_update
BEFORE UPDATE ON inference_route_plan_preflight_evidence BEGIN
    SELECT RAISE(ABORT, 'immutable inference route preflight evidence');
END;
CREATE TRIGGER IF NOT EXISTS inference_route_plan_preflight_no_delete
BEFORE DELETE ON inference_route_plan_preflight_evidence BEGIN
    SELECT RAISE(ABORT, 'immutable inference route preflight evidence');
END;

-- Private request planning retains hashes and frozen per-leg eligibility, not
-- owner material.  Story 06 consumes these rows but owns controller advance.
CREATE TABLE IF NOT EXISTS inference_operation_route_request_plans (
    id TEXT PRIMARY KEY,
    sha256 TEXT NOT NULL UNIQUE,
    route_plan_id TEXT NOT NULL REFERENCES inference_route_plans(id),
    operation_id TEXT NOT NULL,
    evidence_provider_id TEXT NOT NULL,
    evidence_provider_revision INTEGER NOT NULL CHECK (evidence_provider_revision > 0),
    planning_reference TEXT NOT NULL,
    admission_evidence_ref TEXT NOT NULL,
    admission_evidence_sha256 TEXT NOT NULL,
    material_snapshot_sha256 TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    deadline_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS inference_operation_route_request_plan_entries (
    id TEXT PRIMARY KEY,
    operation_plan_id TEXT NOT NULL REFERENCES inference_operation_route_request_plans(id),
    route_leg_ordinal INTEGER NOT NULL CHECK (route_leg_ordinal BETWEEN 1 AND 4),
    eligibility TEXT NOT NULL CHECK (eligibility IN ('executable','known_preflight_unavailable','known_context_overflow')),
    reason_code TEXT,
    admitted_request_id TEXT,
    admitted_request_sha256 TEXT,
    context_plan_sha256 TEXT,
    serialized_request_sha256 TEXT,
    CHECK (
      (eligibility='executable' AND reason_code IS NULL AND admitted_request_id IS NOT NULL AND admitted_request_sha256 IS NOT NULL AND context_plan_sha256 IS NOT NULL AND serialized_request_sha256 IS NOT NULL) OR
      (eligibility<>'executable' AND reason_code IS NOT NULL AND admitted_request_id IS NULL AND admitted_request_sha256 IS NULL AND context_plan_sha256 IS NULL AND serialized_request_sha256 IS NULL)
    ),
    UNIQUE (operation_plan_id, route_leg_ordinal)
);
CREATE TABLE IF NOT EXISTS inference_operation_route_request_plan_commands (
    command_id TEXT PRIMARY KEY,
    request_sha256 TEXT NOT NULL,
    route_plan_id TEXT NOT NULL REFERENCES inference_route_plans(id),
    route_plan_sha256 TEXT NOT NULL,
    operation_plan_id TEXT NOT NULL REFERENCES inference_operation_route_request_plans(id),
    operation_plan_sha256 TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS inference_operation_route_commands_no_update
BEFORE UPDATE ON inference_operation_route_request_plan_commands BEGIN
    SELECT RAISE(ABORT, 'immutable operation route command');
END;
CREATE TRIGGER IF NOT EXISTS inference_operation_route_commands_no_delete
BEFORE DELETE ON inference_operation_route_request_plan_commands BEGIN
    SELECT RAISE(ABORT, 'immutable operation route command');
END;
CREATE UNIQUE INDEX IF NOT EXISTS idx_inference_operation_route_request_operation
    ON inference_operation_route_request_plans(operation_id);
CREATE TABLE IF NOT EXISTS inference_operation_route_attempt_budget_evidence (
    operation_plan_id TEXT PRIMARY KEY REFERENCES inference_operation_route_request_plans(id),
    provider_id TEXT NOT NULL,
    provider_revision INTEGER NOT NULL CHECK (provider_revision > 0),
    evidence_ref TEXT NOT NULL,
    material_snapshot_sha256 TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    sha256 TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS inference_operation_route_attempt_budgets_no_update
BEFORE UPDATE ON inference_operation_route_attempt_budget_evidence BEGIN
    SELECT RAISE(ABORT, 'immutable operation route attempt budgets');
END;
CREATE TRIGGER IF NOT EXISTS inference_operation_route_attempt_budgets_no_delete
BEFORE DELETE ON inference_operation_route_attempt_budget_evidence BEGIN
    SELECT RAISE(ABORT, 'immutable operation route attempt budgets');
END;

-- HS-143-07: application-owned private material and exact per-leg request
-- serialization. These rows are local-only and immutable: route planning may
-- reconstruct their hashes, but sync and public route receipts never expose
-- prompt/context bytes.
CREATE TABLE IF NOT EXISTS inference_adoption_material_snapshots (
    planning_reference TEXT PRIMARY KEY,
    capability_id TEXT NOT NULL,
    operation_id TEXT NOT NULL UNIQUE,
    contract TEXT NOT NULL,
    contract_revision TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    payload_sha256 TEXT NOT NULL,
    material_snapshot_sha256 TEXT NOT NULL UNIQUE,
    reserved_output_tokens INTEGER NOT NULL CHECK (reserved_output_tokens >= 0),
    reserved_tool_calls INTEGER NOT NULL CHECK (reserved_tool_calls >= 0),
    created_at TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS inference_adoption_material_no_update
BEFORE UPDATE ON inference_adoption_material_snapshots BEGIN
    SELECT RAISE(ABORT, 'immutable inference adoption material');
END;
CREATE TRIGGER IF NOT EXISTS inference_adoption_material_no_delete
BEFORE DELETE ON inference_adoption_material_snapshots BEGIN
    SELECT RAISE(ABORT, 'immutable inference adoption material');
END;
CREATE TABLE IF NOT EXISTS inference_adoption_route_evidence (
    evidence_ref TEXT PRIMARY KEY,
    planning_reference TEXT NOT NULL UNIQUE
        REFERENCES inference_adoption_material_snapshots(planning_reference),
    operation_id TEXT NOT NULL UNIQUE,
    capability_id TEXT NOT NULL,
    material_snapshot_sha256 TEXT NOT NULL,
    evidence_json TEXT NOT NULL,
    evidence_sha256 TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS inference_adoption_route_evidence_no_update
BEFORE UPDATE ON inference_adoption_route_evidence BEGIN
    SELECT RAISE(ABORT, 'immutable inference adoption route evidence');
END;
CREATE TRIGGER IF NOT EXISTS inference_adoption_route_evidence_no_delete
BEFORE DELETE ON inference_adoption_route_evidence BEGIN
    SELECT RAISE(ABORT, 'immutable inference adoption route evidence');
END;
CREATE TABLE IF NOT EXISTS inference_adoption_composites (
    composite_id TEXT PRIMARY KEY,
    command_id TEXT NOT NULL UNIQUE,
    request_sha256 TEXT NOT NULL,
    operation_plan_ids_json TEXT NOT NULL,
    result_sha256 TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS inference_adoption_composites_no_update
BEFORE UPDATE ON inference_adoption_composites BEGIN
    SELECT RAISE(ABORT, 'immutable inference adoption composite');
END;
CREATE TRIGGER IF NOT EXISTS inference_adoption_composites_no_delete
BEFORE DELETE ON inference_adoption_composites BEGIN
    SELECT RAISE(ABORT, 'immutable inference adoption composite');
END;
CREATE TABLE IF NOT EXISTS inference_adoption_attempt_results (
    attempt_id TEXT PRIMARY KEY,
    child_invocation_id TEXT NOT NULL UNIQUE,
    producer_result_ref TEXT NOT NULL UNIQUE,
    result_json TEXT NOT NULL,
    result_sha256 TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS inference_adoption_attempt_results_no_update
BEFORE UPDATE ON inference_adoption_attempt_results BEGIN
    SELECT RAISE(ABORT, 'immutable inference adoption attempt result');
END;
CREATE TRIGGER IF NOT EXISTS inference_adoption_attempt_results_no_delete
BEFORE DELETE ON inference_adoption_attempt_results BEGIN
    SELECT RAISE(ABORT, 'immutable inference adoption attempt result');
END;

-- HS-143-06: one durable fallback-controller state machine above the physical
-- inference waist.  A row is the terminal-election authority for one frozen
-- operation request plan; attempts are reservations, not provider retries.
CREATE TABLE IF NOT EXISTS inference_route_executions (
    id TEXT PRIMARY KEY,
    route_plan_id TEXT NOT NULL REFERENCES inference_route_plans(id),
    route_plan_sha256 TEXT NOT NULL,
    operation_plan_id TEXT NOT NULL UNIQUE REFERENCES inference_operation_route_request_plans(id),
    operation_plan_sha256 TEXT NOT NULL,
    budget_evidence_provider_id TEXT NOT NULL,
    budget_evidence_provider_revision INTEGER NOT NULL CHECK (budget_evidence_provider_revision > 0),
    budget_evidence_sha256 TEXT NOT NULL,
    state TEXT NOT NULL CHECK (state IN ('active','stopping','stopped','terminal')),
    revision INTEGER NOT NULL CHECK (revision > 0),
    total_attempt_limit INTEGER NOT NULL CHECK (total_attempt_limit > 0),
    per_leg_attempt_limit INTEGER NOT NULL CHECK (per_leg_attempt_limit > 0),
    attempts_reserved INTEGER NOT NULL DEFAULT 0 CHECK (attempts_reserved >= 0),
    token_budget INTEGER,
    cost_budget INTEGER,
    tool_call_budget INTEGER,
    tokens_reserved INTEGER NOT NULL DEFAULT 0 CHECK (tokens_reserved >= 0),
    cost_reserved INTEGER NOT NULL DEFAULT 0 CHECK (cost_reserved >= 0),
    tool_calls_reserved INTEGER NOT NULL DEFAULT 0 CHECK (tool_calls_reserved >= 0),
    stop_requested INTEGER NOT NULL DEFAULT 0 CHECK (stop_requested IN (0,1)),
    stop_command_id TEXT UNIQUE,
    terminal_disposition TEXT CHECK (terminal_disposition IS NULL OR terminal_disposition IN ('preflight_unavailable','known_no_generation_transient','dispatch_outcome_unknown','provider_permanent','invalid_typed_output','invalid_tool_call','context_overflow','local_capacity_unavailable','tool_unavailable_or_stale','permission_denied','policy_refused','owner_cancelled','deadline_exhausted','physical_outcome_unknown','effect_indeterminate','owner_terminal')),
    terminal_outcome TEXT CHECK (terminal_outcome IS NULL OR terminal_outcome IN ('succeeded','failed','refused','cancelled','indeterminate')),
    result_ref TEXT,
    winning_attempt_id TEXT,
    started_at TEXT NOT NULL,
    terminal_at TEXT,
    CHECK (
      (state='active' AND stop_requested=0 AND stop_command_id IS NULL AND terminal_disposition IS NULL AND terminal_outcome IS NULL AND winning_attempt_id IS NULL AND terminal_at IS NULL) OR
      (state='stopping' AND stop_requested=1 AND stop_command_id IS NOT NULL AND terminal_disposition IS NULL AND terminal_outcome IS NULL AND winning_attempt_id IS NULL AND terminal_at IS NULL) OR
      (state='stopped' AND stop_requested=1 AND stop_command_id IS NOT NULL AND terminal_disposition='owner_cancelled' AND terminal_outcome='cancelled' AND winning_attempt_id IS NULL AND terminal_at IS NOT NULL) OR
      (state='terminal' AND terminal_outcome IS NOT NULL AND terminal_at IS NOT NULL)
    ),
    CHECK (
      terminal_outcome<>'succeeded' OR
      (winning_attempt_id IS NOT NULL AND result_ref IS NOT NULL AND result_ref<>'')
    )
);
CREATE TRIGGER IF NOT EXISTS inference_route_execution_stop_provenance_immutable
BEFORE UPDATE ON inference_route_executions
WHEN OLD.stop_command_id IS NOT NULL AND NEW.stop_command_id IS NOT OLD.stop_command_id
BEGIN
    SELECT RAISE(ABORT, 'immutable inference route Stop provenance');
END;
CREATE TABLE IF NOT EXISTS inference_route_attempts (
    id TEXT PRIMARY KEY,
    execution_id TEXT NOT NULL REFERENCES inference_route_executions(id),
    route_leg_ordinal INTEGER NOT NULL CHECK (route_leg_ordinal BETWEEN 1 AND 4),
    physical_attempt_ordinal INTEGER NOT NULL CHECK (physical_attempt_ordinal > 0),
    leg_attempt_ordinal INTEGER NOT NULL CHECK (leg_attempt_ordinal > 0),
    purpose TEXT NOT NULL CHECK (purpose IN ('primary','retry','fallback','compatibility')),
    deployment_revision_id TEXT NOT NULL,
    boundary TEXT NOT NULL CHECK (boundary IN ('local','private_network','mesh','cloud')),
    state TEXT NOT NULL CHECK (state IN ('reserved','admitted','dispatch_intent','terminal')),
    child_invocation_id TEXT NOT NULL UNIQUE,
    reservation_command_id TEXT NOT NULL UNIQUE,
    admission_nonce_sha256 TEXT NOT NULL,
    budget_evidence_provider_id TEXT NOT NULL,
    budget_evidence_provider_revision INTEGER NOT NULL CHECK (budget_evidence_provider_revision > 0),
    budget_evidence_sha256 TEXT NOT NULL,
    child_operation_id TEXT UNIQUE,
    disposition TEXT CHECK (disposition IS NULL OR disposition IN ('preflight_unavailable','known_no_generation_transient','dispatch_outcome_unknown','provider_permanent','invalid_typed_output','invalid_tool_call','context_overflow','local_capacity_unavailable','tool_unavailable_or_stale','permission_denied','policy_refused','owner_cancelled','deadline_exhausted','physical_outcome_unknown','effect_indeterminate','owner_terminal')),
    outcome TEXT CHECK (outcome IS NULL OR outcome IN ('succeeded','failed','refused','cancelled','indeterminate')),
    result_ref TEXT,
    child_receipt_sha256 TEXT,
    disposition_evidence_json TEXT,
    disposition_evidence_sha256 TEXT,
    classifier_revision TEXT,
    send_phase TEXT CHECK (send_phase IS NULL OR send_phase IN ('pre_send','dispatch_intent','provider_no_generation','provider_returned')),
    reserved_token_budget INTEGER NOT NULL DEFAULT 0 CHECK (reserved_token_budget >= 0),
    reserved_cost_budget INTEGER NOT NULL DEFAULT 0 CHECK (reserved_cost_budget >= 0),
    reserved_tool_call_budget INTEGER NOT NULL DEFAULT 0 CHECK (reserved_tool_call_budget >= 0),
    reserved_at TEXT NOT NULL,
    admitted_at TEXT,
    dispatch_intent_at TEXT,
    terminal_at TEXT,
    CHECK (
      (state='terminal' AND disposition IS NOT NULL AND outcome IS NOT NULL
       AND disposition_evidence_sha256 IS NOT NULL AND terminal_at IS NOT NULL
       AND (
         child_receipt_sha256 IS NOT NULL OR
         (disposition='dispatch_outcome_unknown' AND outcome='indeterminate'
          AND send_phase='dispatch_intent')
       )) OR
      (state<>'terminal' AND disposition IS NULL AND outcome IS NULL
       AND child_receipt_sha256 IS NULL AND disposition_evidence_sha256 IS NULL
       AND classifier_revision IS NULL AND send_phase IS NULL AND terminal_at IS NULL)
    ),
    UNIQUE (execution_id, physical_attempt_ordinal),
    UNIQUE (execution_id, route_leg_ordinal, leg_attempt_ordinal)
);
CREATE INDEX IF NOT EXISTS idx_inference_route_attempts_execution
    ON inference_route_attempts(execution_id, physical_attempt_ordinal);
CREATE TRIGGER IF NOT EXISTS inference_route_attempt_authority_immutable
BEFORE UPDATE ON inference_route_attempts
WHEN NEW.execution_id IS NOT OLD.execution_id
  OR NEW.route_leg_ordinal IS NOT OLD.route_leg_ordinal
  OR NEW.physical_attempt_ordinal IS NOT OLD.physical_attempt_ordinal
  OR NEW.leg_attempt_ordinal IS NOT OLD.leg_attempt_ordinal
  OR NEW.purpose IS NOT OLD.purpose
  OR NEW.deployment_revision_id IS NOT OLD.deployment_revision_id
  OR NEW.boundary IS NOT OLD.boundary
  OR NEW.child_invocation_id IS NOT OLD.child_invocation_id
  OR NEW.reservation_command_id IS NOT OLD.reservation_command_id
  OR NEW.admission_nonce_sha256 IS NOT OLD.admission_nonce_sha256
  OR NEW.budget_evidence_provider_id IS NOT OLD.budget_evidence_provider_id
  OR NEW.budget_evidence_provider_revision IS NOT OLD.budget_evidence_provider_revision
  OR NEW.budget_evidence_sha256 IS NOT OLD.budget_evidence_sha256
  OR NEW.reserved_token_budget IS NOT OLD.reserved_token_budget
  OR NEW.reserved_cost_budget IS NOT OLD.reserved_cost_budget
  OR NEW.reserved_tool_call_budget IS NOT OLD.reserved_tool_call_budget
BEGIN
    SELECT RAISE(ABORT, 'immutable inference route attempt authority');
END;
CREATE TRIGGER IF NOT EXISTS inference_route_attempt_terminal_immutable
BEFORE UPDATE ON inference_route_attempts
WHEN OLD.state='terminal'
BEGIN
    SELECT RAISE(ABORT, 'immutable terminal inference route attempt');
END;
CREATE TABLE IF NOT EXISTS inference_route_execution_skips (
    id TEXT PRIMARY KEY,
    execution_id TEXT NOT NULL REFERENCES inference_route_executions(id),
    route_leg_ordinal INTEGER NOT NULL CHECK (route_leg_ordinal BETWEEN 1 AND 4),
    disposition TEXT NOT NULL CHECK (disposition IN ('preflight_unavailable','context_overflow')),
    reason_code TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE (execution_id, route_leg_ordinal)
);
CREATE TRIGGER IF NOT EXISTS inference_route_execution_skips_no_update
BEFORE UPDATE ON inference_route_execution_skips BEGIN
    SELECT RAISE(ABORT, 'immutable inference route execution skip');
END;
CREATE TRIGGER IF NOT EXISTS inference_route_execution_skips_no_delete
BEFORE DELETE ON inference_route_execution_skips BEGIN
    SELECT RAISE(ABORT, 'immutable inference route execution skip');
END;
CREATE TABLE IF NOT EXISTS inference_route_execution_commands (
    command_id TEXT PRIMARY KEY,
    action TEXT NOT NULL CHECK (action IN ('start','reserve','claim','bind','dispatch_intent','settle','stop','reconcile')),
    request_sha256 TEXT NOT NULL,
    execution_id TEXT NOT NULL REFERENCES inference_route_executions(id),
    effect_json TEXT NOT NULL,
    effect_sha256 TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS inference_route_execution_commands_no_update
BEFORE UPDATE ON inference_route_execution_commands BEGIN
    SELECT RAISE(ABORT, 'immutable inference route execution command');
END;
CREATE TRIGGER IF NOT EXISTS inference_route_execution_commands_no_delete
BEFORE DELETE ON inference_route_execution_commands BEGIN
    SELECT RAISE(ABORT, 'immutable inference route execution command');
END;
CREATE TABLE IF NOT EXISTS inference_route_execution_transitions (
    transition_id TEXT PRIMARY KEY,
    execution_id TEXT NOT NULL REFERENCES inference_route_executions(id),
    ordinal INTEGER NOT NULL CHECK (ordinal > 0),
    action TEXT NOT NULL CHECK (action IN ('start','reserve','stop','settle','reconcile')),
    command_id TEXT NOT NULL UNIQUE REFERENCES inference_route_execution_commands(command_id),
    prior_revision INTEGER NOT NULL CHECK (prior_revision >= 0),
    post_revision INTEGER NOT NULL CHECK (post_revision > 0),
    prior_state TEXT NOT NULL CHECK (prior_state IN ('none','active','stopping','stopped','terminal')),
    post_state TEXT NOT NULL CHECK (post_state IN ('active','stopping','stopped','terminal')),
    effect_sha256 TEXT NOT NULL,
    previous_sha256 TEXT NOT NULL,
    sha256 TEXT NOT NULL UNIQUE,
    UNIQUE (execution_id, ordinal),
    UNIQUE (execution_id, post_revision)
);
CREATE TRIGGER IF NOT EXISTS inference_route_execution_transitions_no_update
BEFORE UPDATE ON inference_route_execution_transitions BEGIN
    SELECT RAISE(ABORT, 'immutable inference route execution transition');
END;
CREATE TRIGGER IF NOT EXISTS inference_route_execution_transitions_no_delete
BEFORE DELETE ON inference_route_execution_transitions BEGIN
    SELECT RAISE(ABORT, 'immutable inference route execution transition');
END;

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
