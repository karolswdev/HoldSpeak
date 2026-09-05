"""MCP tool schemas and transport-neutral HoldSpeak service dispatch."""
from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import asdict
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError as JsonSchemaValidationError

from holdspeak.db import get_database, get_observer
from holdspeak.mcp.families import FAMILIES
from holdspeak.principals import Principal
from holdspeak.services.decision_record_service import DecisionRecordService
from holdspeak.services.desk_service import DeskService
from holdspeak.services.dictation_service import DictationService
from holdspeak.services.event_query_service import EventQueryService
from holdspeak.services.follow_through_service import FollowThroughService
from holdspeak.services.meeting_service import MeetingService
from holdspeak.services.monday_brief_service import MondayBriefService
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from holdspeak.services.model_library_service import ModelLibraryApplicationService
from holdspeak.services.primitive_service import PrimitiveService
from holdspeak.services.recipe_service import RecipeService
from holdspeak.services.scheduled_recording_service import ScheduledRecordingService
from holdspeak.services.workbench_service import WorkbenchService

PRIMITIVE_KINDS = ("notes", "decisions", "kbs", "directories", "workflows", "chains")
_KIND_ALIASES = {kind: kind[:-1] if kind.endswith("s") else kind for kind in PRIMITIVE_KINDS}
_KIND_ALIASES["kbs"] = "kb"


class ToolError(ValueError):
    """An expected tool failure which maps to an MCP ``isError`` result."""


TOOLS: list[dict[str, Any]] = [
    {
        "name": "desk.list",
        "description": "List HoldSpeak desk primitives of one kind. The desk schema advertises 18 primitive kinds; this tool operates on the 6 authorable kinds: notes, decisions, kbs, directories, workflows, and chains. The remaining 12 kinds (meeting, artifact, project, repository, recipe, coder, game, roadmap, story, workbench, layout, people) are managed through dedicated tools or are read-only.",
        "inputSchema": {
            "type": "object",
            "properties": {"kind": {"type": "string", "enum": list(PRIMITIVE_KINDS)}},
            "required": ["kind"],
            "additionalProperties": False,
        },
    },
    {
        "name": "desk.get",
        "description": "Get one HoldSpeak desk primitive by kind and id. The desk schema advertises 18 primitive kinds; this tool operates on the 6 authorable kinds: notes, decisions, kbs, directories, workflows, and chains. The remaining 12 kinds (meeting, artifact, project, repository, recipe, coder, game, roadmap, story, workbench, layout, people) are managed through dedicated tools or are read-only.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "kind": {"type": "string", "enum": list(PRIMITIVE_KINDS)},
                "id": {"type": "string", "description": "Primitive identifier."},
            },
            "required": ["kind", "id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "desk.create",
        "description": "Create a desk primitive. Pass fields appropriate to its kind in data. Authorable kinds: notes, decisions, kbs, directories, workflows, chains.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "kind": {"type": "string", "enum": list(PRIMITIVE_KINDS)},
                "data": {"type": "object", "description": "Primitive fields, including optional id."},
            },
            "required": ["kind"],
            "additionalProperties": False,
        },
    },
    {
        "name": "desk.update",
        "description": "Update a desk primitive. Only supplied fields in data change. Authorable kinds: notes, decisions, kbs, directories, workflows, chains.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "kind": {"type": "string", "enum": list(PRIMITIVE_KINDS)},
                "id": {"type": "string"},
                "data": {"type": "object"},
            },
            "required": ["kind", "id", "data"],
            "additionalProperties": False,
        },
    },
    {
        "name": "desk.delete",
        "description": "Delete one desk primitive by kind and id. Authorable kinds: notes, decisions, kbs, directories, workflows, chains.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "kind": {"type": "string", "enum": list(PRIMITIVE_KINDS)},
                "id": {"type": "string"},
            },
            "required": ["kind", "id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "desk.verb",
        "description": "Dispatch an allowlisted server-side desk verb. Local presentation verbs return ui_only.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "verb_id": {"type": "string", "description": "The desk verb identifier."},
                "arguments": {"type": "object", "description": "Arguments for the server-side verb."},
            },
            "required": ["verb_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "workbench.run",
        "description": "Trigger a HoldSpeak Workbench run.",
        "inputSchema": {
            "type": "object",
            "properties": {"workbench_id": {"type": "string"}},
            "required": ["workbench_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "workbench.add_item",
        "description": "Add a work item to a HoldSpeak Workbench.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workbench_id": {"type": "string"},
                "title": {"type": "string"},
                "data": {"type": "object", "description": "Optional item fields."},
            },
            "required": ["workbench_id", "title"],
            "additionalProperties": False,
        },
    },
    {
        "name": "meeting.list",
        "description": "List or search archived meetings with optional archive filters.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"}, "from_date": {"type": "string"},
                "to_date": {"type": "string"}, "speaker": {"type": "string"},
                "tag": {"type": "string"}, "has_open_actions": {"type": "boolean"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 500},
                "cursor": {"type": ["string", "integer"]},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "meeting.get",
        "description": "Get the complete stored detail for one meeting.",
        "inputSchema": {
            "type": "object",
            "properties": {"meeting_id": {"type": "string"}, "include": {"type": "string"}},
            "required": ["meeting_id"],
            "additionalProperties": False,
        },
    },
 ]


def _workbench_tool(name: str, description: str, properties: dict[str, Any], required: list[str] | None = None) -> dict[str, Any]:
    return {"name": name, "description": description, "inputSchema": {
        "type": "object", "properties": properties, "required": required or [], "additionalProperties": False,
    }}


_RECIPE_RUN_OPTIONS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "variables": {"type": "object"},
        "max_tokens": {"type": "integer", "minimum": 1},
        "temperature": {"type": "number", "minimum": 0, "maximum": 2},
        "source_ref": {"type": "string"},
        "source_type": {}, "grounding_refs": {}, "grounding_revisions": {},
        "source_revision": {}, "deadline_at": {}, "initiator": {},
    },
    "additionalProperties": False,
}
_RECIPE_CHAT_OPTIONS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "history": {"type": "array"}, "grounding": {"type": "object"},
        "egress_context": {},
    },
    "additionalProperties": False,
}
_WORKBENCH_FIELDS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "name": {"type": "string"},
        "recipe_id": {"type": ["string", "null"]},
        "schedule": {"type": ["string", "null"]},
        "schedule_enabled": {"type": "boolean"},
        "schedule_revision": {"type": "integer", "minimum": 1},
        "item_order": {"type": "array", "items": {"type": "string"}},
    },
    "additionalProperties": False,
}


def _workbench_fields(value: Any) -> dict[str, Any]:
    fields = _data(value)
    unknown = set(fields) - set(_WORKBENCH_FIELDS_SCHEMA["properties"])
    if unknown:
        raise ToolError(f"Unsupported Workbench fields: {', '.join(sorted(unknown))}")
    return fields


TOOLS.extend([
    _workbench_tool("workbench.list", "List Workbenches.", {}),
    _workbench_tool("workbench.get", "Get a Workbench.", {"workbench_id": {"type": "string"}}, ["workbench_id"]),
    _workbench_tool("workbench.create", "Create a Workbench with closed optional configuration fields.", {"name": {"type": "string", "description": "Non-empty Workbench name."}, "fields": _WORKBENCH_FIELDS_SCHEMA}, ["name"]),
    _workbench_tool("workbench.update", "Update supplied closed Workbench configuration fields.", {"workbench_id": {"type": "string"}, "fields": _WORKBENCH_FIELDS_SCHEMA}, ["workbench_id", "fields"]),
    _workbench_tool("workbench.delete", "Delete a Workbench.", {"workbench_id": {"type": "string"}}, ["workbench_id"]),
    _workbench_tool("workbench.update_item", "Update supplied fields of a Workbench item.", {"workbench_id": {"type": "string"}, "item_id": {"type": "string"}, "fields": {"type": "object", "description": "Item patch fields."}}, ["workbench_id", "item_id", "fields"]),
    _workbench_tool("workbench.delete_item", "Delete a Workbench item.", {"workbench_id": {"type": "string"}, "item_id": {"type": "string"}}, ["workbench_id", "item_id"]),
    _workbench_tool("workbench.list_runs", "List Workbench runs.", {"workbench_id": {"type": "string"}}, ["workbench_id"]),
    _workbench_tool("recipe.list", "List Agent recipes.", {}),
    _workbench_tool("recipe.get", "Get an Agent recipe.", {"recipe_id": {"type": "string"}}, ["recipe_id"]),
    _workbench_tool("recipe.run", "Run an Agent recipe and return its lifecycle-backed result and minted artifact reference.", {"recipe_id": {"type": "string"}, "input": {"type": "string"}, "options": _RECIPE_RUN_OPTIONS_SCHEMA}, ["recipe_id"]),
    _workbench_tool("recipe.chat", "Ask an Agent recipe a question.", {"recipe_id": {"type": "string"}, "question": {"type": "string"}, "options": _RECIPE_CHAT_OPTIONS_SCHEMA}, ["recipe_id", "question"]),
    _workbench_tool("zone.file", "File a primitive in a Zone.", {"directory_id": {"type": "string"}, "primitive_id": {"type": "string"}}, ["directory_id", "primitive_id"]),
    _workbench_tool("zone.unfile", "Remove a primitive from a Zone.", {"directory_id": {"type": "string"}, "primitive_id": {"type": "string"}}, ["directory_id", "primitive_id"]),
    _workbench_tool("zone.list_members", "List Zone members.", {"directory_id": {"type": "string"}}, ["directory_id"]),
    _workbench_tool("kb.add_member", "Add a resource reference to a knowledge base.", {"kb_id": {"type": "string"}, "ref": {"type": "string"}}, ["kb_id", "ref"]),
    _workbench_tool("kb.remove_member", "Remove a resource reference from a knowledge base.", {"kb_id": {"type": "string"}, "ref": {"type": "string"}}, ["kb_id", "ref"]),
    _workbench_tool("kb.list_members", "List knowledge-base members.", {"kb_id": {"type": "string"}}, ["kb_id"]),
])


def _mcp_tool(name: str, description: str, properties: dict[str, Any], required: list[str] | None = None) -> dict[str, Any]:
    return {
        "name": name,
        "description": description,
        "inputSchema": {
            "type": "object",
            "properties": properties,
            "required": required or [],
            "additionalProperties": False,
        },
    }


# Kept as a distinct extension block: the workbench/recipe family above is
# owned by HS-123-09, while this is the operational meeting and desk family.
TOOLS.extend([
    _mcp_tool(
        "meeting.start_capture",
        "Start a meeting capture through the configured HoldSpeak capture controller.",
        {"config": {"type": "object", "description": "Optional capture configuration, including devices."}},
    ),
    _mcp_tool(
        "meeting.stop_capture",
        "Stop the active meeting capture, optionally identifying the meeting to stop.",
        {"meeting_id": {"type": "string", "description": "Optional meeting identifier."}},
    ),
    _mcp_tool(
        "meeting.delete",
        "Delete a stored meeting when it should no longer be retained.",
        {"meeting_id": {"type": "string", "description": "Meeting identifier to delete."}},
        ["meeting_id"],
    ),
    _mcp_tool(
        "meeting.export",
        "Export a stored meeting as Markdown or JSON for sharing or archival.",
        {
            "meeting_id": {"type": "string", "description": "Meeting identifier to export."},
            "format": {"type": "string", "enum": ["markdown", "json"], "description": "Export format."},
        },
        ["meeting_id", "format"],
    ),
    _mcp_tool(
        "meeting.run_intelligence",
        "Enqueue a fresh intelligence job for a meeting that has a transcript but never ran intelligence. Returns {jobId, state, host}. Refuses 409 when the meeting has no transcript.",
        {"meeting_id": {"type": "string", "description": "Meeting identifier."}},
        ["meeting_id"],
    ),
    _mcp_tool(
        "meeting.proposals",
        "List follow-through proposals extracted from a meeting's intelligence run. Each proposal is a decision or action item waiting for Confirm or Drop.",
        {
            "meeting_id": {"type": "string", "description": "Meeting identifier."},
            "state": {"type": "string", "enum": ["proposed", "confirmed", "dismissed"], "description": "Optional state filter."},
        },
        ["meeting_id"],
    ),
    _mcp_tool(
        "proposal.confirm",
        "Confirm a follow-through proposal, writing the decision record or action item through the kernel. Optionally amend text, owner, or due before confirming.",
        {
            "proposal_id": {"type": "string", "description": "Proposal identifier."},
            "text": {"type": "string", "description": "Amended text (optional; original kept when omitted)."},
            "owner": {"type": "string", "description": "Accountable owner (optional)."},
            "due": {"type": "string", "description": "ISO-8601 due date (optional)."},
        },
        ["proposal_id"],
    ),
    _mcp_tool(
        "proposal.dismiss",
        "Dismiss a follow-through proposal without creating any record.",
        {"proposal_id": {"type": "string", "description": "Proposal identifier."}},
        ["proposal_id"],
    ),
    _mcp_tool(
        "dictation.list",
        "Read the retained dictation journal, optionally paged and filtered by source.",
        {
            "limit": {"type": "integer", "minimum": 1, "maximum": 500, "description": "Maximum entries to return."},
            "cursor": {"type": "integer", "description": "Return entries older than this journal entry id."},
            "source": {"type": "string", "enum": ["dictation", "dry_run", "browser", "hotkey"], "description": "Optional dictation source filter."},
        },
    ),
    _mcp_tool(
        "dictation.get",
        "Get one retained dictation journal entry by its numeric id.",
        {"entry_id": {"type": "integer", "description": "Numeric dictation journal entry id."}},
        ["entry_id"],
    ),
    _mcp_tool("desk.snapshot", "Read one coherent snapshot of the durable HoldSpeak desk.", {}),
    _mcp_tool("desk.needs_you", "Aggregate needs-you items across all active project rooms. Returns {count, projects, items, next}.", {}),
    _mcp_tool("settings.hub", "Read the settings hub row facts: module state tokens for the settings truth table.", {}),
    _mcp_tool(
        "decision_record.list", "List durable decision records, newest first.",
        {"limit": {"type": "integer", "minimum": 1, "maximum": 500}, "offset": {"type": "integer", "minimum": 0}},
    ),
    _mcp_tool(
        "decision_record.get", "Get one decision record with sources, work, and revisions.",
        {"record_id": {"type": "string"}}, ["record_id"],
    ),
    _mcp_tool(
        "decision_record.create_from_meeting", "Mint a durable record from a meeting decision.",
        {"decision_id": {"type": "string"}}, ["decision_id"],
    ),
    _mcp_tool(
        "decision_record.create_from_desk", "Mint a durable record from an authored desk decision.",
        {"decision_id": {"type": "string"}}, ["decision_id"],
    ),
    _mcp_tool(
        "decision_record.search", "Search decision records and their affected-work labels.",
        {"query": {"type": "string"}, "limit": {"type": "integer", "minimum": 1, "maximum": 500}}, ["query"],
    ),
    _mcp_tool(
        "decision.supersede",
        "Supersede a decision when a successor decision replaces it.",
        {"decision_id": {"type": "string", "description": "Decision to supersede."}},
        ["decision_id"],
    ),
    _mcp_tool(
        "pipeline.events",
        "Query observed pipeline events with optional filters.",
        {
            "service": {"type": "string"},
            "method": {"type": "string"},
            "principal_kind": {"type": "string"},
            "since": {"type": "number", "description": "Inclusive epoch timestamp."},
            "until": {"type": "number", "description": "Inclusive epoch timestamp."},
            "correlation_id": {"type": "string"},
            "errors_only": {"type": "boolean", "default": False},
            "limit": {"type": "integer", "default": 50},
        },
    ),
    _mcp_tool(
        "follow_through.board",
        "Read the Follow-Through board, optionally filtered by project, owner, or lane.",
        {
            "project_id": {"type": "string", "description": "Optional project identifier."},
            "owner": {"type": "string", "description": "Optional accountable owner."},
            "state": {"type": "string", "enum": ["now", "waiting", "unassigned", "overdue"], "description": "Optional board lane."},
        },
    ),
    _mcp_tool(
        "follow_through.complete",
        "Apply a completion verb to a Follow-Through action card.",
        {
            "card_id": {"type": "string", "description": "Action card identifier."},
            "verb": {"type": "string", "enum": ["done", "dismiss", "snooze", "delegate", "reopen"], "description": "Write-through board verb."},
            "payload": {"type": "object", "description": "Verb data: until for snooze, to for delegate."},
        },
        ["card_id", "verb"],
    ),
    _mcp_tool(
        "follow_through.commit_decision",
        "Create an accountable commitment from an accepted decision.",
        {
            "decision_id": {"type": "string", "description": "Accepted decision identifier."},
            "owner": {"type": "string", "description": "Optional accountable owner."},
            "due_at": {"type": "string", "description": "Optional ISO-8601 due date."},
        },
        ["decision_id"],
    ),
    _mcp_tool(
        "monday_brief.get",
        "Read the latest persisted Monday Brief; set generate to true when no brief exists and one should be composed.",
        {"generate": {"type": "boolean", "default": False, "description": "Generate the current brief when no persisted brief exists."}},
    ),
    _mcp_tool(
        "monday_brief.generate",
        "Generate the current Monday Brief from durable sources. Repeated calls return the day's existing brief.",
        {},
    ),
    _mcp_tool(
        "scheduled_recording.list",
        "List all scheduled recordings with their current state, cron, and next-fire time.",
        {},
    ),
    _mcp_tool(
        "scheduled_recording.create",
        "Create a scheduled recording. Pass calendar_event_id to arm a calendar event (title/times/duration computed server-side, one-shot, enabled, fires 60 s before start). Without it, pass cron_expr + fields for a manual schedule.",
        {
            "title": {"type": "string", "description": "Human-readable schedule name (ignored when calendar_event_id is set)."},
            "cron_expr": {"type": "string", "description": "5-field cron expression (required without calendar_event_id)."},
            "tz": {"type": "string", "description": "IANA timezone name (default UTC; auto-detected for event-linked)."},
            "one_shot": {"type": "boolean", "description": "Disable after first fire (default false; always true for event-linked)."},
            "duration_minutes": {"type": "integer", "minimum": 1, "description": "Auto-stop minutes (default 60; computed from event for event-linked)."},
            "enabled": {"type": "boolean", "description": "Start scheduling immediately (default false; always true for event-linked)."},
            "calendar_event_id": {"type": "string", "description": "Calendar event projection id (ce_...) to arm. Server computes all fields from the event."},
        },
        [],
    ),
    _mcp_tool(
        "scheduled_recording.update",
        "Update a scheduled recording. Only supplied fields change. Re-validates cron and duration if provided.",
        {
            "schedule_id": {"type": "string", "description": "Schedule identifier."},
            "title": {"type": "string"},
            "cron_expr": {"type": "string", "description": "5-field cron expression."},
            "tz": {"type": "string"},
            "one_shot": {"type": "boolean"},
            "duration_minutes": {"type": "integer", "minimum": 1},
            "enabled": {"type": "boolean"},
        },
        ["schedule_id"],
    ),
    _mcp_tool(
        "scheduled_recording.delete",
        "Delete a scheduled recording. Refuses if the schedule is armed or recording.",
        {"schedule_id": {"type": "string", "description": "Schedule identifier."}},
        ["schedule_id"],
    ),
    _mcp_tool(
        "scheduled_recording.cancel_armed",
        "Cancel an armed (counting-down) scheduled recording before it fires.",
        {"schedule_id": {"type": "string", "description": "Schedule identifier."}},
        ["schedule_id"],
    ),
])

# Aggregate tools from per-family modules.
for _family in FAMILIES:
    TOOLS.extend(_family.TOOLS)

# The UI owns local surface state. These IDs deliberately never mutate the
# database when sent by an external MCP client.
_UI_ONLY_VERBS = {
    "desk.open", "object.open", "object.info", "object.edit", "object.rename",
    "object.ask", "object.ask-project", "desk.toggle-view", "desk.overview",
    "desk.arrange", "desk.reset-layout", "desk.reset-to-seed", "system.search",
    "system.sheet", "window.close", "window.minimize", "window.cycle",
    "window.cycle-reverse", "window.snap-left", "window.snap-right", "window.maximize",
}


def _kind(kind: Any) -> str:
    raw = str(kind or "")
    if raw not in _KIND_ALIASES:
        raise ToolError(f"Unsupported primitive kind: {raw}")
    return _KIND_ALIASES[raw]


def _data(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ToolError("data must be an object")
    return dict(value)


def _tool_schema(name: str) -> dict[str, Any] | None:
    for tool in TOOLS:
        if tool["name"] == name:
            return tool["inputSchema"]
    # Families are the dispatch authority.  The fallback keeps an in-process
    # family extension closed even before a caller refreshes the public list.
    for family in FAMILIES:
        for tool in family.TOOLS:
            if tool["name"] == name:
                return tool["inputSchema"]
    return None


def _validate_tool_arguments(name: str, arguments: dict[str, Any]) -> None:
    schema = _tool_schema(name)
    if schema is None:
        raise ToolError(f"Unknown tool: {name}")
    try:
        Draft202012Validator(schema).validate(arguments)
    except JsonSchemaValidationError as exc:
        location = ".".join(str(part) for part in exc.absolute_path)
        detail = f"{location}: {exc.message}" if location else exc.message
        raise ToolError(f"Invalid arguments for {name}: {detail}") from exc


def _require_owner_before_schema(name: str, principal: Principal | None) -> None:
    """Preserve owner-before-body semantics for the twelve owner MCP twins.

    The shared validator closes every public schema, but these endpoints must
    return their owner denial without inspecting even a malformed body. Their
    service guards are static, so this check neither composes a service nor
    discovers a database before authorization.
    """
    if name.startswith("model_library."):
        ModelLibraryApplicationService.require_owner(principal)
    elif name.startswith("inference_assignment."):
        InferenceAssignmentService._require_owner(principal)


def _primitive_list(service: PrimitiveService, principal: Principal, kind: str) -> Any:
    return getattr(service, f"list_{kind}s" if kind != "kb" else "list_kbs")(principal)


def _primitive_get(service: PrimitiveService, principal: Principal, kind: str, item_id: str) -> Any:
    return getattr(service, f"get_{kind}")(principal, item_id)


def _primitive_create(service: PrimitiveService, principal: Principal, kind: str, data: dict[str, Any]) -> Any:
    return getattr(service, f"create_{kind}")(principal, **data)


def _primitive_update(service: PrimitiveService, principal: Principal, kind: str, item_id: str, data: dict[str, Any]) -> Any:
    return getattr(service, f"update_{kind}")(principal, item_id, **data)


def _primitive_delete(service: PrimitiveService, principal: Principal, kind: str, item_id: str) -> Any:
    return {"deleted": getattr(service, f"delete_{kind}")(principal, item_id), "id": item_id}


def _card_dict(card: Any) -> dict[str, Any]:
    """Serialize a follow-through card, including its provenance, for MCP."""
    return asdict(card)


def _compose_brief_overlay_mcp(result: dict[str, Any], db: Any, principal: Principal) -> dict[str, Any]:
    """HS-150-03: person_sections at the MCP adapter, gated by People access."""
    from holdspeak.mcp.families.people import access_mode, build_people_service, _mcp_readable
    from holdspeak.services.follow_through_service import FollowThroughService as _FT
    from holdspeak.services.person_overlay import compose_person_overlay

    # Gate: absent when People access is off.
    try:
        mode = access_mode()
    except Exception:
        mode = "off"
    if mode == "off":
        return result

    people_svc = build_people_service()
    follow_through = _FT(db)
    brief_window = (result.get("period_start", ""), result.get("period_end", ""))

    overlay = compose_person_overlay(brief_window, people_svc, follow_through, db, principal)

    if overlay.get("state") == "ready":
        # F6: filter sections to shared_intent-only via _mcp_readable pattern.
        # Person overlay sections are manager-computed summaries (counts + dates),
        # not encrypted records, so they pass through.  The underlying encrypted
        # data was already filtered by the people_service layer.
        result["person_sections"] = overlay.get("sections", [])
    elif overlay.get("state") == "unavailable":
        result["person_sections_state"] = "unavailable"

    return result


def _run(coro: Any) -> Any:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    raise ToolError("async MCP tools cannot execute inside an active event loop")


def dispatch(name: str, arguments: dict[str, Any] | None, principal: Principal) -> Any:
    """Call one day-one MCP tool and return JSON-serializable data."""
    args = arguments or {}
    if not isinstance(args, dict):
        raise ToolError("arguments must be an object")
    if _tool_schema(name) is None:
        raise ToolError(f"Unknown tool: {name}")
    retired_family_fields = {
        "ask.run": {"inference_target_id"},
        "sequence.run": {"inference_target_id"},
        "workflow.run": {"inference_target_id"},
    }
    if retired := (retired_family_fields.get(name, set()) & set(args)):
        raise ToolError(f"Invalid arguments for {name}: retired field(s): {', '.join(sorted(retired))}")
    _require_owner_before_schema(name, principal)

    # Families preserve their established transport-specific validation and
    # refusal codes. S4's retired selector families reject those names before
    # composing a service; the owner twins above already deny before body read.
    # Main-catalogue tools have no family dispatcher, so their schemas are the
    # dispatch-time closure fence.
    for family in FAMILIES:
        if any(tool["name"] == name for tool in family.TOOLS):
            return family.dispatch(name, args, principal)

    _validate_tool_arguments(name, args)
    db = get_database()
    obs = get_observer()
    primitives = PrimitiveService(db, observer=obs)
    workbenches = WorkbenchService(db, observer=obs)
    meetings = MeetingService(db, observer=obs)
    recipes = RecipeService(db, observer=obs)
    dictation = DictationService(db, observer=obs)
    events = EventQueryService(db)
    follow_through = FollowThroughService(db, observer=obs)
    monday_brief = MondayBriefService(db, observer=obs)
    desk = DeskService(db, observer=obs)
    records = DecisionRecordService(db, observer=obs)

    if name == "desk.list":
        return _primitive_list(primitives, principal, _kind(args.get("kind")))
    if name == "desk.get":
        return _primitive_get(primitives, principal, _kind(args.get("kind")), str(args.get("id") or ""))
    if name == "desk.create":
        return _primitive_create(primitives, principal, _kind(args.get("kind")), _data(args.get("data")))
    if name == "desk.update":
        return _primitive_update(primitives, principal, _kind(args.get("kind")), str(args.get("id") or ""), _data(args.get("data")))
    if name == "desk.delete":
        return _primitive_delete(primitives, principal, _kind(args.get("kind")), str(args.get("id") or ""))
    if name == "desk.verb":
        return _dispatch_verb(args, principal, primitives, workbenches)
    if name == "workbench.run":
        return _run(workbenches.run(principal, str(args.get("workbench_id") or "")))
    if name == "workbench.add_item":
        return workbenches.add_item(principal, str(args.get("workbench_id") or ""), title=str(args.get("title") or ""), **_data(args.get("data")))
    if name == "workbench.list":
        return workbenches.list_workbenches(principal)
    if name == "workbench.get":
        return workbenches.get_workbench(principal, str(args.get("workbench_id") or ""))
    if name == "workbench.create":
        fields = _workbench_fields(args.get("fields"))
        if "name" in fields:
            raise ToolError("Workbench name belongs at the top level")
        return workbenches.create_workbench(principal, name=str(args.get("name") or ""), **fields)
    if name == "workbench.update":
        return workbenches.update_workbench(
            principal, str(args.get("workbench_id") or ""), **_workbench_fields(args.get("fields"))
        )
    if name == "workbench.delete":
        workbenches.delete_workbench(principal, str(args.get("workbench_id") or ""))
        return {"deleted": True, "id": str(args.get("workbench_id") or "")}
    if name == "workbench.update_item":
        return workbenches.update_item(principal, str(args.get("workbench_id") or ""), str(args.get("item_id") or ""), **_data(args.get("fields")))
    if name == "workbench.delete_item":
        item_id = str(args.get("item_id") or "")
        workbenches.delete_item(principal, str(args.get("workbench_id") or ""), item_id)
        return {"deleted": True, "id": item_id}
    if name == "workbench.list_runs":
        return workbenches.list_runs(principal, str(args.get("workbench_id") or ""))
    if name == "recipe.list":
        return recipes.list_recipes(principal)
    if name == "recipe.get":
        return recipes.get_recipe(principal, str(args.get("recipe_id") or ""))
    if name == "recipe.run":
        allowed = ("variables", "max_tokens", "temperature", "source_ref", "source_type", "grounding_refs", "grounding_revisions", "source_revision", "deadline_at", "initiator")
        options = _data(args.get("options"))
        return _run(recipes.run(principal, str(args.get("recipe_id") or ""), input=str(args.get("input") or ""), **{key: options[key] for key in allowed if key in options}))
    if name == "recipe.chat":
        # HS-151-02: recipe.chat RETIRED. The tool definition stays so tool
        # counts documented elsewhere remain stable; the body returns the
        # retired error.
        return {
            "error": "recipe_chat_retired",
            "replacement": "POST /api/threads/{id}/turns",
            "reason": "HS-151-04 lands the thread alias",
        }
    if name == "zone.file":
        return primitives.file_member(principal, str(args.get("directory_id") or ""), str(args.get("primitive_id") or ""))
    if name == "zone.unfile":
        primitive_id = str(args.get("primitive_id") or "")
        primitives.unfile_member(principal, str(args.get("directory_id") or ""), primitive_id)
        return {"deleted": True, "id": primitive_id}
    if name == "zone.list_members":
        return primitives.list_directory_members(principal, str(args.get("directory_id") or ""))
    if name == "kb.add_member":
        return primitives.add_kb_member(principal, str(args.get("kb_id") or ""), str(args.get("ref") or ""))
    if name == "kb.remove_member":
        ref = str(args.get("ref") or "")
        primitives.remove_kb_member(principal, str(args.get("kb_id") or ""), ref)
        return {"deleted": True, "id": ref}
    if name == "kb.list_members":
        return primitives.list_kb_members(principal, str(args.get("kb_id") or ""))
    if name == "meeting.list":
        allowed = ("query", "from_date", "to_date", "limit", "cursor", "speaker", "tag", "has_open_actions")
        return meetings.list_meetings(principal, **{key: args[key] for key in allowed if key in args})
    if name == "meeting.get":
        return meetings.get_meeting(principal, meeting_id=str(args.get("meeting_id") or ""), include=args.get("include"))
    if name == "meeting.start_capture":
        config = args.get("config")
        if config is not None and not isinstance(config, dict):
            raise ToolError("config must be an object")
        return meetings.start_capture(principal, config=config)
    if name == "meeting.stop_capture":
        meeting_id = args.get("meeting_id")
        return meetings.stop_capture(principal, meeting_id=str(meeting_id) if meeting_id is not None else None)
    if name == "meeting.delete":
        meeting_id = str(args.get("meeting_id") or "")
        meetings.delete_meeting(principal, meeting_id)
        return {"deleted": True, "id": meeting_id}
    if name == "meeting.export":
        return meetings.export_meeting(principal, str(args.get("meeting_id") or ""), str(args.get("format") or ""))
    if name == "dictation.list":
        allowed = ("limit", "cursor", "source")
        return dictation.list_journal(principal, **{key: args[key] for key in allowed if key in args})
    if name == "dictation.get":
        try:
            entry_id = int(args.get("entry_id"))
        except (TypeError, ValueError) as exc:
            raise ToolError("entry_id must be an integer") from exc
        return dictation.get_entry(principal, entry_id)
    if name == "desk.snapshot":
        return desk.snapshot(principal)
    if name == "desk.needs_you":
        from holdspeak.services.project_service import ProjectService
        project_service = ProjectService(db, observer=obs)
        projects = project_service.list_projects(principal, {"include_archived": False})
        _sev = {"danger": 0, "warning": 1, "info": 2}
        items: list[dict] = []
        project_ids: set[str] = set()
        for proj in projects:
            pid = proj.get("id") or ""
            if not pid:
                continue
            try:
                room = project_service.room(principal, pid)
            except Exception:
                continue
            needs = room.get("needsYou", {})
            if needs.get("state") != "ok":
                continue
            for item in (needs.get("items") or []):
                items.append({"projectId": pid, "projectName": proj.get("name") or proj.get("title") or "", "ref": item.get("title", ""), "title": item.get("title", ""), "why": item.get("why", ""), "ageToken": item.get("since", ""), "source": item.get("source", ""), "verbHref": item.get("url"), "severity": item.get("severity", "info")})
                project_ids.add(pid)
        items.sort(key=lambda r: (_sev.get(r.get("severity", "info"), 2), r.get("ageToken") or ""))
        return {"count": len(items), "projects": sorted(project_ids), "items": items, "next": None}
    if name == "settings.hub":
        from holdspeak.config import Config, CONFIG_FILE
        from holdspeak.services.inference_assignment_service import InferenceAssignmentService
        config = Config.load()
        engines = 0; groups_set = 0; default_set = False
        try:
            from holdspeak.services.model_library_service import ModelLibraryApplicationService
            from holdspeak.services.inference_setup_service import InferenceSetupApplicationService
            setup = InferenceSetupApplicationService(db)
            lib = ModelLibraryApplicationService(db, setup_service=setup)
            lib_data = lib.get_library(principal)
            engines = lib_data.get("summary", {}).get("ready_count", 0)
        except Exception:
            pass
        try:
            from holdspeak.kernel.runtime import _configure
            broker = _configure(db)
            asn_svc = InferenceAssignmentService(db, registry=broker.inference_capability_registry)
            asn = asn_svc.assignment_summary(principal)
            for row in asn.get("rows", []):
                if row.get("id") == "global":
                    default_set = row.get("status") == "assigned"
                elif row.get("status") == "assigned":
                    groups_set += 1
        except Exception:
            pass
        connected = 0
        try:
            connected = len(db.automations.list_provider_connections())
        except Exception:
            pass
        loops = 0
        try:
            loops = len(db.cadence.list_loops())
        except Exception:
            pass
        import os
        written_at = None
        try:
            if CONFIG_FILE.exists():
                written_at = os.path.getmtime(CONFIG_FILE)
        except Exception:
            pass
        # HS-171-02: heartbeat rhythm mirror.
        heartbeat_rhythm: dict = {"loops": loops}
        try:
            from holdspeak.services.heartbeat_service import HeartbeatService
            hb = HeartbeatService(db)
            heartbeat_rhythm = hb.hub_rhythm()
        except Exception:
            heartbeat_rhythm["sweepEveryMinutes"] = 15
            heartbeat_rhythm["nextSweepAt"] = None
            heartbeat_rhythm["lastSweepAt"] = None
            heartbeat_rhythm["quiet"] = {"start": 22, "end": 8, "held": False}
        meetings_host = None
        try:
            if config.meeting.intel_profile_id:
                from holdspeak.intel.providers import resolve_meeting_placement as _rmp, endpoint_host as _eh
                _pl = _rmp(config.meeting)
                if _pl.profile_id:
                    if _pl.node:
                        meetings_host = str(_pl.node)
                    else:
                        _h = _eh(_pl.base_url)
                        meetings_host = _h if _h else (_pl.boundary or "local")
        except Exception:
            pass
        return {"models": {"engines": engines, "groupsSet": groups_set, "defaultSet": default_set}, "connections": {"connected": connected}, "voice": {"live": config.dictation.pipeline.enabled, "target": config.dictation.pipeline.target_profile_override or "auto"}, "meetings": {"intelligence": config.meeting.intel_enabled, "auto": config.meeting.intelligence_auto, "host": meetings_host}, "rhythm": heartbeat_rhythm, "sounds": {"on": config.ui.desk_sounds}, "system": {"host": "THIS DEVICE", "mesh": bool(getattr(config.mesh, "device_name", ""))}, "posture": config.control_mode, "writtenAt": written_at}
    if name == "meeting.run_intelligence":
        from holdspeak.services.meeting_intel_service import MeetingIntelService as _MIS
        intel_svc = _MIS(db, observer=obs)
        return intel_svc.run_intelligence(principal, str(args.get("meeting_id") or ""))
    if name == "meeting.proposals":
        from holdspeak.services.proposal_bridge_service import ProposalBridgeService as _PBS
        pbs = _PBS(db)
        return {"proposals": pbs.list_meeting_proposals(str(args.get("meeting_id") or ""), state=args.get("state"))}
    if name == "proposal.confirm":
        from holdspeak.services.proposal_bridge_service import ProposalBridgeService as _PBS2
        pbs = _PBS2(db)
        return pbs.confirm_proposal(principal, str(args.get("proposal_id") or ""), text=args.get("text"), owner=args.get("owner"), due=args.get("due"))
    if name == "proposal.dismiss":
        from holdspeak.services.proposal_bridge_service import ProposalBridgeService as _PBS3
        pbs = _PBS3(db)
        return pbs.dismiss_proposal(principal, str(args.get("proposal_id") or ""))
    if name == "decision_record.list":
        allowed = ("limit", "offset")
        return records.list_records(principal, **{key: args[key] for key in allowed if key in args})
    if name == "decision_record.get":
        return records.get(principal, str(args.get("record_id") or ""))
    if name == "decision_record.create_from_meeting":
        return records.create_from_meeting(principal, str(args.get("decision_id") or ""))
    if name == "decision_record.create_from_desk":
        return records.create_from_desk(principal, str(args.get("decision_id") or ""))
    if name == "decision_record.search":
        return records.search(
            principal, str(args.get("query") or ""),
            **({"limit": args["limit"]} if "limit" in args else {}),
        )
    if name == "decision.supersede":
        return primitives.supersede_decision(principal, str(args.get("decision_id") or ""))
    if name == "pipeline.events":
        allowed = ("service", "method", "principal_kind", "since", "until", "correlation_id", "errors_only", "limit")
        filters = {key: args[key] for key in allowed if key in args}
        return events.recent(principal, **filters)
    if name == "follow_through.board":
        filters = {}
        if args.get("project_id"):
            filters["project_id"] = args["project_id"]
        if args.get("owner"):
            filters["owner"] = args["owner"]
        if args.get("state"):
            filters["state"] = args["state"]
        board = follow_through.board(principal, **filters)
        return {
            "now": [_card_dict(card) for card in board.now],
            "waiting": [_card_dict(card) for card in board.waiting],
            "unassigned": [_card_dict(card) for card in board.unassigned],
            "overdue": [_card_dict(card) for card in board.overdue],
        }
    if name == "follow_through.complete":
        return follow_through.complete(
            principal,
            str(args.get("card_id") or ""),
            str(args.get("verb") or ""),
            args.get("payload"),
        )
    if name == "follow_through.commit_decision":
        return follow_through.commit_decision(
            principal,
            str(args.get("decision_id") or ""),
            owner=args.get("owner"),
            due_at=args.get("due_at"),
        )
    if name == "monday_brief.get":
        brief = monday_brief.generate(principal) if args.get("generate") else monday_brief.get_latest(principal)
        if brief is None:
            return None
        result = asdict(brief)
        return _compose_brief_overlay_mcp(result, db, principal)
    if name == "monday_brief.generate":
        result = asdict(monday_brief.generate(principal))
        return _compose_brief_overlay_mcp(result, db, principal)

    # HS-136-02: scheduled recording CRUD + cancel-armed
    if name.startswith("scheduled_recording."):
        sr_service = ScheduledRecordingService(db)
        if name == "scheduled_recording.list":
            return sr_service.list_schedules(principal)
        if name == "scheduled_recording.create":
            kwargs: dict[str, Any] = {}
            # HS-147-01: calendar_event_id triggers event-linked arm;
            # service computes everything from the event.
            if "calendar_event_id" in args:
                kwargs["calendar_event_id"] = str(args["calendar_event_id"])
            else:
                kwargs["cron_expr"] = str(args.get("cron_expr") or "")
            if "title" in args:
                kwargs["title"] = str(args["title"])
            if "tz" in args:
                kwargs["tz"] = str(args["tz"])
            if "one_shot" in args:
                kwargs["one_shot"] = bool(args["one_shot"])
            if "duration_minutes" in args:
                kwargs["duration_minutes"] = int(args["duration_minutes"])
            if "enabled" in args:
                kwargs["enabled"] = bool(args["enabled"])
            return sr_service.create_schedule(principal, **kwargs)
        if name == "scheduled_recording.update":
            schedule_id = str(args.get("schedule_id") or "")
            kwargs = {}
            if "title" in args:
                kwargs["title"] = str(args["title"])
            if "cron_expr" in args:
                kwargs["cron_expr"] = str(args["cron_expr"])
            if "tz" in args:
                kwargs["tz"] = str(args["tz"])
            if "one_shot" in args:
                kwargs["one_shot"] = bool(args["one_shot"])
            if "duration_minutes" in args:
                kwargs["duration_minutes"] = int(args["duration_minutes"])
            if "enabled" in args:
                kwargs["enabled"] = bool(args["enabled"])
            return sr_service.update_schedule(principal, schedule_id, **kwargs)
        if name == "scheduled_recording.delete":
            return sr_service.delete_schedule(principal, str(args.get("schedule_id") or ""))
        if name == "scheduled_recording.cancel_armed":
            return sr_service.cancel_armed(principal, str(args.get("schedule_id") or ""))
    raise ToolError(f"Unknown tool: {name}")


def _dispatch_verb(args: dict[str, Any], principal: Principal, primitives: PrimitiveService, workbenches: WorkbenchService) -> Any:
    verb_id = str(args.get("verb_id") or "")
    verb_args = _data(args.get("arguments"))
    if verb_id in _UI_ONLY_VERBS or verb_id.startswith(("go.", "window.", "system.")):
        return {"status": "ui_only", "verb_id": verb_id, "reason": "Opens a local surface"}
    server_verbs: dict[str, Callable[[dict[str, Any]], Any]] = {
        "desk.create": lambda value: _primitive_create(primitives, principal, _kind(value.get("kind")), _data(value.get("data"))),
        "desk.update": lambda value: _primitive_update(primitives, principal, _kind(value.get("kind")), str(value.get("id") or ""), _data(value.get("data"))),
        "desk.delete": lambda value: _primitive_delete(primitives, principal, _kind(value.get("kind")), str(value.get("id") or "")),
        "workbench.add_item": lambda value: workbenches.add_item(principal, str(value.get("workbench_id") or ""), title=str(value.get("title") or ""), **_data(value.get("data"))),
        "workbench.run": lambda value: _run(workbenches.run(principal, str(value.get("workbench_id") or ""))),
    }
    handler = server_verbs.get(verb_id)
    if handler is None:
        raise ToolError(f"Verb is not allowlisted for MCP: {verb_id}")
    return handler(verb_args)


# ── MCP-007: Palette scoping ────────────────────────────────────────
# The same species as thread_modes.palette_for (allow-list intersected
# with a registry), applied at the MCP layer.  A palette is a
# frozenset[str] of tool names.  tools_for_palette filters the
# catalogue; dispatch_for_palette rejects names outside the palette.


def tools_for_palette(palette: frozenset[str]) -> list[dict[str, Any]]:
    """Return only the tools whose names are in *palette*."""
    return [t for t in TOOLS if t["name"] in palette]


def dispatch_for_palette(
    name: str,
    arguments: dict[str, Any] | None,
    principal: Principal,
    palette: frozenset[str],
) -> Any:
    """Dispatch scoped by *palette* -- typed refusal for tools outside it."""
    if name not in palette:
        raise ToolError(
            f"Tool {name!r} is not in the configured palette"
        )
    return dispatch(name, arguments, principal)
