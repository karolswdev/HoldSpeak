"""Memory family — MCP tools for the MemoryService surface (``memory.observations``, ``memory.page``)."""
from __future__ import annotations

from holdspeak.runtime.composition import db_or, observer_or, service as runtime_service

from typing import Any

from holdspeak.db import get_database
from holdspeak.db.core import get_observer
from holdspeak.principals import Principal
from holdspeak.services.memory_service import MemoryService

#: ``memory.search`` is a declared row now (``holdspeak/memory_operations.py``; the declared family).
TOOLS: list[dict[str, Any]] = []


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
    if name not in _OPERATION_TOOLS:
        raise LookupError(name)
    from holdspeak import operations

    ops = operations.for_runtime(
        memory_service=lambda: runtime_service(
            "memory_service",
            lambda: MemoryService(db=db_or(get_database), observer=observer_or(get_observer)),
        ),
    )
    return ops.invoke(principal, _OPERATION_TOOLS[name], dict(arguments or {}))
