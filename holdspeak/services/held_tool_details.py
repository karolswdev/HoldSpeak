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
        if handle.resolved_args is not None and handle.resolved_args == handle.args:
            if handle.resolution_error or not schema.get("x-held-authority") or handle.state != "awaiting_decision":
                # Target identity stays fixed; completed authority is historical.
                return deepcopy(handle.args)
            # Re-read authority for a pending question. The caller's old binding
            # then refuses; this does not consent to the newly shown permission.
            current = deepcopy(handle.args)
            path = schema.get("x-held-authority-binding", "expected_authority").split(".")
            seat = current
            for part in path[:-1]:
                seat = seat.get(part, {})
            seat.pop(path[-1], None)
            handle.args = current
        try:
            args = resolve_target(schema, handle.args, Principal(PrincipalKind.OWNER, "held-tool-details"), caller=handle.principal)
            handle.resolution_error = None
        except ServiceError as error:
            if error.code != "program_not_found":
                raise
            args = deepcopy(handle.args)
            handle.resolution_error = {"found": False, "started": False, "code": error.code, "spoken": error.detail}
            if handle.name == "program.shape":
                words = " ".join(str(args.get("name") or args.get("program_id") or "").split())
                handle.resolution_error = {"found": False, "applied": False, "code": error.code,
                    "spoken": f"There is no program with the name {words}. Nothing changed."}
        handle.args = deepcopy(args)
        handle.resolved_args = deepcopy(args)
        return args


HELD_FACT_VALUE_LIMIT = 160



def _owner_private(row: dict[str, Any], args: dict[str, Any], reader: Principal) -> bool:
    if not row.get("owner_only") or reader.kind is PrincipalKind.OWNER:
        return False
    if row.get("caller_launch") and reader.kind is PrincipalKind.AGENT:
        from ..principals import agent_credentials
        credential = agent_credentials.for_principal(reader)
        if credential and credential.launch_id == _path(args, row["caller_launch"]):
            return False
    return True

def _facts(schema: dict[str, Any], args: dict[str, Any], reader: Principal) -> list[dict[str, str]]:
    declarations = schema.get("x-held-arguments", [])
    private = [key for row in declarations if row.get("kind") != "text"
               or _owner_private(row, args, reader)
               for key in ([row["key"]] if isinstance(row["key"], str) else row["key"])]
    facts, reads = [], {}
    covered: set[str] = {schema["x-held-delegate"]["arguments"]} if schema.get("x-held-delegate") else set()
    for row in declarations:
        keys = [row["key"]] if isinstance(row["key"], str) else row["key"]
        covered.update(keys)
        # Hidden parents take precedence regardless of declaration order.
        keys = [key for key in keys if not any(key.startswith(parent + ".") for parent in private)]
        present = [key for key in keys if _path(args, key) is not None or row.get("format") == "spend_limit"]
        if not present and "value" not in row:
            continue
        value = row["value"] if "value" in row else _path(args, present[0])
        kind = row.get("kind")
        if _owner_private(row, args, reader):
            value = "Hidden"
        elif kind != "text":
            value = "Hidden"
        elif not row.get("label"):
            value = "not described"
        else:
            if row.get("read"):
                value = _named_value(row["read"], args, reader, reads)
                if type(value) not in (str, int, float, bool) or value == "":
                    value = "Hidden"
            if row.get("format") == "prompt" and isinstance(value, str):
                # Every part is short, but the owner must read the whole command.
                parts = [value[i:i + HELD_FACT_VALUE_LIMIT] for i in range(0, len(value), HELD_FACT_VALUE_LIMIT)] or [""]
                facts.extend({"label": row["label"] + (f" {i + 1}" if len(parts) > 1 else ""),
                              "value": part, "redact": True} for i, part in enumerate(parts))
                continue
            if row.get("format") and value != "Hidden":
                value = _formatted(row["format"], value)
            elif type(value) not in (str, int, float, bool):
                value = "not described"
        if (str(row.get("label", "")).lower().endswith("kind") or row.get("label") == "Through") and isinstance(value, str) and value != "Hidden":
            value = value[:1].upper() + value[1:].replace("_", " ")
        value = str(value)
        if len(value) > HELD_FACT_VALUE_LIMIT:
            value = value[:HELD_FACT_VALUE_LIMIT - 1] + "…"
        facts.append({"label": row.get("label") or "Write details", "value": value,
                      **({"redact": True} if row.get("redact") else {})})
    if schema.get("x-held-delegate"):
        from importlib import import_module
        from holdspeak.mcp.tools import _tool_schema, ToolError
        module, function = schema["x-held-delegate"]["resolver"].split(":")
        root = schema["x-held-delegate"]["arguments"]
        if not any(root == path or root.startswith(path + ".") for path in private):
            try:
                name, payload = getattr(import_module(module), function)(args)
            except ToolError:
                name, payload = None, {}
            if name is not None:
                facts.extend(_facts(_tool_schema(name), payload, reader))
            else:
                facts.append({"label": "Inputs", "value": "Hidden"})
    if not facts:
        facts.append({"label": "Write details", "value": "not described"})
    elif _uncovered(args, "", covered):
        facts.append({"label": "Other fields", "value": "Hidden"})
    return facts


def _formatted(kind: str, value: Any) -> str:
    """Lengths and safe locator parts, never a body's contents or a secret."""
    if kind == "subject_line":
        return value.splitlines()[0] if isinstance(value, str) and value.splitlines() else ""
    if kind == "body_word_count":
        return f"{len(' '.join(value.splitlines()[1:]).split())} words" if isinstance(value, str) else "Hidden"
    if kind == "egress":
        return _formatted("host", value) if value else "none"
    if kind == "word_count":
        return f"{len(value.split())} words" if isinstance(value, str) else "Hidden"
    if kind == "utf8_bytes":
        return f"{len(value.encode('utf-8'))} bytes" if isinstance(value, str) else "Hidden"
    if kind == "item_count":
        return f"{len(value)} paths" if isinstance(value, list) else "Hidden"
    if kind == "spend_limit":
        if value is None:
            return "No limit"
        return str(round(float(value), 2)) if type(value) in (int, float) else "Hidden"
    if kind in {"host", "account"}:
        import re
        if not isinstance(value, str):
            return "Hidden"
        if kind == "account":
            return value if re.fullmatch(r"[A-Za-z0-9._@+\-]+", value) else "Hidden"
        from urllib.parse import urlsplit
        try:
            url = urlsplit(value if "://" in value else "//" + value)
            if url.username or url.password or url.query or url.fragment or not url.hostname:
                return "Hidden"
            return url.hostname
        except ValueError:
            return "Hidden"
    return "not described"


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
        if option == "$":
            return value
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
    inputs = {}
    for key, path in read["arguments"].items():
        if isinstance(path, dict):
            # A qualified reference is already an explicit target. Use the
            # owning filing service's parser, then its ordinary public read.
            from ..db.relationships import qualified_ref
            try:
                kind, identity = qualified_ref(_path(args, path["reference"])).split(":", 1)
                if path["part"] == "desk_kind" and tool == "desk.get":
                    from ..mcp.tools import _KIND_ALIASES
                    # decision: is a meeting decision; only the explicit
                    # desk_decision: kind may use the Desk decision read.
                    if kind == "decision":
                        return None
                    canonical_kind = "decision" if kind == "desk_decision" else kind
                    inputs[key] = next(k for k, canonical in _KIND_ALIASES.items() if canonical == canonical_kind)
                else:
                    inputs[key] = {"kind": kind, "id": identity}[path["part"]]
            except (ValueError, KeyError, TypeError, StopIteration):
                return None
        elif path.startswith("="):
            inputs[key] = path[1:]
        elif (value := _path(args, path)) is not None:
            inputs[key] = value
    if not set(source["inputSchema"].get("required", ())) <= inputs.keys():
        return None
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
            _path(row, key) == ((path.get("prefix", "") + str(_path(args, path["path"]))) if isinstance(path, dict) else _path(args, path))
            for key, path in read["match"].items()
        )), None) if isinstance(rows, list) else None
    if read.get("through"):
        if value is None:
            return None
        # The next public read uses only the filtered answer of the first.
        # It reuses this reader's policy path and cache, never owner data.
        return _named_value({**read["through"], "value": read["value"]}, value, caller, cache)
    return _path(value, read["value"])
