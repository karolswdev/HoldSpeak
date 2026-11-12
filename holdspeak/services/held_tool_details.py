"""One disclosure of a held call, from the tool's own input declaration.

The schema title names the tool; ``x-held-arguments`` orders its fact labels
and kinds. Only declared text scalars or named public-read fields are
disclosed; private kinds hide values.
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
        reads: dict[str, Any] = {}
        for declaration in schema.get("x-held-arguments", []):
            keys = declaration["key"]
            keys = [keys] if isinstance(keys, str) else keys
            present = [key for key in keys if _path(args, key) is not None]
            if not present:
                continue
            described.update(key.split(".")[0] for key in present)
            label = declaration.get("label") or "Write details"
            kind = declaration.get("kind")
            value = _path(args, present[0])
            if kind and kind != "text":
                kind = kind if isinstance(kind, str) and kind in {"secret", "token", "credential", "file bytes"} else "secret"
                value = f"hidden ({kind})"
            elif kind == "text" and declaration.get("label"):
                if declaration.get("read"):
                    value = _named_value(declaration["read"], args, caller, reads)
                    if type(value) not in (str, int, float, bool) or value == "":
                        value = "hidden (secret)"
                elif type(value) not in (str, int, float, bool):
                    value = "not described"
                value = str(value)
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


def _path(value: Any, path: str) -> Any:
    """Read only a declared field; alternatives support the desk's named kinds."""
    for option in path.split("|"):
        found = value
        for part in option.split("."):
            if isinstance(found, dict):
                found = found.get(part)
            elif isinstance(found, list) and part.isdigit() and int(part) < len(found):
                found = found[int(part)]
            else:
                found = None
                break
        if found is not None:
            return found
    return None


def _named_value(read: dict[str, Any], args: dict[str, Any], caller: Principal,
                 cache: dict[str, Any]) -> Any:
    """Resolve through the owning service's public read, with the caller's rights.

    A failed/forbidden read hides the reference. It never substitutes an id or
    an exception message. Cache only within this disclosure, so changed names
    are read again and become part of the details revision.
    """
    import json
    from ..mcp.tools import dispatch
    from .thread_tools import _ALL_TOOL_CLASSES
    from ..mcp.tool_authority import TOOL_AUTHORITY, WORK

    tool = read["tool"]
    if (_ALL_TOOL_CLASSES.get(tool, (None,))[0] != "evidence_read"
            or TOOL_AUTHORITY.get(tool) != WORK or caller is None):
        return None
    inputs = {key: (path[1:] if path.startswith("=") else _path(args, path))
              for key, path in read["arguments"].items()
              if path.startswith("=") or _path(args, path) is not None}
    identity = json.dumps([tool, inputs], sort_keys=True)
    if identity not in cache:
        try:
            cache[identity] = dispatch(tool, inputs, caller)
        except Exception:
            cache[identity] = None
    value = cache[identity]
    if read.get("rows"):
        paths = read["rows"] if isinstance(read["rows"], list) else [read["rows"]]
        rows = [row for path in paths for row in (_path(value, path) or [])]
        value = next((row for row in rows if isinstance(row, dict) and all(
            row.get(key) == _path(args, path) for key, path in read["match"].items()
        )), None) if isinstance(rows, list) else None
    return _path(value, read["value"])
