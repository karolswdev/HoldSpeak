"""Keep route work off the hub event loop.

The owner: "I open a window and often need to wait 2-3 seconds. Even on local"
(2026-10-28).

The guard walks every Python route under ``holdspeak/web``. A synchronous
route runs in Starlette's threadpool. An async route is allowed here only
while its sibling R1 lane still owns the conversion; the final R1 PR removes
the allowlist and turns on the strict empty-list check.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import Any

import anyio
import pytest

from holdspeak.runtime import composition

_REPO = Path(__file__).resolve().parents[2]
_WEB = _REPO / "holdspeak" / "web"
_ROUTE_DECORATORS = frozenset({
    "get", "post", "put", "patch", "delete", "head", "options",
    "api_route", "route", "websocket",
})

# Generated from the post-conversion census. Each entry is a sibling R1 lane.
ALLOWLIST: dict[str, frozenset[str]] = {

    'web/routes/activity/candidates.py': frozenset(('create', 'delete', 'list_candidates', 'preview', 'start', 'update')),
    'web/routes/activity/enrichment.py': frozenset(('annotations', 'briefing', 'clear_annotations', 'clear_candidates', 'connectors', 'dry_run', 'github_preview', 'github_run', 'ingest', 'jira_preview', 'jira_run', 'pipeline', 'runs', 'update_connector')),
    'web/routes/activity/ledger.py': frozenset(('delete_domain', 'delete_records', 'domain', 'records', 'refresh', 'settings', 'status')),
    'web/routes/activity/nudges.py': frozenset(('clear', 'dismiss', 'list_nudges', 'select')),
    'web/routes/activity/plugin_jobs.py': frozenset(('cancel', 'list_jobs', 'process', 'retry', 'summary')),
    'web/routes/activity/rules.py': frozenset(('apply', 'create', 'delete', 'list_rules', 'preview', 'update')),
    'web/routes/authority.py': frozenset(('api_authority_policy', 'api_grant_uses', 'api_list_grants', 'api_revoke_grant')),
    'web/routes/automations.py': frozenset(('baseline_watch', 'compile_practice_recipe', 'configure_resourceful_policy', 'create_reaction', 'create_watch', 'create_workbench_automation', 'get_practice_recipe', 'get_resourceful_policy', 'list_events', 'list_practice_recipes', 'list_presets', 'list_reactions', 'list_watches', 'list_workbench_automations', 'resourceful_history', 'set_reaction_enabled', 'set_watch_enabled', 'set_workbench_automation_enabled', 'test_watch', 'test_workbench_automation', 'workbench_automation_history')),
    'web/routes/cadence.py': frozenset(('audit', 'brief', 'close', 'closeout', 'closeout_apply', 'history', 'kill', 'loops', 'run_now', 'snooze', 'status')),
    'web/routes/calendar_events.py': frozenset(('link_event', 'list_events', 'unlink_event')),
    'web/routes/calendar_sources.py': frozenset(('list_sources',)),
    'web/routes/calls.py': frozenset(('api_call_get', 'api_calls_list')),
    'web/routes/connections.py': frozenset(('list_connections',)),
    'web/routes/constitutional.py': frozenset(('api_context_history', 'api_get_context')),
    'web/routes/core.py': frozenset(('api_state', 'health')),
    'web/routes/decision_records.py': frozenset(('carry_record', 'create_from_desk', 'dispute_record', 'get_record', 'list_records', 'records_due_for_review', 'records_for_source', 'records_for_work', 'search_records', 'supersede_record')),
    'web/routes/decisions.py': frozenset(('accept_decision', 'get_decision', 'get_decision_moment', 'list_decisions', 'promote_decision', 'reject_decision', 'supersede_decision')),
    'web/routes/delivery_node.py': frozenset(('api_delivery_nodes', 'api_node_commands', 'api_node_disconnect', 'api_node_heartbeat', 'api_node_hello')),
    'web/routes/desk_actuators.py': frozenset(('api_desk_actuators_status',)),
    'web/routes/desk_seed.py': frozenset(('api_desk_reset', 'api_desk_seed')),
    'web/routes/dictation/agent.py': frozenset(('api_dictation_agent_context', 'api_dictation_agent_context_clear', 'api_dictation_agent_context_summarize', 'api_dictation_agent_hooks', 'api_dictation_project_context')),
    'web/routes/dictation/blocks.py': frozenset(('api_dictation_block_templates', 'api_dictation_blocks_create', 'api_dictation_blocks_delete', 'api_dictation_blocks_list', 'api_dictation_blocks_update')),
    'web/routes/dictation/floor.py': frozenset(('api_audio_floor', 'api_audio_floor_claim', 'api_audio_floor_release')),
    'web/routes/dictation/intents.py': frozenset(('api_get_intent_controls', 'api_preview_intent_route', 'api_set_intent_override', 'api_set_intent_profile')),
    'web/routes/dictation/kb.py': frozenset(('api_dictation_project_kb_delete', 'api_dictation_project_kb_get', 'api_dictation_project_kb_put', 'api_dictation_project_kb_starter')),
    'web/routes/dictation/pipeline.py': frozenset(('api_dictation_corrections_clear', 'api_dictation_corrections_delete', 'api_dictation_corrections_list', 'api_dictation_corrections_record', 'api_dictation_journal_clear', 'api_dictation_journal_correct', 'api_dictation_journal_delete', 'api_dictation_journal_list', 'api_dictation_journal_update', 'api_dictation_learning_digest')),
    'web/routes/dictation/project_docs.py': frozenset(('api_dictation_project_doc_suggestion_apply', 'api_dictation_project_doc_suggestion_dismiss', 'api_dictation_project_doc_suggestion_get', 'api_dictation_project_hs_get', 'api_dictation_project_hs_put')),
    'web/routes/follow_through.py': frozenset(('board', 'commit_decision', 'complete')),
    'web/routes/front_door.py': frozenset(('get_apply',)),
    'web/routes/inference_assignments.py': frozenset(('get_assignments',)),
    'web/routes/mcp_http.py': frozenset(('get_remote_settings', 'revoke_credential')),
    'web/routes/meeting_import.py': frozenset(('import_recording', 'transcribe_meeting')),
    'web/routes/meetings/action_items.py': frozenset(('api_edit_action_item', 'api_edit_global_action_item', 'api_list_all_action_items', 'api_review_global_action_item', 'api_update_action_item', 'api_update_action_item_review', 'api_update_global_action_item')),
    'web/routes/meetings/aftercare.py': frozenset(('api_aftercare_file_issue', 'api_decide_meeting_proposal', 'api_export_meeting_to_slack', 'api_get_meeting_aftercare', 'api_get_meeting_followup_draft', 'api_get_meeting_proposals')),
    'web/routes/meetings/crud.py': frozenset(('api_delete_meeting', 'api_export_meeting', 'api_get_meeting', 'api_list_meetings', 'api_list_unread_ready_meetings', 'api_mark_meeting_ready_read', 'api_meeting_facets', 'api_meeting_sync_conflicts', 'api_recover_meeting_capture', 'api_resolve_meeting_sync_conflict', 'api_restore_meeting')),
    'web/routes/meetings/insights.py': frozenset(('api_get_meeting_artifacts', 'api_get_meeting_intent_timeline', 'api_get_meeting_plugin_runs', 'api_get_meeting_prepared')),
    'web/routes/meetings/intel.py': frozenset(('api_get_meeting_intel_recovery', 'api_intel_queue_summary', 'api_list_intel_jobs', 'api_process_intel_jobs', 'api_skip_meeting_intel_recovery')),
    'web/routes/meetings/live.py': frozenset(('api_bookmark', 'api_meeting_start', 'api_update_meeting')),
    'web/routes/meetings/speakers.py': frozenset(('api_get_speaker', 'api_list_speakers', 'api_update_speaker')),
    'web/routes/memory.py': frozenset(('recall_memory',)),
    'web/routes/mesh.py': frozenset(('api_mesh_inbox', 'api_mesh_info', 'api_mesh_relay_claim', 'api_mesh_relay_complete', 'api_mesh_relay_fail')),
    'web/routes/missioncontrol.py': frozenset(('api_missioncontrol_rails_remote_events',)),
    'web/routes/model_library.py': frozenset(('get_model_library',)),
    'web/routes/monday_brief.py': frozenset(('generate', 'read_by_id', 'read_shelf', 'write_shelf')),
    'web/routes/primitives/_parked/decisions.py': frozenset(('api_list_desk_decisions',)),
    'web/routes/primitives/ask.py': frozenset(('api_ask_runs', 'api_cancel_ask', 'api_list_models')),
    'web/routes/primitives/chains.py': frozenset(('cancel', 'delete', 'get_', 'list_')),
    'web/routes/primitives/decisions.py': frozenset(('api_delete_decision', 'api_get_desk_decision', 'api_supersede_decision')),
    'web/routes/primitives/directories.py': frozenset(('api_delete_directory', 'api_file_member', 'api_get_directory', 'api_list_directories', 'api_list_directory_members', 'api_unfile_member')),
    'web/routes/primitives/invocations.py': frozenset(('api_cancel_invocation', 'api_get_invocation', 'api_list_invocations')),
    'web/routes/primitives/kbs.py': frozenset(('api_add_kb_member', 'api_delete_kb', 'api_get_kb', 'api_list_kb_members', 'api_list_kbs', 'api_remove_kb_member')),
    'web/routes/primitives/model_profiles.py': frozenset(('api_delete_model_profile', 'api_get_model_profile', 'api_list_model_profiles', 'api_unbind_model_profile')),
    'web/routes/primitives/note_outcomes.py': frozenset(('confirm', 'dismiss', 'read')),
    'web/routes/primitives/notes.py': frozenset(('api_get_note', 'api_list_notes')),
    'web/routes/primitives/profiles.py': frozenset(('api_create_profile', 'api_delete_inference_target', 'api_delete_inference_target_secret', 'api_delete_profile', 'api_get_inference_target', 'api_list_inference_targets', 'api_probe_target', 'api_update_profile')),
    'web/routes/primitives/recipes.py': frozenset(('api_cancel_recipe_invocation', 'api_delete_recipe', 'api_get_recipe', 'api_list_recipes')),
    'web/routes/primitives/thoughts.py': frozenset(('for_note', 'get', 'get_default_context', 'list_context', 'list_unfinished', 'original', 'review', 'workbench')),
    'web/routes/primitives/workbenches.py': frozenset(('api_cancel_workbench_run', 'api_clear_memory', 'api_delete_item', 'api_delete_skill', 'api_delete_workbench', 'api_forget_memory', 'api_get_workbench', 'api_list_memory', 'api_list_runs', 'api_list_skills', 'api_list_templates', 'api_list_workbenches', 'api_make_one_automation', 'api_new_results', 'api_open_result', 'api_prepared_for_today', 'api_promote_memory', 'api_restore_item', 'api_retry_mint')),
    'web/routes/primitives/workflows.py': frozenset(('cancel', 'delete', 'get_', 'list_')),
    'web/routes/projects.py': frozenset(('api_archive_project', 'api_associate_meeting', 'api_create_item', 'api_create_project', 'api_desk_needs_you_seen', 'api_disassociate_meeting', 'api_discard_ask_task', 'api_dismiss_suggested_source', 'api_get_project', 'api_list_ask_tasks', 'api_list_items', 'api_list_project_briefings', 'api_list_projects', 'api_mark_room_read', 'api_meeting_projects', 'api_project_action_items', 'api_project_artifacts', 'api_project_meetings', 'api_project_people', 'api_project_resources', 'api_project_since_last_meeting', 'api_project_summary', 'api_record_ask_stop', 'api_resource_relationships', 'api_restore_project', 'api_save_ask_task', 'api_suggested_sources', 'api_transition_item', 'api_update_item', 'api_update_project')),
    'web/routes/proposals.py': frozenset(('api_accept_reviewed', 'api_confirm_proposal', 'api_defer_proposal', 'api_dismiss_proposal', 'api_edit_proposal', 'api_meeting_outcome_review', 'api_meeting_proposals', 'api_project_proposals', 'api_restore_proposal')),
    'web/routes/providers.py': frozenset(('atlassian_remove_connection', 'confluence_connection_recheck', 'confluence_connections', 'confluence_discover', 'evaluate_watch', 'jira_connection_recheck', 'jira_connections', 'jira_discover', 'list_providers')),
    'web/routes/scheduled_recordings.py': frozenset(('cancel_armed', 'create_schedule', 'delete_schedule', 'get_schedule', 'list_schedules', 'update_schedule')),
    'web/routes/setup.py': frozenset(('api_first_value_event', 'api_first_value_finish', 'api_first_value_start', 'api_hub_default_summary', 'api_inference_acquisition', 'api_inference_capabilities', 'api_inference_capability', 'api_inference_setup', 'api_onboarding_disposition', 'api_setup_status')),
    'web/routes/steward.py': frozenset(('api_dismiss_nudge', 'api_get_steward_policy', 'api_get_steward_run', 'api_list_nudges', 'api_list_steward_runs')),
    'web/routes/sync.py': frozenset(('api_get_artifact', 'api_sync_pull')),
    'web/routes/system/agent_capabilities.py': frozenset(('api_agent_capabilities',)),
    'web/routes/system/coder_steering_routes.py': frozenset(('api_coder_disarm', 'api_coder_grants', 'api_coder_nodes')),
    'web/routes/system/coders.py': frozenset(('api_companion_clear_stale', 'api_companion_dismiss', 'api_companion_pin', 'api_companion_select', 'api_companion_status')),
    'web/routes/system/gate_routes.py': frozenset(('api_gate_audit', 'api_gate_full_call', 'api_gate_list', 'api_gate_read', 'api_revoke_agent_principal', 'api_revoke_self', 'api_session_receipt')),
    'web/routes/system/health.py': frozenset(('api_devices_health', 'api_runtime_status', 'api_system_identity')),
    'web/routes/system/kernel_routes.py': frozenset(('api_kernel_claim', 'api_kernel_events', 'api_kernel_read', 'api_kernel_reconcile')),
    'web/routes/system/settings.py': frozenset(('api_get_settings', 'api_heartbeat_put', 'api_heartbeat_run_now', 'api_update_settings')),
    'web/routes/system/settings_secrets.py': frozenset(('api_delete_secret', 'api_replace_secret', 'api_rotate_secret')),
    'web/routes/system/ui_feedback.py': frozenset(('api_ui_feedback_status',)),
    'web/routes/system/voice.py': frozenset(('api_mic_close', 'api_mic_open', 'api_preview_discard', 'api_preview_type', 'api_test_voice_command', 'api_wake_type')),
    'web/routes/threads.py': frozenset(('api_abort', 'api_delete_annotation', 'api_delete_thread', 'api_get_thread', 'api_interview_promotions', 'api_list_threads')),
    'web/routes/tts.py': frozenset(('tts_download', 'tts_status')),
    'web/routes/watches.py': frozenset(('get_watch', 'list_project_watches', 'list_watches')),
}


def _is_route_handler(node: ast.AST) -> bool:
    return (
        isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef))
        and any(
            isinstance(decorator, ast.Call)
            and isinstance(decorator.func, ast.Attribute)
            and decorator.func.attr in _ROUTE_DECORATORS
            for decorator in node.decorator_list
        )
    )


def _runs_on_loop(node: ast.AsyncFunctionDef) -> bool:
    """Return whether the route's own body has no async operation.

    Nested definitions, lambdas, and class bodies belong to their own call
    sites. They must not make their enclosing route appear loop-bound.
    """
    class BodyVisitor(ast.NodeVisitor):
        has_async_operation = False

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            return

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            return

        def visit_Lambda(self, node: ast.Lambda) -> None:
            return

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            return

        def visit_Await(self, node: ast.Await) -> None:
            self.has_async_operation = True

        def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
            self.has_async_operation = True

        def visit_AsyncWith(self, node: ast.AsyncWith) -> None:
            self.has_async_operation = True

    visitor = BodyVisitor()
    for statement in node.body:
        visitor.visit(statement)
    return not visitor.has_async_operation


def _route_handlers() -> list[tuple[str, int, str, bool, bool]]:
    handlers: list[tuple[str, int, str, bool, bool]] = []
    for path in sorted(_WEB.rglob("*.py")):
        relative = str(path.relative_to(_REPO / "holdspeak"))
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if not _is_route_handler(node):
                continue
            is_async = isinstance(node, ast.AsyncFunctionDef)
            handlers.append((
                relative, node.lineno, node.name, is_async,
                is_async and _runs_on_loop(node),
            ))
    return handlers


def test_route_handlers_are_off_loop_or_allowlisted() -> None:
    offenders = [
        f"{path}:{line} {name}: make it `def`, or await its sync work "
        "through `run_in_threadpool`"
        for path, line, name, is_async, on_loop in _route_handlers()
        if is_async and on_loop and name not in ALLOWLIST.get(path, frozenset())
    ]
    assert not offenders, "route handlers still run on the event loop:\n" + "\n".join(offenders)


def test_route_handler_walk_is_non_vacuous() -> None:
    handlers = _route_handlers()
    assert len(handlers) > 400
    assert any(
        path == "web/routes/people.py"
        and name == "readiness"
        and not is_async
        for path, _line, name, is_async, _on_loop in handlers
    )


# The test boots the real MeetingWebServer so startup runs on its event loop.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_desk_needs_you import _boot  # noqa: E402


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    from holdspeak.db import reset_database

    yield _boot(tmp_path, monkeypatch)
    reset_database()
    composition.install(composition.bare(label="pytest"))


def test_hub_raises_starlette_thread_limiter(hub: Any) -> None:
    with hub.client as client:
        tokens = client.portal.call(
            lambda: anyio.to_thread.current_default_thread_limiter().total_tokens
        )
    assert tokens == 64

