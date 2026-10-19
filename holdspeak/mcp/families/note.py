"""Note family -- Betterment Q9 "Find the tasks", over MCP.

Each tool IS its declared operation (``holdspeak/operations.py``,
``NOTE_OUTCOME_OPERATIONS``): one schema, one set of words, the same bound
``NoteOutcomesService`` the HTTP routes reach.
"""
from __future__ import annotations

import copy
from typing import Any

from holdspeak.principals import Principal

#: Each tool and the declared operation it is.
_OPERATION_TOOLS: dict[str, str] = {
    "note.outcomes": "note.outcomes.read",
    "note.find_tasks": "note.find_tasks",
    "note.outcome.edit": "note.outcome.edit",
    "note.outcome.dismiss": "note.outcome.dismiss",
    "note.outcome.confirm": "note.outcome.confirm",
}


def _tool(name: str, operation: str) -> dict[str, Any]:
    from holdspeak import operations

    descriptor = next(d for d in operations.NOTE_OUTCOME_OPERATIONS if d.name == operation)
    schema = copy.deepcopy(dict(descriptor.args_schema))
    schema["$id"] = f"holdspeak://mcp/{name}@{descriptor.version}"
    return {"name": name, "description": descriptor.description, "inputSchema": schema}


TOOLS: list[dict[str, Any]] = [_tool(name, operation) for name, operation in _OPERATION_TOOLS.items()]


def dispatch(name: str, arguments: dict[str, Any], principal: Principal) -> Any:
    """Route a tool call.  Raises LookupError for unowned names."""
    operation = _OPERATION_TOOLS.get(name)
    if operation is None:
        raise LookupError(name)
    from holdspeak import operations
    from holdspeak.db import get_database
    from holdspeak.runtime.composition import db_or, service as runtime_service
    from holdspeak.services.note_outcomes_service import NoteOutcomesService

    ops = operations.for_runtime(
        note_outcomes_service=lambda: runtime_service(
            "note_outcomes_service",
            lambda: NoteOutcomesService(db_or(get_database),
                                        people_service=runtime_service("people_service", lambda: None),
                                        door_service=runtime_service("door_service", lambda: None)),
        ),
    )
    return ops.invoke(principal, operation, dict(arguments or {}))
