"""MCP family for connector Watches and OWNER-mode Reactions."""
from __future__ import annotations

import asyncio
from typing import Any

from holdspeak.db import get_database, get_observer
from holdspeak.principals import Principal
from holdspeak.services.reaction_service import ReactionService


def _tool(name: str, description: str, properties: dict[str, Any], required: list[str] = []) -> dict[str, Any]:
    return {"name": name, "description": description, "inputSchema": {
        "type": "object", "properties": properties, "required": required,
        "additionalProperties": False,
    }}


TOOLS = [
    _tool("reaction.presets", "List batteries-included Watch and Reaction presets.", {}),
    _tool("watch.list", "List connector Watches and their last refresh state.", {}),
    _tool("watch.create", "Create a typed GitHub or Jira Watch.", {
        "connector_id": {"type": "string", "enum": ["gh", "github", "jira"]},
        "query_kind": {"type": "string", "enum": ["pull_requests", "issues"]},
        "name": {"type": "string"}, "query": {"type": "object"},
        "enabled": {"type": "boolean"}, "watch_id": {"type": "string"},
    }, ["connector_id", "query_kind"]),
    _tool("watch.set_enabled", "Enable or disable a Watch.", {
        "watch_id": {"type": "string"}, "enabled": {"type": "boolean"},
    }, ["watch_id", "enabled"]),
    _tool("watch.refresh", "Submit a typed connector snapshot, diff it, and deliver matching Reactions.", {
        "watch_id": {"type": "string"},
        "entities": {"type": "array", "items": {"type": "object"}},
    }, ["watch_id"]),
    _tool("watch.preview", "Query or submit a snapshot and preview changes without persisting or firing.", {
        "watch_id": {"type": "string"},
        "entities": {"type": "array", "items": {"type": "object"}},
    }, ["watch_id"]),
    _tool("event.list", "List typed events from the shared service-event ledger.", {
        "event_type": {"type": "string"}, "producer": {"type": "string"},
        "limit": {"type": "integer", "minimum": 1, "maximum": 500},
    }),
    _tool("reaction.list", "List configured Reactions.", {}),
    _tool("reaction.create", "Create a disabled-by-default Reaction targeting one Workbench.", {
        "event_pattern": {"type": "string"}, "workbench_id": {"type": "string"},
        "name": {"type": "string"}, "watch_id": {"type": "string"},
        "title_template": {"type": "string"}, "auto_run": {"type": "boolean"},
        "enabled": {"type": "boolean"}, "reaction_id": {"type": "string"},
    }, ["event_pattern", "workbench_id"]),
    _tool("reaction.set_enabled", "Enable or disable a Reaction.", {
        "reaction_id": {"type": "string"}, "enabled": {"type": "boolean"},
    }, ["reaction_id", "enabled"]),
    _tool("reaction.process", "Project unhandled service events into matching Workbenches.", {
        "limit": {"type": "integer", "minimum": 1, "maximum": 500},
    }),
]


def _run(coro: Any) -> Any:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    raise ValueError("async MCP tools cannot execute inside an active event loop")


def dispatch(name: str, arguments: dict[str, Any], principal: Principal) -> Any:
    service = ReactionService(get_database(), observer=get_observer())
    if name == "reaction.presets":
        return service.list_presets(principal)
    if name == "watch.list":
        return service.list_watches(principal)
    if name == "watch.create":
        return service.create_watch(principal, **arguments)
    if name == "watch.set_enabled":
        return service.set_watch_enabled(principal, str(arguments["watch_id"]), bool(arguments["enabled"]))
    if name == "watch.refresh":
        return _run(service.refresh_watch(principal, str(arguments["watch_id"]), arguments.get("entities")))
    if name == "watch.preview":
        return service.preview_watch(principal, str(arguments["watch_id"]), arguments.get("entities"))
    if name == "event.list":
        return service.list_events(
            principal, event_type=arguments.get("event_type"),
            producer=arguments.get("producer"), limit=arguments.get("limit", 100),
        )
    if name == "reaction.list":
        return service.list_reactions(principal)
    if name == "reaction.create":
        return service.create_reaction(principal, **arguments)
    if name == "reaction.set_enabled":
        return service.set_reaction_enabled(principal, str(arguments["reaction_id"]), bool(arguments["enabled"]))
    if name == "reaction.process":
        return _run(service.process_pending(principal, limit=arguments.get("limit", 100)))
    raise LookupError(name)
