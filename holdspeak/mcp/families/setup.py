"""Setup family: the owner's local Setup inventory and adoption press."""
from __future__ import annotations

import copy
from typing import Any

from holdspeak.principals import Principal


_OPERATION_TO_TOOL = {
    "setup.status": "setup.status",
    "setup.use": "setup.use",
}


def _tools() -> list[dict[str, Any]]:
    from holdspeak import operations

    descriptors = {descriptor.name: descriptor for descriptor in operations.SETUP_OPERATIONS}
    tools: list[dict[str, Any]] = []
    for name, operation in _OPERATION_TO_TOOL.items():
        descriptor = descriptors[operation]
        schema = copy.deepcopy(dict(descriptor.args_schema))
        schema["$id"] = f"holdspeak://mcp/{name}@{descriptor.version}"
        tools.append({"name": name, "description": descriptor.description, "inputSchema": schema})
    return tools


TOOLS: list[dict[str, Any]] = _tools()


def dispatch(name: str, arguments: dict[str, Any], principal: Principal) -> Any:
    operation = _OPERATION_TO_TOOL.get(name)
    if operation is None:
        raise LookupError(name)

    from holdspeak import operations
    from holdspeak.db import get_database
    from holdspeak.runtime.composition import db_or, service as runtime_service
    from holdspeak.services.setup_service import SetupService

    ops = operations.for_runtime(
        setup_service=lambda: runtime_service(
            "setup_service", lambda: SetupService(db_or(get_database))
        ),
    )
    return ops.invoke(principal, operation, dict(arguments or {}))


__all__ = ["TOOLS", "dispatch"]
