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
        owner = Principal(PrincipalKind.OWNER, "held-tool-details")
        schema = next((tool["inputSchema"] for tool in TOOLS if tool["name"] == handle.name), {})
        args = resolve_held_call(handle, schema)
        result = {"call_id": handle.call_id, "tool": handle.name,
                  "words": schema.get("title") or "Tool call",
                  "facts": [{"label": "Program", "value": "not available"}] if handle.resolution_error else _facts(schema, args, owner)}
        result["binding"] = room_binding(
            {"id": handle.call_id, "thread_id": handle.thread_id, "turn": handle.turn_operation_id, **result},
            args, handle.elicitation, [caller.kind.value, caller.identity] if caller else None,
        )
        if principal.kind is not PrincipalKind.OWNER and not handle.resolution_error:
            result["facts"] = _facts(schema, args, caller)
        return result


def resolve_held_call(handle: Any, schema: Any = None) -> dict[str, Any]:
    """Freeze the selector once, including a missing match's refusal.

    Calls uses this before deciding a start is a no-op. Otherwise a new name
    match could turn its automatic no-op answer into a real write.
    """
    from ..held_arguments import resolve_target
    from ..mcp.tools import TOOLS
    with handle.details_lock:
        if schema is None:
            schema = next((tool["inputSchema"] for tool in TOOLS if tool["name"] == handle.name), {})
        if handle.resolution_error is not None and handle.resolved_args == handle.args:
            return deepcopy(handle.args)
        try:
            args = resolve_target(schema, handle.args, Principal(PrincipalKind.OWNER, "held-tool-details"))
            handle.resolution_error = None
        except ServiceError as error:
            if error.code != "program_not_found":
                raise
            args = deepcopy(handle.args)
            handle.resolution_error = {"found": False, "started": False, "code": error.code, "spoken": error.detail}
        handle.args = deepcopy(args)
        handle.resolved_args = deepcopy(args)
        return args


HELD_FACT_VALUE_LIMIT = 160
_PRIVATE_KINDS = {"secret", "token", "credential", "file bytes"}


def _facts(schema: dict[str, Any], args: dict[str, Any], reader: Principal) -> list[dict[str, str]]:
    declarations = schema.get("x-held-arguments", [])
    private = [key for row in declarations if row.get("kind") not in (None, "text")
               for key in ([row["key"]] if isinstance(row["key"], str) else row["key"])]
    facts, reads = [], {}
    covered: set[str] = set()
    for row in declarations:
        keys = [row["key"]] if isinstance(row["key"], str) else row["key"]
        covered.update(keys)
        # Hidden parents take precedence regardless of declaration order.
        keys = [key for key in keys if not any(key.startswith(parent + ".") for parent in private)]
        present = [key for key in keys if _path(args, key) is not None]
        if not present:
            continue
        value = _path(args, present[0])
        kind = row.get("kind")
        if kind != "text":
            value = f"hidden ({kind if isinstance(kind, str) and kind in _PRIVATE_KINDS else 'secret'})"
        elif not row.get("label"):
            value = "not described"
        elif row.get("format") == "word_count":
            value = f"{len(value.split())} words" if isinstance(value, str) else "hidden (secret)"
        elif row.get("read"):
            value = _named_value(row["read"], args, reader, reads)
            if type(value) not in (str, int, float, bool) or value == "":
                value = "hidden (secret)"
        elif type(value) not in (str, int, float, bool):
            value = "not described"
        value = str(value)
        if len(value) > HELD_FACT_VALUE_LIMIT:
            value = value[:HELD_FACT_VALUE_LIMIT - 1] + "…"
        facts.append({"label": row.get("label") or "Write details", "value": value})
    if not facts:
        facts.append({"label": "Write details", "value": "not described"})
    elif _uncovered(args, "", covered):
        facts.append({"label": "Other fields", "value": "hidden (secret)"})
    return facts


def _uncovered(value: Any, path: str, covered: set[str]) -> bool:
    if any(path == key or path.startswith(key + ".") for key in covered):
        return False
    if isinstance(value, dict):
        if not value:
            return bool(path) and not any(key.startswith(path + ".") for key in covered)
        return any(_uncovered(child, f"{path}.{key}" if path else key, covered)
                   for key, child in value.items())
    return True


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
    from ..mcp.server import read_for_principal
    from ..mcp.tools import TOOLS
    from ..held_arguments import strongest_effect
    from .thread_tools import _ALL_TOOL_CLASSES
    from ..mcp.tool_authority import TOOL_AUTHORITY, WORK

    tool = read["tool"]
    source = next((t for t in TOOLS if t["name"] == tool), None)
    if (_ALL_TOOL_CLASSES.get(tool, (None,))[0] != "evidence_read"
            or TOOL_AUTHORITY.get(tool) != WORK or caller is None
            or source is None or strongest_effect(source) != "read"):
        return None
    inputs = {key: (path[1:] if path.startswith("=") else _path(args, path))
              for key, path in read["arguments"].items()
              if path.startswith("=") or _path(args, path) is not None}
    identity = json.dumps([tool, inputs], sort_keys=True)
    if identity not in cache:
        try:
            cache[identity] = read_for_principal(tool, inputs, caller)
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
