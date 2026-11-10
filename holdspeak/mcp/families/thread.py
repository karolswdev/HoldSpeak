"""Thread MCP family — HS-152-05.

One tool: ``thread.set_status`` writes the thread's persisted status line
and returns the written value.  The live ``thread_status_line`` frame the
ThreadService loop sent after dispatch is parked (2026-11-08); the family
uses the composed ThreadService; it refuses unknown threads and agents.
"""
from __future__ import annotations

from holdspeak.runtime.composition import db_or, service as runtime_service

from typing import Any

from holdspeak.db import get_database
from holdspeak.principals import Principal


TOOLS: list[dict[str, Any]] = [
    {
        "name": "thread.set_status",
        "description": (
            "Set the persistent thread status line; it persists across turns."
        ),
        "inputSchema": {
            "$id": "holdspeak://mcp/thread.set_status@1",
            "type": "object",
            "properties": {
                "thread_id": {
                    "type": "string",
                    "description": "Thread ID.",
                },
                "text": {
                    "type": "string",
                    "description": "Status text; empty clears.",
                },
            },
            "required": ["thread_id", "text"],
            "additionalProperties": False,
        },
    },
]


def dispatch(name: str, arguments: dict[str, Any], principal: Principal) -> Any:
    """Dispatch thread family tools."""
    if name == "thread.set_status":
        from holdspeak.services.thread_service import ThreadService

        make = runtime_service("hub_thread_service", lambda: lambda: ThreadService(
            db_or(get_database), broadcast=lambda *_: None))
        service = make()
        return service.set_status(principal, str(arguments.get("thread_id") or ""),
                                  str(arguments.get("text") or ""))
    raise LookupError(name)


__all__ = ["TOOLS", "dispatch"]
