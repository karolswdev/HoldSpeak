"""Memory family — MCP tools for the MemoryService surface."""
from __future__ import annotations

from typing import Any

from holdspeak.db import get_database
from holdspeak.db.core import get_observer
from holdspeak.principals import Principal
from holdspeak.services.memory_service import MemoryService

TOOLS: list[dict[str, Any]] = [
    {
        "name": "memory.search",
        "description": "Search the long-horizon memory store. Results are filtered by the principal's read permission.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query."},
                "kind": {"type": "string", "description": "Optional kind filter (decision, artifact, note, thread)."},
                "project_id": {"type": "string", "description": "Optional project filter."},
                "time_from": {"type": "string", "description": "Optional ISO-8601 start bound."},
                "time_to": {"type": "string", "description": "Optional ISO-8601 end bound."},
                "limit": {"type": "integer", "minimum": 1, "maximum": 500, "description": "Maximum results (default 50)."},
                "offset": {"type": "integer", "minimum": 0, "description": "Pagination offset (default 0)."},
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
]


def dispatch(name: str, arguments: dict[str, Any], principal: Principal) -> Any:
    """Route a tool call.  Raises LookupError for unowned names."""
    if name != "memory.search":
        raise LookupError(name)

    svc = MemoryService(db=get_database(), observer=get_observer())

    kwargs: dict[str, Any] = {"query": str(arguments.get("query") or "")}
    for key in ("kind", "project_id", "time_from", "time_to"):
        if key in arguments:
            kwargs[key] = arguments[key]
    if "limit" in arguments:
        kwargs["limit"] = arguments["limit"]
    if "offset" in arguments:
        kwargs["offset"] = arguments["offset"]
    return svc.search(principal, **kwargs)
