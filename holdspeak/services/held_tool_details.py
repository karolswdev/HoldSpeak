"""One disclosure of a held call, from the tool's own input declaration.

The schema title names the tool; ``x-held-arguments`` orders its fact labels
and kinds. Only declared text scalars are disclosed; private kinds hide values.
Unlabelled, structured and undeclared arguments are never serialized.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from ..principals import Principal, PrincipalKind
from .errors import ServiceError
from .room_binding import room_binding


def check_held_call_reader(principal: Principal, caller: Any) -> None:
    if principal.kind is not PrincipalKind.OWNER and not (
        principal.kind is PrincipalKind.AGENT and caller is not None
        and caller.kind is PrincipalKind.AGENT and principal.identity == caller.identity
    ):
        raise ServiceError("held_call_forbidden", "This call belongs to another principal.",
                           context={"status": 403, "code": "held_call_forbidden"})


def held_call_details(handle: Any, principal: Principal) -> dict[str, Any]:
    caller = handle.principal
    check_held_call_reader(principal, caller)
    from ..mcp.tools import TOOLS

    with handle.details_lock:
        args = deepcopy(handle.args)
        schema = next((tool["inputSchema"] for tool in TOOLS if tool["name"] == handle.name), {})
        words = schema.get("title") or "Tool call"
        facts = []
        described = set()
        for declaration in schema.get("x-held-arguments", []):
            key = declaration["key"]
            if key not in args:
                continue
            described.add(key)
            label = declaration.get("label") or "Write details"
            kind = declaration.get("kind")
            if kind and kind != "text":
                # The kind comes from code, never from the engine's arguments.
                kind = kind if isinstance(kind, str) and kind in {"secret", "token", "credential", "file bytes"} else "secret"
                value = f"hidden ({kind})"
            elif kind == "text" and declaration.get("label") and type(args[key]) in (str, int, float, bool):
                value = str(args[key])
            else:
                value = "not described"
            facts.append({"label": label, "value": value})
        if not facts or set(args) - described:
            facts.append({"label": "Write details", "value": "not described"})
        result = {"call_id": handle.call_id, "tool": handle.name, "words": words, "facts": facts}
        result["binding"] = room_binding(
            {"id": handle.call_id, "thread_id": handle.thread_id, "turn": handle.turn_operation_id, **result},
            args, handle.elicitation, [caller.kind.value, caller.identity] if caller else None,
        )
        return result
