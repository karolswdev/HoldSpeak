"""Memory family — MCP tools for the MemoryService surface."""
from __future__ import annotations

from holdspeak.runtime.composition import db_or, observer_or, service as runtime_service

from typing import Any

from holdspeak.db import get_database
from holdspeak.db.core import get_observer
from holdspeak.principals import Principal
from holdspeak.services.memory_service import MemoryService

TOOLS: list[dict[str, Any]] = [
    {
        "name": "memory.search",
        "description": "Search memory: decisions, meetings (transcript, summary), notes, threads, actions, project milestones/risks, sends, published updates, prep briefs, calendar events. Returns records; use project.list for projects; read permission applies.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query."},
                "kind": {"type": "string", "description": "Kinds: decision, decision_record, desk_decision, artifact, meeting, note, thread, action, project_item, workbench_item, cadence, send, project_update, prep_brief, calendar_event."},
                "project_id": {"type": "string", "description": "Project ID."},
                "time_from": {"type": "string", "description": "ISO-8601 start."},
                "time_to": {"type": "string", "description": "ISO-8601 end."},
                "limit": {"type": "integer", "minimum": 1, "maximum": 500, "description": "Maximum; default 50."},
                "offset": {"type": "integer", "minimum": 0, "description": "Pagination offset."},
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
]


def _observations_tool() -> dict[str, Any]:
    """``memory.observations`` IS its declared operation
    (``memory.observations.read``): one schema, one set of words."""
    import copy

    from holdspeak.operations import MEMORY_OBSERVATIONS_READ as descriptor

    schema = copy.deepcopy(dict(descriptor.args_schema))
    schema["$id"] = f"holdspeak://mcp/memory.observations@{descriptor.version}"
    return {"name": "memory.observations", "description": descriptor.description, "inputSchema": schema}


TOOLS.append(_observations_tool())


def _page_tool() -> dict[str, Any]:
    """``memory.page`` IS its declared operation (``memory.page.read``)."""
    import copy

    from holdspeak.operations import MEMORY_PAGE_READ as descriptor

    schema = copy.deepcopy(dict(descriptor.args_schema))
    schema["$id"] = f"holdspeak://mcp/memory.page@{descriptor.version}"
    return {"name": "memory.page", "description": descriptor.description, "inputSchema": schema}


TOOLS.append(_page_tool())

#: Each read tool and the declared operation it is.
_OPERATION_TOOLS = {"memory.observations": "memory.observations.read", "memory.page": "memory.page.read"}


def dispatch(name: str, arguments: dict[str, Any], principal: Principal) -> Any:
    """Route a tool call.  Raises LookupError for unowned names."""
    if name != "memory.search" and name not in _OPERATION_TOOLS:
        raise LookupError(name)

    if name in _OPERATION_TOOLS:
        from holdspeak import operations

        ops = operations.for_runtime(
            memory_service=lambda: runtime_service(
                "memory_service",
                lambda: MemoryService(db=db_or(get_database), observer=observer_or(get_observer)),
            ),
        )
        if name == "memory.page":
            return ops.invoke(principal, "memory.page.read", dict(arguments or {}))
        return ops.invoke(principal, "memory.observations.read", dict(arguments or {}))

    svc = MemoryService(db=db_or(get_database), observer=observer_or(get_observer))

    kwargs: dict[str, Any] = {"query": str(arguments.get("query") or "")}
    for key in ("kind", "project_id", "time_from", "time_to"):
        if key in arguments:
            kwargs[key] = arguments[key]
    if "limit" in arguments:
        kwargs["limit"] = arguments["limit"]
    if "offset" in arguments:
        kwargs["offset"] = arguments["offset"]
    return svc.search(principal, **kwargs)
