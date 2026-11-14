"""Held-write schema vocabulary and the remaining disclosure work.

Declarations live beside the tool/operation. Projection belongs only to
services.held_tool_details. NOT_YET_DESCRIBED is an explicit shrinking debt
set; the census test rejects both new omissions and obsolete entries.

Tool-author contract: a description and execution MUST use the same target
resolver. Explicit ids are already resolved; selector/default tools declare
x-held-target with their owning operation and public resolver method. The
held handle keeps the canonical arguments, and approval freezes that payload.
Never resolve a name again at execution or let a service ignore a shown id.
A qualified ref that can select between stores needs the same resolver and
a frozen identity precondition too. Public name reads do not select write targets.
A fallback is part of the resolved operand too: description and dispatch
use the owning adapter/service's x-held-normalize function for scalar defaults
and normalization; x-held-target handles stateful derivation. Both functions
must be idempotent. Missing, blank and whitespace must have the same meaning
for facts and writes. Never stringify a structured value into a text fact.
The target may select the caller as actor when direction depends on who sent
it; reviewing as owner must not turn an agent's send into an owner's reply.
Derived private values use owner_only facts; the caller sees Hidden,
and both readers keep the revision over the owner's facts. A frozen derived
value is a checked precondition, never a client assertion to trust.
Existing allowlisted aliases can declare x-held-delegate: the owning handler
resolver selects the existing inner tool and argument root. Its declaration,
canonical preparation and the one projector are reused, never copied.
Bodies use word_count, never text. File contents use utf8_bytes, never text.
Read list paths may use $ for the root; a match can add a fixed id prefix. A hidden parent suppresses every child.
An authority change or a start/resume of autonomous work MUST declare
x-held-authority and a public owning resolver. It resolves the effective native
rights, Desk rights, principal, network, folder and lifetime, not just a Control
label. The held call keeps expected_authority; the writer recomputes it before
any grant, process or input and refuses answer_stale on a difference. A missing
host is an effective value too. Queues and later launches carry the commitment;
no fallback may widen it. The commitment is a precondition, never a mode request.
Authority snapshots are withheld at every depth by the observer. A public
resolve_*_authority method withholds its arguments and result, because its
read can contain an owner-only prompt or scope.
A screen answer uses the same prompt reader at description and input. Bind its
content, selected permission and duration, not the state word's timestamp.
Agent prompt words are the owner's question: format prompt keeps every word in
short redacted facts. Only the caller's own launch may read those prompt words;
private authority material remains hidden. Document bodies still use lengths.
Every shown scalar is bounded by HELD_FACT_VALUE_LIMIT in the one projector.
"""
from __future__ import annotations

from typing import Any


def held_arguments(title: str, *facts: dict[str, Any]) -> dict[str, Any]:
    return {"title": title, "x-held-arguments": list(facts)}


def text(key: str, label: str, *, owner_only: bool = False) -> dict[str, Any]:
    return {"key": key, "label": label, "kind": "text", **({"owner_only": True} if owner_only else {})}


def word_count(key: str, label: str, *, owner_only: bool = False) -> dict[str, Any]:
    return {**text(key, label, owner_only=owner_only), "format": "word_count"}




def authority_facts() -> list[dict[str, Any]]:
    return [text("expected_authority." + key, label, owner_only=True) | {"redact": True, **({"format": "prompt"} if key in ("folder", "agent") else {})}
            for key, label in (("control", "Control"), ("files", "Files"), ("commands", "Commands"),
                ("desk", "Desk"), ("network", "Network"), ("folder", "Folder"), ("agent", "For"), ("until", "Until"),
                ("calls", "Calls"), ("handoff", "Hand off"), ("spend", "Spend limit"))] + [
            hidden("expected_authority.material", "Authority binding", "token")]

def prompt_facts() -> list[dict[str, Any]]:
    """Agent words are the owner's question, never an arbitrary document body."""
    return [text("expected_authority.action", "Permission", owner_only=True) | {"caller_launch": "launch_id"},
            text("expected_authority.agent", "Agent", owner_only=True) | {"caller_launch": "launch_id"},
            text("expected_authority.until", "Until", owner_only=True) | {"caller_launch": "launch_id"},
            {**text("expected_authority.prompt", "Prompt", owner_only=True), "format": "prompt", "redact": True, "caller_launch": "launch_id"},
            {**text("expected_authority.choice", "Choice", owner_only=True), "format": "prompt", "redact": True, "caller_launch": "launch_id"},
            hidden("expected_authority.digest", "Prompt binding", "token"), hidden("expected_authority.pane", "Pane")]

def constant(label: str, value: str) -> dict[str, Any]:
    """A tool-declared fact for a fixed destination or a selector-free action."""
    return {"key": [], "label": label, "kind": "text", "value": value}


def normalizer(function: str, **arguments: Any) -> dict[str, Any]:
    """The owning adapter/service's pure effective-argument function."""
    return {"x-held-normalize": {"function": function, "arguments": arguments}}


def normalize_arguments(schema: dict[str, Any], args: dict[str, Any]) -> dict[str, Any]:
    from copy import deepcopy
    from importlib import import_module

    name = schema.get("x-held-normalize")
    if name is None:
        return deepcopy(args)
    module, path = name["function"].split(":")
    function = import_module(module)
    for part in path.split("."):
        function = getattr(function, part)
    return function(deepcopy(args), **name["arguments"])


def target(operation: str, method: str, *, factory: str | None = None, actor: str = "owner") -> dict[str, Any]:
    return {"x-held-target": {"operation": operation, "method": method,
            **({"factory": factory} if factory else {}), **({"actor": actor} if actor != "owner" else {})}}


def resolve_target(schema: dict[str, Any], args: dict[str, Any], principal: Any, *, caller: Any = None) -> dict[str, Any]:
    """Use the execution service's resolver, never a second selector."""
    from copy import deepcopy
    declaration = schema.get("x-held-target")
    args = normalize_arguments(schema, args)
    if schema.get("x-held-delegate"):
        from holdspeak.mcp.tools import _tool_schema
        module, function = schema["x-held-delegate"]["resolver"].split(":")
        from importlib import import_module
        name, payload = getattr(import_module(module), function)(args)
        if name is not None:
            inner = _tool_schema(name)
            args[schema["x-held-delegate"]["arguments"]] = resolve_target(inner, payload, principal, caller=caller)
    if not declaration:
        return deepcopy(args)
    if declaration.get("factory"):
        from importlib import import_module
        module, function = declaration["factory"].split(":")
        service = getattr(import_module(module), function)()
    else:
        from holdspeak.mcp.tools import runtime_registry
        service = runtime_registry().target(declaration["operation"])
    actor = caller if declaration.get("actor") == "caller" and caller is not None else principal
    return getattr(service, declaration["method"])(actor, deepcopy(args))


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


def named(key: str | list[str], label: str, tool: str, arguments: dict[str, Any],
          value: str, *, rows: str | list[str] | None = None, match: dict[str, Any] | None = None,
          through: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"key": key, "label": label, "kind": "text", "read": {
        "tool": tool, "arguments": arguments, "value": value,
        **({"rows": rows, "match": match} if rows else {}),
        **({"through": through} if through else {}),
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
    "automation.template.instantiate",
    "automation.update",
    "cadence.apply_closeout",
    "cadence.closeout",
    "cadence.run_now",
    "cadence.set_status",
    "cadence.snooze",
    "concierge.detect",
    "concierge.retry",
    "connection.recheck",
    "decision_record.carry",
    "decision_record.create_from_desk",
    "decision_record.create_from_meeting",
    "delivery.actuator.github.propose",
    "delivery.actuator.webhook.propose",
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
    "monday_brief.shelf",
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
    "program.round",
    "program.shape_held_drop",
    "program.start_from",
    "program.step_done",
    "program.step_remove",
    "program.step_update",
    "program.text_apply",
    "program.update",
    "proposal.confirm",
    "proposal.defer",
    "proposal.dismiss",
    "proposal.edit",
    "proposal.restore",
    "recipe.create",
    "recipe.delete",
    "recipe.run",
    "recipe.update",
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
    "zone.unfile",
})
