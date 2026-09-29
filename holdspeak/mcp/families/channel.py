"""PHILO-10-01: the Send over MCP -- each tool IS its declared operation.

Nine tools, one per ``channel.*`` operation (``holdspeak/channel_operations.py``).
A tool's input schema and words are its operation's (one source); dispatch
reaches the hub's bound registry, so MCP, HTTP and the rig's ``op`` step reach
the same declared operation and the same ``ChannelService`` instance. An
admitted call answers with its ``operation_id`` and terminal ``receipt``; a
refusal of an admitted call carries them on the error.
"""
from __future__ import annotations

import copy
from typing import Any

from holdspeak.db import get_database
from holdspeak.principals import Principal
from holdspeak.runtime.composition import db_or, service as runtime_service
from holdspeak.services.errors import ServiceError, ValidationError


def _tools() -> list[dict[str, Any]]:
    from holdspeak.channel_operations import CHANNEL_OPERATIONS

    tools = []
    for descriptor in CHANNEL_OPERATIONS:
        if not any(str(e).startswith("mcp:") for e in descriptor.exposure):
            continue  # PHILO-10-03: channel.save_email_key is HTTP only (the key is held, never an argument)
        schema = copy.deepcopy(dict(descriptor.args_schema))
        schema["$id"] = f"holdspeak://mcp/{descriptor.name}@{descriptor.version}"
        schema.setdefault("required", [])
        tools.append({"name": descriptor.name, "description": descriptor.description, "inputSchema": schema})
    return tools


TOOLS: list[dict[str, Any]] = _tools()
#: Each tool -> the declared operation it reaches (the same name).
TOOL_OPERATIONS: dict[str, str] = {tool["name"]: tool["name"] for tool in TOOLS}
CHANNEL_TOOLS: frozenset[str] = frozenset(TOOL_OPERATIONS)


def _ops() -> Any:
    """The hub's bound registry, else one bound over a bare ChannelService (off-hub only)."""
    from holdspeak import operations
    from holdspeak.services.channel_service import ChannelService

    return operations.for_runtime(
        channel_service=lambda: runtime_service("channel_service", lambda: ChannelService(db_or(get_database))),
    )


def dispatch(name: str, arguments: dict[str, Any], principal: Principal) -> Any:
    from holdspeak.operations import OperationRefused

    if name not in TOOL_OPERATIONS:
        raise LookupError(name)
    try:
        result, kernel = _ops().invoke_receipted(principal, TOOL_OPERATIONS[name], dict(arguments or {}))
    except OperationRefused as exc:
        code = "validation" if exc.code == "invalid_arguments" else exc.code
        raise ValidationError(exc.detail, code=code,
                              context={"refusal": exc.code, **(getattr(exc, "kernel", None) or {})}) from exc
    except ServiceError:
        raise
    if kernel and isinstance(result, dict):
        result = {**result, "operation_id": kernel.get("operation_id"), "receipt": kernel.get("receipt"),
                  **({"state": kernel["state"]} if kernel.get("state") and "state" not in result else {})}
    return result


__all__ = ["TOOLS", "TOOL_OPERATIONS", "CHANNEL_TOOLS", "dispatch"]
