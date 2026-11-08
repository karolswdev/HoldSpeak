"""Schema SQL and version constant for the HoldSpeak persistence layer.

Extracted from core.py (HS-117-10) so the schema definition is navigable
independently of the Database container. The SQL lives in one module per
domain; SCHEMA_SQL joins them in execution order, byte for byte the text the
single schema.py held (tests/unit/test_schema_package.py).
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

SCHEMA_VERSION = 91  # informational; 91 (PG-DIRECTION DIR4, additive): held_later; 90 (PG-DIRECTION DIR1, additive): briefing_packages, program_checkpoints.via; 89 (PG-LANG fields, additive): programs.review_depth, planner_engine, budget_tokens, night_json, within_json, delivery_ref, rounds_before_start; program_steps.budget_tokens; program_rounds; 88 (PG-REQ, additive): program_requirements and its index; 87 (PG14, additive): workbenches.program_template, program_control, program_runs_on_json, program_may_call, program_may_handoff; 86→87: phone_devices, phone_messages, phone_calls, phone_events, programs.may_call, program_steps.may_call (Phone 2026-10-28); 86 (PG19, additive): programs.default_runs_on_json, allowed_profiles_json, may_handoff, usage_warning_share; program_steps.runs_on_json, handoffs_json; 85→86: programs, program_steps, program_checkpoints (Programs 2026-10-28); 84→85: desk_windows, desk_window_desk (PHILO-16 16b); 83→84: agent_session_events (PHILO-14 C0); 82→83: memory facts, entities, fact links, jobs (memory slice 3)

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

# SQL Schema
SCHEMA_SQL = "".join(part.SQL for part in PARTS)

__all__ = ["SCHEMA_SQL", "SCHEMA_VERSION"]
