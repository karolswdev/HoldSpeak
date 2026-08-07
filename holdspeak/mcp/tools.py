"""MCP tool schemas and transport-neutral HoldSpeak service dispatch."""
from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

from holdspeak.db import get_database
from holdspeak.principals import Principal
from holdspeak.services.meeting_service import MeetingService
from holdspeak.services.primitive_service import PrimitiveService
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


def _run(coro: Any) -> Any:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    raise ToolError("workbench.run cannot execute inside an active event loop")


def dispatch(name: str, arguments: dict[str, Any] | None, principal: Principal) -> Any:
    """Call one day-one MCP tool and return JSON-serializable data."""
    args = arguments or {}
    if not isinstance(args, dict):
        raise ToolError("arguments must be an object")
    db = get_database()
    primitives = PrimitiveService(db)
    workbenches = WorkbenchService(db)
    meetings = MeetingService(db)

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
    if name == "meeting.list":
        allowed = ("query", "from_date", "to_date", "limit", "cursor", "speaker", "tag", "has_open_actions")
        return meetings.list_meetings(principal, **{key: args[key] for key in allowed if key in args})
    if name == "meeting.get":
        return meetings.get_meeting(principal, meeting_id=str(args.get("meeting_id") or ""), include=args.get("include"))
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
