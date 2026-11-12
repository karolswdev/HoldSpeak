"""Schema SQL and version constant for the HoldSpeak persistence layer.

Extracted from core.py (HS-117-10) so the schema definition is navigable
independently of the Database container. The SQL lives in one module per
domain; SCHEMA_SQL joins only the live declarations in execution order.

Retire a table by declaring it in RETIRED_TABLES and moving its DDL, indexes
and triggers to _parked/. Nothing live imports the parked SQL. Reconcile
compares only the live shape and never drops absent tables or their rows.
"""

from . import (
    activity_dictation,
    cadence_agents,
    decisions_projects,
    inference_routing,
    inference_turns,
    kernel_journal,
    ledger_models,
    library,
    meetings,
    memory,
    primitives,
    programs,
    rooms,
    steward,
    threads,
    workbench,
    working_context,
)

# Informational stamp only. Nothing gates on it: `reconcile_schema` detects
# missing tables and columns by comparing the live database against this
# SCHEMA_SQL shape directly, so you do NOT need to bump this to have a shape
# change take effect. Just edit the SQL in its domain module; the reconcile
# applies it on open.

SCHEMA_VERSION = 92  # informational; 92 (Codex on #2051, additive): phone_devices.pair_origin; 91 (PG-DIRECTION DIR4, additive): held_later; 90 (PG-DIRECTION DIR1, additive): briefing_packages, program_checkpoints.via; 89 (PG-LANG fields, additive): programs.review_depth, planner_engine, budget_tokens, night_json, within_json, delivery_ref, rounds_before_start; program_steps.budget_tokens; program_rounds; 88 (PG-REQ, additive): program_requirements and its index; 87 (PG14, additive): workbenches.program_template, program_control, program_runs_on_json, program_may_call, program_may_handoff; 86→87: phone_devices, phone_messages, phone_calls, phone_events, programs.may_call, program_steps.may_call (Phone 2026-10-28); 86 (PG19, additive): programs.default_runs_on_json, allowed_profiles_json, may_handoff, usage_warning_share; program_steps.runs_on_json, handoffs_json; 85→86: programs, program_steps, program_checkpoints (Programs 2026-10-28); 84→85: desk_windows, desk_window_desk (PHILO-16 16b); 83→84: agent_session_events (PHILO-14 C0); 82→83: memory facts, entities, fact links, jobs (memory slice 3)

# The execution order. A table must come after every table it references.
PARTS = (
    meetings,
    decisions_projects,
    activity_dictation,
    primitives,
    working_context,
    library,
    workbench,
    cadence_agents,
    kernel_journal,
    ledger_models,
    inference_routing,
    inference_turns,
    threads,
    rooms,
    steward,
    memory,
    programs,
)

# One declaration of retired history. Fresh installs omit it; old files keep it.
RETIRED_TABLES = frozenset({
    "inference_adoption_attempt_results",
    "inference_adoption_composites",
    "inference_adoption_material_snapshots",
    "inference_adoption_route_evidence",
    "inference_operation_route_attempt_budget_evidence",
    "inference_operation_route_request_plan_commands",
    "inference_operation_route_request_plan_entries",
    "inference_operation_route_request_plans",
    "inference_parent_route_bundle_members",
    "inference_parent_route_bundles",
    "inference_parent_stop_handoff_executions",
    "inference_parent_stop_handoff_settlements",
    "inference_parent_stop_handoffs",
    "inference_route_attempts",
    "inference_route_execution_commands",
    "inference_route_execution_skips",
    "inference_route_execution_transitions",
    "inference_route_executions",
    "inference_route_plan_authority_evidence",
    "inference_route_plan_commands",
    "inference_route_plan_entries",
    "inference_route_plan_preflight_evidence",
    "inference_route_plan_principal_evidence",
    "inference_route_plans",
    "reaction_event_projections",
    "tool_turn_commands",
    "tool_turn_effect_children",
    "tool_turn_model_steps",
    "tool_turn_tool_call_results",
    "tool_turn_tool_calls",
    "tool_turn_transitions",
    "tool_turns",
    "turn_capability_leases",
})

# SQL Schema
SCHEMA_SQL = "".join(part.SQL for part in PARTS)

__all__ = ["SCHEMA_SQL", "SCHEMA_VERSION", "RETIRED_TABLES"]
