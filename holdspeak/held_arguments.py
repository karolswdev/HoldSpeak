"""Held-write schema vocabulary and the remaining disclosure work.

Declarations live beside the tool/operation. Projection belongs only to
services.held_tool_details. NOT_YET_DESCRIBED is an explicit shrinking debt
set; the census test rejects both new omissions and obsolete entries.

Tool-author contract: a description and execution MUST use the same target
resolver. Explicit ids are already resolved; selector/default tools declare
x-held-target with their owning operation and public resolver method. The
held handle keeps the canonical arguments, and approval freezes that payload.
Never resolve a name again at execution or let a service ignore a shown id.
Bodies use word_count, never text. A hidden parent suppresses every child.
Every shown scalar is bounded by HELD_FACT_VALUE_LIMIT in the one projector.
"""
from __future__ import annotations

from typing import Any


def held_arguments(title: str, *facts: dict[str, Any]) -> dict[str, Any]:
    return {"title": title, "x-held-arguments": list(facts)}


def text(key: str, label: str) -> dict[str, Any]:
    return {"key": key, "label": label, "kind": "text"}


def word_count(key: str, label: str) -> dict[str, Any]:
    return {**text(key, label), "format": "word_count"}


def target(operation: str, method: str) -> dict[str, Any]:
    return {"x-held-target": {"operation": operation, "method": method}}


def resolve_target(schema: dict[str, Any], args: dict[str, Any], principal: Any) -> dict[str, Any]:
    """Use the execution service's resolver, never a second selector."""
    from copy import deepcopy
    declaration = schema.get("x-held-target")
    if not declaration:
        return deepcopy(args)
    from holdspeak.mcp.tools import runtime_registry
    service = runtime_registry().target(declaration["operation"])
    return getattr(service, declaration["method"])(principal, deepcopy(args))


def strongest_effect(tool: dict[str, Any]) -> str:
    """Strongest declared effect, including argument-qualified MCP exposures.

    This classifies disclosure reads and the census. Admission continues to
    use the existing per-call truth table; classification grants no rights.
    """
    from holdspeak.operations import DESCRIPTORS
    from holdspeak.services.thread_tools import _ALL_TOOL_CLASSES
    name = tool["name"]
    if tool["inputSchema"].get("x-effect") == "write":
        return "write"
    if _ALL_TOOL_CLASSES.get(name, (None,))[0] in {"effect_proposal", "candidate_builder"}:
        return "write"
    if any(row.effect == "write" and any(exposure.startswith("mcp:") and
           exposure[4:].split("[", 1)[0] == name for exposure in row.exposure) for row in DESCRIPTORS):
        return "write"
    return "read"


def hidden(key: str, label: str, kind: str = "secret") -> dict[str, Any]:
    return {"key": key, "label": label, "kind": kind}


def named(key: str | list[str], label: str, tool: str, arguments: dict[str, str],
          value: str, *, rows: str | list[str] | None = None, match: dict[str, str] | None = None) -> dict[str, Any]:
    return {"key": key, "label": label, "kind": "text", "read": {
        "tool": tool, "arguments": arguments, "value": value,
        **({"rows": rows, "match": match} if rows else {}),
    }}


NOT_YET_DESCRIBED: frozenset[str] = frozenset({
    "action_item.review",
    "action_item.update",
    "activity.extension.ingest",
    "activity.meeting_candidate.start",
    "activity.nudge.dismiss",
    "activity.nudge.select",
    "activity.records.delete",
    "activity.refresh",
    "activity.rule.delete",
    "agent.answer",
    "agent.hand.cancel_queued",
    "agent.launch.seen",
    "agent.prompt",
    "agent.start_helper",
    "ask.resolve_grounding",
    "ask.run",
    "automation.cancel",
    "automation.create",
    "automation.delete",
    "automation.event_start.set_enabled",
    "automation.item.restore",
    "automation.lesson.forget",
    "automation.make_one",
    "automation.result.open",
    "automation.run",
    "automation.template.instantiate",
    "automation.update",
    "cadence.apply_closeout",
    "cadence.closeout",
    "cadence.run_now",
    "cadence.set_status",
    "cadence.snooze",
    "calls.hangup",
    "concierge.detect",
    "concierge.retry",
    "connection.recheck",
    "decision.accept",
    "decision.meeting_supersede",
    "decision.promote",
    "decision.promote_draft",
    "decision.supersede",
    "decision_record.carry",
    "decision_record.create_from_desk",
    "decision_record.create_from_meeting",
    "delivery.actuator.github.propose",
    "delivery.actuator.webhook.propose",
    "desk.mark",
    "desk.projection.present",
    "desk.request.replay",
    "desk.say",
    "desk.scroll",
    "desk.verb",
    "desk_window.arrange",
    "desk_window.close",
    "desk_window.move",
    "desk_window.open",
    "desk_window.raise",
    "desk_window.resize",
    "desk_window.seat",
    "desk_window.send_back",
    "desk_window.set_geometry",
    "desk_window.stage_shelf",
    "desk_window.zoom",
    "dictation.blocks.create",
    "dictation.blocks.delete",
    "dictation.blocks.update",
    "dictation.corrections.add",
    "dictation.corrections.remove",
    "dictation.journal.clear",
    "dictation.journal.correct",
    "dictation.journal.delete",
    "dictation.journal.update",
    "dictation.project_hs.put",
    "dictation.project_kb.put",
    "dictation.project_kb.start",
    "follow_through.commit_decision",
    "heartbeat.notify_test",
    "heartbeat.run_now",
    "interview.change_section",
    "interview.record_fact",
    "interview.suggest",
    "kb.add_member",
    "kb.remove_member",
    "meeting.accept_reviewed",
    "meeting.aftercare_decide",
    "meeting.bookmark",
    "meeting.intel_recovery_retry",
    "meeting.intel_recovery_skip",
    "meeting.intel_retry",
    "meeting.ready_read",
    "meeting.recover_capture",
    "meeting.rename",
    "meeting.resolve_sync_conflict",
    "meeting.restore",
    "meeting.update",
    "monday_brief.generate",
    "monday_brief.get",
    "monday_brief.shelf",
    "nudge.dismiss",
    "people.agenda.add",
    "people.agenda.transition",
    "people.calendar.link",
    "people.calendar.unlink",
    "people.commitment.satisfy",
    "people.commitment.send_to_workbench",
    "people.commitment.transition",
    "people.note.create",
    "people.one_on_one.create",
    "people.owed.create",
    "people.project.link",
    "people.project.unlink",
    "people.relationship.create",
    "people.request.accept",
    "people.request.create",
    "people.suggestion.add",
    "people.suggestion.hide",
    "phone.brief",
    "phone.later",
    "phone.send_message",
    "plugin_job.cancel",
    "plugin_job.retry",
    "program.add_to_night",
    "program.amend",
    "program.checkpoint",
    "program.create",
    "program.from_action",
    "program.park",
    "program.plan",
    "program.plan_draft",
    "program.plan_programs",
    "program.propose_fix",
    "program.race",
    "program.require",
    "program.resume",
    "program.round",
    "program.shape_held_drop",
    "program.start_from",
    "program.step_done",
    "program.step_remove",
    "program.step_update",
    "program.text_apply",
    "program.update",
    "project.accept_review",
    "project.ask.discard",
    "project.ask.save",
    "project.ask.stopped",
    "project.brief.discard",
    "project.brief.keep",
    "project.brief.prepare",
    "project.brief.stop",
    "project.create",
    "project.decide_proposal",
    "project.dismiss_suggested_source",
    "project.draft_update",
    "project.item.transition",
    "project.item.update",
    "project.link",
    "project.mark_room_read",
    "project.open_review",
    "project.publish_update",
    "project.resource.add",
    "project.resource.remove",
    "project.restore",
    "project.run_steward",
    "project.setup.answer",
    "project.setup.clarify_jira_scope",
    "project.setup.clarify_repo_scope",
    "project.setup.deselect_proposal",
    "project.setup.select_proposal",
    "project.setup.start",
    "project.setup.suggest",
    "project.setup.test_proposal",
    "project.steward.trigger",
    "project.stop_steward",
    "project.unlink",
    "project.update",
    "project.update.engine_pass",
    "project.update.job_apply",
    "project.update.job_stop",
    "project.update.regenerate",
    "project.update.review_claim",
    "project.update_draft",
    "project.watch.evaluate",
    "project.watch.test",
    "proposal.confirm",
    "proposal.defer",
    "proposal.dismiss",
    "proposal.edit",
    "proposal.restore",
    "recipe.create",
    "recipe.delete",
    "recipe.run",
    "recipe.update",
    "recordings.park",
    "recordings.retry",
    "recordings.unshare",
    "repository.checkout",
    "repository.commit",
    "repository.register",
    "repository.stage",
    "repository.write_file",
    "scheduled_recording.cancel_armed",
    "scheduled_recording.create",
    "scheduled_recording.delete",
    "scheduled_recording.update",
    "thought.accept_review",
    "thought.adopt_note",
    "thought.answer_and_continue",
    "thought.answer_review",
    "thought.attach_context",
    "thought.complete",
    "thought.create",
    "thought.detach_context",
    "thought.open_note",
    "thought.reconcile",
    "thought.refine",
    "thought.refresh_context",
    "thought.reject_review",
    "thought.resume",
    "thought.stop_refinement",
    "thought.update_working",
    "thread.abort",
    "thread.annotation.add",
    "thread.annotation.delete",
    "thread.branch",
    "thread.create",
    "thread.decide",
    "thread.delete",
    "thread.import",
    "thread.keep",
    "thread.regenerate",
    "thread.set_status",
    "thread.todo",
    "thread.turn",
    "thread.update",
    "walk.answer",
    "walk.create",
    "workbench.add_item",
    "workbench.delete_item",
    "workbench.update_item",
    "zone.file",
    "zone.unfile",
})
