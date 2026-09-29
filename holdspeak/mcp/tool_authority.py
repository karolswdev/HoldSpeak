"""Every MCP tool's authority class: what a thread acting as the owner may do.

The owner's ruling (2026-09-29, #694, his pick "Egress + authority + config"):
a thread acting as him may do normal WORK (notes, People notes, drafting,
filing, preparing a send); it may NEVER, without his press:

* ``egress``    -- anything that leaves the machine (a send, a nudge, any
  external post), and the ledger of what he sent;
* ``authority`` -- anything that changes who or what may act (archive, the
  steward policy, the egress allow-list, who he is, file custody);
* ``config``    -- anything that changes the system itself (models, endpoints,
  assignments, setup, the default context, connections, watches, settings).

A setup follows Send's prepare-then-press (Muad'Dib's ruling on #694): the
steps that draft it (start, answer, suggest, select, test, clarify) write only
the setup session and are work; ``project.setup.finalize`` commits it into the
system and is config.

Everything else is ``work`` and stays with the thread's posture (yolo too).
Reads of his connected providers and model calls on his assigned routes are
work: nothing of his is posted. A steward run is work: it acts inside the
policy he pressed.

ONE table over the whole dispatch set (``holdspeak.mcp.tools.TOOLS`` and every
family): ``services/thread_tools`` offers a thread only the ``work`` rows, and
``tests/unit/test_thread_tool_gate.py`` fails on any tool without a row.
"""
from __future__ import annotations

from typing import Any, Callable, Mapping

WORK = "work"
EGRESS = "egress"
AUTHORITY = "authority"
CONFIG = "config"

#: Each non-work row carries its reason.
TOOL_AUTHORITY: dict[str, str] = {
    "desk.list": WORK,
    "desk.get": WORK,
    "desk.create": WORK,
    "desk.update": WORK,
    "desk.delete": WORK,
    "desk.verb": WORK,
    "workbench.run": WORK,
    "workbench.add_item": WORK,
    "meeting.list": WORK,
    "meeting.get": WORK,
    "workbench.list": WORK,
    "workbench.get": WORK,
    "workbench.create": WORK,  # argument-aware: ARGUMENT_AUTHORITY below
    "workbench.update": WORK,  # argument-aware: ARGUMENT_AUTHORITY below
    "workbench.delete": WORK,
    "workbench.update_item": WORK,
    "workbench.delete_item": WORK,
    "workbench.list_runs": WORK,
    "recipe.list": WORK,
    "recipe.get": WORK,
    "recipe.run": WORK,
    "recipe.chat": WORK,
    "zone.file": WORK,
    "zone.unfile": WORK,
    "zone.list_members": WORK,
    "kb.add_member": WORK,
    "kb.remove_member": WORK,
    "kb.list_members": WORK,
    "meeting.start_capture": WORK,
    "meeting.stop_capture": WORK,
    "meeting.delete": WORK,
    "meeting.export": WORK,
    "meeting.import": AUTHORITY,  # custody: the hub reads a file path on the owner's disk (owner_only)
    "meeting.run_intelligence": WORK,
    "meeting.proposals": WORK,
    "proposal.confirm": WORK,
    "proposal.dismiss": WORK,
    "steward.nudges": WORK,
    "nudge.send": EGRESS,  # posts a GitHub comment as the owner
    "nudge.dismiss": WORK,
    "dictation.list": WORK,
    "dictation.get": WORK,
    "desk.snapshot": WORK,
    "desk.needs_you": WORK,
    "settings.hub": WORK,
    "decision_record.list": WORK,
    "decision_record.get": WORK,
    "decision_record.create_from_meeting": WORK,
    "decision_record.create_from_desk": WORK,
    "decision_record.search": WORK,
    "decision.supersede": WORK,
    "kernel.receipt": WORK,
    "pipeline.events": WORK,
    "follow_through.board": WORK,
    "follow_through.complete": WORK,
    "follow_through.commit_decision": WORK,
    "monday_brief.get": WORK,
    "monday_brief.generate": WORK,
    "monday_brief.shelf": WORK,
    "monday_brief.shelf_read": WORK,
    "scheduled_recording.list": WORK,
    "scheduled_recording.create": WORK,  # argument-aware: ARGUMENT_AUTHORITY below
    "scheduled_recording.update": WORK,  # argument-aware: ARGUMENT_AUTHORITY below
    "scheduled_recording.delete": WORK,
    "scheduled_recording.cancel_armed": WORK,
    "ask.resolve_grounding": WORK,
    "ask.run": WORK,
    "ask.cancel": WORK,
    "ask.keep": WORK,
    "settings.get": WORK,
    "settings.update": CONFIG,  # the system settings (incl. calendar sources)
    "coder.list": WORK,
    "coder.get": WORK,
    "coder.audit": WORK,
    "cadence.status": WORK,
    "cadence.loops": WORK,
    "cadence.get_loop": WORK,
    "cadence.brief": WORK,
    "cadence.closeout": WORK,
    "cadence.history": WORK,
    "cadence.audit": WORK,
    "cadence.snooze": WORK,
    "cadence.set_status": WORK,
    "cadence.run_now": WORK,
    "cadence.apply_closeout": WORK,
    "sequence.run": WORK,
    "sequence.cancel": WORK,
    "workflow.run": WORK,
    "workflow.cancel": WORK,
    "memory.search": WORK,
    "people.readiness": WORK,
    "people.relationship.list": WORK,
    "people.relationship.get": WORK,
    "people.grounding.get": WORK,
    "people.relationship.create": WORK,
    "people.one_on_one.create": WORK,
    "people.agenda.add": WORK,
    "people.note.create": WORK,
    "people.request.create": WORK,
    "people.request.accept": WORK,
    "people.commitment.transition": WORK,
    "people.one_on_one.brief": WORK,
    "people.calendar.link": WORK,
    "people.calendar.unlink": WORK,
    "people.owner_alias.link": AUTHORITY,  # who the owner is in the People store
    "people.owner_alias.unlink": AUTHORITY,  # who the owner is in the People store
    "people.resolve": WORK,
    "plugin_job.list": WORK,
    "plugin_job.summary": WORK,
    "plugin_job.retry": WORK,
    "plugin_job.cancel": WORK,
    "reaction.presets": WORK,
    "watch.list": WORK,
    "watch.create": CONFIG,  # a connector watch
    "watch.set_enabled": CONFIG,  # a connector watch
    "watch.refresh": WORK,
    "watch.preview": WORK,
    "event.list": WORK,
    "reaction.list": WORK,
    "reaction.create": CONFIG,  # an automatic reaction
    "reaction.set_enabled": CONFIG,  # an automatic reaction
    "reaction.process": WORK,
    "thought.create": WORK,
    "thought.adopt_note": WORK,
    "thought.get_default_context": WORK,
    "thought.replace_default_context": CONFIG,  # the hub's default AI context
    "thought.list_context": WORK,
    "thought.refine": WORK,
    "thought.reconcile": WORK,
    "thought.stop_refinement": WORK,
    "thought.attach_context": WORK,
    "thought.detach_context": WORK,
    "thought.refresh_context": WORK,
    "thought.answer_review": WORK,
    "thought.accept_review": WORK,
    "thought.reject_review": WORK,
    "thought.answer_and_continue": WORK,
    "thought.update_working": WORK,
    "thought.complete": WORK,
    "thought.resume": WORK,
    "inference.cancel_model_acquisition": CONFIG,  # a model download
    "model_library.get": WORK,
    "model_library.download": CONFIG,  # the model library
    "model_library.add_to_library": CONFIG,  # the model library
    "model_library.connect_hosted_model": CONFIG,  # a hosted model provider and its secret
    "model_library.define_endpoint": CONFIG,  # a model endpoint and its secret
    "model_library.connect_paired_device": CONFIG,  # the model library
    "model_library.use_model_file": CONFIG,  # the model library
    "inference_assignment.summary": WORK,
    "inference_assignment.editor": WORK,
    "inference_assignment.set": CONFIG,  # which model serves a capability
    "inference_assignment.preview_use_default": WORK,
    "inference_assignment.clear": CONFIG,  # which model serves a capability
    "concierge.detect": WORK,
    "concierge.propose": WORK,
    "concierge.probe": WORK,
    "concierge.apply": CONFIG,  # the engine set for every capability group
    "concierge.download": CONFIG,  # a model download
    "door.get": WORK,
    "door.add_item": WORK,
    "thread.set_status": WORK,
    "project.list": WORK,
    "project.get": WORK,
    "project.get_room": WORK,
    "project.create": WORK,
    "project.update": WORK,
    "project.archive": AUTHORITY,  # archives a project: pauses its watches and turns unattended runs off
    "project.restore": WORK,
    "project.link": WORK,
    "project.unlink": WORK,
    "project.open_review": WORK,
    "project.get_delta": WORK,
    "project.decide_proposal": WORK,
    "project.accept_review": WORK,
    "project.list_updates": WORK,
    "project.draft_update": WORK,
    "project.update_draft": WORK,
    "project.publish_update": WORK,
    "project.item.list": WORK,
    "project.item.create": WORK,
    "project.item.update": WORK,
    "project.item.transition": WORK,
    "project.resource.list": WORK,
    "project.resource.add": WORK,
    "project.resource.remove": WORK,
    "project.mark_update_delivered": EGRESS,  # records that the owner delivered an update (the delivery ledger)
    "project.configure_steward": AUTHORITY,  # the steward policy: what may act unattended, and its bounds
    "project.run_steward": WORK,
    "project.stop_steward": WORK,
    "project.get_steward_run": WORK,
    "project.steward.trigger": WORK,
    "project.setup.start": WORK,  # drafts the setup: writes only its own session (the prepare)
    "project.setup.resume": WORK,
    "project.setup.answer": WORK,  # drafts the setup: writes only its own session (the prepare)
    "project.setup.suggest": WORK,  # drafts the setup: writes only its own session (the prepare)
    "project.setup.finalize": CONFIG,  # commits the setup: creates the project, arms its watches (the press)
    "provider.list": WORK,
    "provider.github_connection": WORK,
    "provider.github_discover": WORK,
    "provider.github_validate_repo": WORK,
    "provider.jira_connections": WORK,
    "provider.jira_add_connection": CONFIG,  # a provider connection
    "provider.jira_connection": WORK,
    "provider.jira_discover": WORK,
    "provider.jira_search": WORK,
    "provider.jira_validate_scope": WORK,
    "provider.confluence_connections": WORK,
    "provider.confluence_discover": WORK,
    "provider.confluence_validate_space": WORK,
    "project.setup.clarify_jira_scope": WORK,  # drafts the setup: writes only its own session (the prepare)
    "project.watch.inspect": WORK,
    "project.watch.test": WORK,
    "project.watch.evaluate": WORK,
    "project.watch.set_rules": CONFIG,  # what a Room watch does and how often it reads
    "project.watch.pause": CONFIG,  # a Room watch
    "project.watch.resume": CONFIG,  # a Room watch
    "project.watch.retire": CONFIG,  # a Room watch
    "project.suggested_sources": WORK,
    "project.add_suggested_source": CONFIG,  # arms a new Room watch on a source
    "project.dismiss_suggested_source": WORK,
    "connection.list": WORK,
    "connection.recheck": WORK,
    "project.setup.select_proposal": WORK,  # drafts the setup: writes only its own session (the prepare)
    "project.setup.deselect_proposal": WORK,  # drafts the setup: writes only its own session (the prepare)
    "project.setup.test_proposal": WORK,  # drafts the setup: writes only its own session (the prepare)
    "project.setup.clarify_repo_scope": WORK,  # drafts the setup: writes only its own session (the prepare)
    "channel.destinations": WORK,
    "channel.save_destination": AUTHORITY,  # the egress allow-list: where documents may go
    "channel.remove_destination": AUTHORITY,  # the egress allow-list: where documents may go
    "channel.check_destination": WORK,
    "channel.preview": WORK,
    "channel.prepare": WORK,
    "channel.discard": EGRESS,  # decides a prepared send (the Send's other answer)
    "channel.send": EGRESS,  # sends a prepared document out (the owner's Send)
    "channel.sends": WORK,
    "heartbeat.status": WORK,
    "heartbeat.run_now": WORK,
    "heartbeat.set": CONFIG,  # the heartbeat sweep settings
    "heartbeat.notify_test": WORK,
    "interview.get": WORK,
    "interview.change_section": WORK,
    "interview.record_fact": WORK,
    "interview.suggest": WORK,
    "practice_recipe.list": WORK,
    "practice_recipe.get": WORK,
    "practice_recipe.compile": WORK,
}

#: What a thread never offers or admits, in any mode.
THREAD_EXCLUDED: frozenset[str] = frozenset(name for name, cls in TOOL_AUTHORITY.items() if cls != WORK)


# ── Mixed-purpose tools: the class depends on the call's arguments ─────────
#
# Codex Astra counsel r4 on #694 (P1) and Muad'Dib's ruling: a WORK tool can
# carry authority in its payload. Each predicate names exactly the arguments
# that create or change a delegation or a schedule (read from the writer that
# mints it); anything else is ordinary content work.

_SCHEDULE_FIELDS = frozenset({"schedule", "schedule_enabled", "schedule_revision"})


def _workbench_create(args: Mapping[str, Any]) -> str:
    # WorkbenchService.create_workbench mints a LIVE schedule delegation when
    # schedule_enabled is true (ScheduleDelegationService.enable_from_owner_in_transaction).
    fields = args.get("fields") or {}
    return AUTHORITY if any(fields.get(key) not in (None, False, "") for key in _SCHEDULE_FIELDS) else WORK


def _workbench_update(args: Mapping[str, Any]) -> str:
    # update_workbench re-fences or re-mints the delegation when a schedule
    # field changes; name, recipe and item order are content.
    fields = args.get("fields") or {}
    return AUTHORITY if _SCHEDULE_FIELDS & set(fields) else WORK


def _recording_create(args: Mapping[str, Any]) -> str:
    # create_schedule writes a delegation receipt for an event-linked arm or
    # an enabled schedule; a disabled draft (the default) mints nothing.
    return AUTHORITY if args.get("calendar_event_id") or args.get("enabled") is True else WORK


def _recording_update(args: Mapping[str, Any]) -> str:
    # update_schedule writes a delegation receipt when it enables or changes
    # the terms of an enabled schedule; a title is content.
    return AUTHORITY if {"enabled", "cron_expr", "tz", "one_shot", "duration_minutes"} & set(args) else WORK


#: The tools whose class is decided per call. Their TOOL_AUTHORITY row is
#: WORK (they are offered); the gate evaluates the predicate on the actual
#: arguments and refuses a non-work call by name.
ARGUMENT_AUTHORITY: dict[str, Callable[[Mapping[str, Any]], str]] = {
    "workbench.create": _workbench_create,
    "workbench.update": _workbench_update,
    "scheduled_recording.create": _recording_create,
    "scheduled_recording.update": _recording_update,
}


def call_class(name: str, args: Mapping[str, Any] | None) -> str:
    """The class of one call: its predicate when the tool is mixed, else its row."""
    predicate = ARGUMENT_AUTHORITY.get(name)
    if predicate is not None:
        return predicate(args or {})
    return TOOL_AUTHORITY[name]

