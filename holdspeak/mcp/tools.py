"""MCP tool schemas and transport-neutral HoldSpeak service dispatch."""
from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import asdict
from typing import Any

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
from holdspeak.services.primitive_service import PrimitiveService
from holdspeak.services.profile_service import ProfileService
from holdspeak.services.recipe_service import RecipeService
from holdspeak.services.workbench_service import WorkbenchService

PRIMITIVE_KINDS = ("notes", "decisions", "kbs", "directories", "workflows", "chains")
_KIND_ALIASES = {kind: kind[:-1] if kind.endswith("s") else kind for kind in PRIMITIVE_KINDS}
_KIND_ALIASES["kbs"] = "kb"


class ToolError(ValueError):
    """An expected tool failure which maps to an MCP ``isError`` result."""


TOOLS: list[dict[str, Any]] = [
    {
        "name": "desk.list",
        "description": "List HoldSpeak desk primitives of one kind.",
        "inputSchema": {
            "type": "object",
            "properties": {"kind": {"type": "string", "enum": list(PRIMITIVE_KINDS)}},
            "required": ["kind"],
            "additionalProperties": False,
        },
    },
    {
        "name": "desk.get",
        "description": "Get one HoldSpeak desk primitive by kind and id.",
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
        "description": "Create a desk primitive. Pass fields appropriate to its kind in data.",
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
        "description": "Update a desk primitive. Only supplied fields in data change.",
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
        "description": "Delete one desk primitive by kind and id.",
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


TOOLS.extend([
    _workbench_tool("workbench.list", "List Workbenches.", {}),
    _workbench_tool("workbench.get", "Get a Workbench.", {"workbench_id": {"type": "string"}}, ["workbench_id"]),
    _workbench_tool("workbench.create", "Create a Workbench. Use fields for optional Workbench configuration.", {"name": {"type": "string", "description": "Non-empty Workbench name."}, "fields": {"type": "object", "description": "Optional Workbench fields such as id, recipe_id, profile_id, schedule, or context."}}, ["name"]),
    _workbench_tool("workbench.update", "Update supplied Workbench fields.", {"workbench_id": {"type": "string"}, "fields": {"type": "object"}}, ["workbench_id", "fields"]),
    _workbench_tool("workbench.delete", "Delete a Workbench.", {"workbench_id": {"type": "string"}}, ["workbench_id"]),
    _workbench_tool("workbench.update_item", "Update supplied fields of a Workbench item.", {"workbench_id": {"type": "string"}, "item_id": {"type": "string"}, "fields": {"type": "object", "description": "Item patch fields."}}, ["workbench_id", "item_id", "fields"]),
    _workbench_tool("workbench.delete_item", "Delete a Workbench item.", {"workbench_id": {"type": "string"}, "item_id": {"type": "string"}}, ["workbench_id", "item_id"]),
    _workbench_tool("workbench.list_runs", "List Workbench runs.", {"workbench_id": {"type": "string"}}, ["workbench_id"]),
    _workbench_tool("recipe.list", "List Agent recipes.", {}),
    _workbench_tool("recipe.get", "Get an Agent recipe.", {"recipe_id": {"type": "string"}}, ["recipe_id"]),
    _workbench_tool("recipe.run", "Run an Agent recipe and return its lifecycle-backed result and minted artifact reference.", {"recipe_id": {"type": "string"}, "input": {"type": "string"}, "options": {"type": "object", "description": "Optional documented run fields."}}, ["recipe_id"]),
    _workbench_tool("recipe.chat", "Ask an Agent recipe a question.", {"recipe_id": {"type": "string"}, "question": {"type": "string"}, "options": {"type": "object", "description": "Optional chat fields."}}, ["recipe_id", "question"]),
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
    _mcp_tool("profile.list", "List inference destinations and current mesh-node liveness.", {}),
    _mcp_tool(
        "profile.get",
        "Get one inference destination when its non-secret configuration is needed.",
        {"profile_id": {"type": "string", "description": "Inference destination identifier."}},
        ["profile_id"],
    ),
    _mcp_tool(
        "profile.create",
        "Create an inference destination using non-secret profile fields.",
        {"fields": {"type": "object", "description": "Profile fields; a non-empty name is required by the service."}},
        ["fields"],
    ),
    _mcp_tool(
        "profile.update",
        "Update the supplied non-secret fields of an inference destination.",
        {
            "profile_id": {"type": "string", "description": "Inference destination identifier."},
            "fields": {"type": "object", "description": "Profile fields to change."},
        },
        ["profile_id", "fields"],
    ),
    _mcp_tool(
        "profile.delete",
        "Delete an inference destination that is no longer available.",
        {"profile_id": {"type": "string", "description": "Inference destination identifier."}},
        ["profile_id"],
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
        "pipeline_events_query",
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

    # Route to the owning family by name membership; errors inside an owned
    # dispatch (including LookupError subclasses like KeyError) surface to
    # the caller instead of reading as "not mine".
    for family in FAMILIES:
        if any(tool["name"] == name for tool in family.TOOLS):
            return family.dispatch(name, args, principal)

    db = get_database()
    obs = get_observer()
    primitives = PrimitiveService(db, observer=obs)
    workbenches = WorkbenchService(db, observer=obs)
    meetings = MeetingService(db, observer=obs)
    recipes = RecipeService(db, observer=obs)
    profiles = ProfileService(db, observer=obs)
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
        return workbenches.create_workbench(principal, name=str(args.get("name") or ""), **_data(args.get("fields")))
    if name == "workbench.update":
        return workbenches.update_workbench(principal, str(args.get("workbench_id") or ""), **_data(args.get("fields")))
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
        allowed = ("variables", "inference_target_id", "requested_placement", "max_tokens", "temperature", "source_ref", "source_type", "grounding_refs", "grounding_revisions", "source_revision", "deadline_at", "initiator")
        options = _data(args.get("options"))
        return _run(recipes.run(principal, str(args.get("recipe_id") or ""), input=str(args.get("input") or ""), **{key: options[key] for key in allowed if key in options}))
    if name == "recipe.chat":
        allowed = ("history", "grounding", "inference_target_id", "egress_context")
        options = _data(args.get("options"))
        return _run(recipes.chat(principal, str(args.get("recipe_id") or ""), question=str(args.get("question") or ""), **{key: options[key] for key in allowed if key in options}))
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
    if name == "profile.list":
        return profiles.list_profiles(principal)
    if name == "profile.get":
        return profiles.get_profile(principal, str(args.get("profile_id") or ""))
    if name == "profile.create":
        return profiles.create_profile(principal, _data(args.get("fields")))
    if name == "profile.update":
        return profiles.update_profile(principal, str(args.get("profile_id") or ""), _data(args.get("fields")))
    if name == "profile.delete":
        profile_id = str(args.get("profile_id") or "")
        profiles.delete_profile(principal, profile_id)
        return {"deleted": True, "id": profile_id}
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
    if name == "pipeline_events_query":
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
        return asdict(brief) if brief is not None else None
    if name == "monday_brief.generate":
        return asdict(monday_brief.generate(principal))
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
