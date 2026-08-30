"""Thread MCP family — HS-152-05.

One tool: ``thread.set_status`` writes the thread's persisted status line
and returns the written value.  The loop in ThreadService handles the
broadcast (``emit_thread_status_line``) after dispatch — the family
touches only the database, no global broadcast seam.
"""
from __future__ import annotations

from typing import Any

from holdspeak.db import get_database
from holdspeak.principals import Principal
from holdspeak.services.errors import ServiceError


TOOLS: list[dict[str, Any]] = [
    {
        "name": "thread.set_status",
        "description": (
            "Set the persistent status line shown in the thread head. "
            "The text is persisted across turns and visible on next load."
        ),
        "inputSchema": {
            "$id": "holdspeak://mcp/thread.set_status@1",
            "type": "object",
            "properties": {
                "thread_id": {
                    "type": "string",
                    "description": "Thread identifier.",
                },
                "text": {
                    "type": "string",
                    "description": "Status line text (empty string clears).",
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
        thread_id = str(arguments.get("thread_id") or "")
        text = str(arguments.get("text") or "")
        if not thread_id:
            raise ServiceError(
                "thread_request_invalid",
                "thread_id is required.",
                context={"status": 400},
            )
        db = get_database()
        db.threads.patch(thread_id, status_line=text)
        return {"status_line": text, "thread_id": thread_id}
    raise LookupError(name)


__all__ = ["TOOLS", "dispatch"]
