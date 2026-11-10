#!/usr/bin/env python3
"""Operation parity census: the ``<service>.<method>`` calls HTTP, MCP and the CLI reach, read statically from each
live route handler, MCP dispatch branch or declared table row (``services/*_operations.py``) and CLI command
(its ``/api/...`` call reaches that route's); ``invoke(p, "op")`` resolves through its ``OperationDescriptor``.
"""
from __future__ import annotations

import ast
import importlib
import inspect
import linecache
import re
import sys
import textwrap
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

REPO = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(REPO), str(REPO / "scripts")]  # this checkout, and gen_api_surface beside this script
Op = tuple[str, str]
DESCRIPTORS: dict[str, Op] = {}  # declared operation name -> (service, method)
TOOL_OPS: dict[str, str] = {}  # MCP tool name -> declared operation name
RESOURCE_OPS: set[Op] = set()  # operations a declared ``mcp-resource:`` exposure reads
HTTP_OPS: dict[tuple[str, str], Op] = {}  # (method, path) a descriptor produces -> its operation
HTTP_ONLY: dict[Op, list[tuple[str, str]]] = defaultdict(list)  # row name and its reason
ROUTE_KINDS: dict[tuple[str, str], str] = {}  # API, page, docs or socket, from the assembled app


def _norm(name: str) -> str | None:
    name = re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower() if name[:1].isupper() else name
    name = re.sub(r"^(default|get|build|make|bare|live|the)_", "", name.strip("_"))
    name = re.sub(r"_(factory|or_none|instance)$", "", name).replace("_application_service", "_service")
    return name if name.endswith("service") and name != "service" else None


def _quiet(get: Any) -> Any:  # an empty closure cell, a name a module no longer has: None
    try:
        return get()
    except Exception:
        return None


def _load_descriptors() -> None:
    catalog = importlib.import_module("holdspeak.operations").DESCRIPTORS
    for mapping in (DESCRIPTORS, TOOL_OPS, HTTP_OPS, HTTP_ONLY):
        mapping.clear()
    RESOURCE_OPS.clear()
    for path in sorted((REPO / "holdspeak").glob("*operations.py")):
        module = importlib.import_module(f"holdspeak.{path.stem}")
        TOOL_OPS.update({k: v for k, v in getattr(module, "TOOL_OPERATIONS", {}).items() if isinstance(v, str)})
    # Only rows in the live catalogue count. A constant in an unregistered
    # module cannot make an undeclared call appear declared.
    DESCRIPTORS.update({i.name: (_norm(i.service) or i.service, i.method) for i in catalog})
    HTTP_OPS.update({tuple(i.http): DESCRIPTORS[i.name] for i in catalog if i.http})
    RESOURCE_OPS.update(DESCRIPTORS[i.name] for i in catalog if any(e.startswith("mcp-resource:") for e in i.exposure))
    for row in catalog:
        if any(e.startswith("http:") for e in row.exposure) and row.tool_schema is None \
                and not any(e.startswith(("mcp:", "mcp-resource:")) for e in row.exposure):
            # Older rows already explain the owner gesture in their admission
            # condition or description. New rows can state the transport reason
            # directly; no second list of route names lives in this census.
            reason = row.http_only_reason or (row.admission.condition if row.admission else row.description)
            HTTP_ONLY[DESCRIPTORS[row.name]].append((row.name, reason))


def _text(node: ast.AST) -> str | None:  # a string constant, or an f-string with * for each hole
    if isinstance(node, ast.JoinedStr):
        return "".join(v.value if isinstance(v, ast.Constant) else "*" for v in node.values)
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


def _source(fn: Any) -> str:  # a lambda's own text: the span its instructions cover
    if fn.__name__ != "<lambda>":
        return textwrap.dedent(inspect.getsource(fn))
    spots = [p for p in fn.__code__.co_positions() if None not in p and (p[0], p[2]) != (p[1], p[3])]
    first, last = min(spots, key=lambda p: (p[0], p[2])), max(spots, key=lambda p: (p[1], p[3]))
    lines = [line.encode() for line in linecache.getlines(fn.__code__.co_filename)[first[0] - 1:last[1]]]
    lines[-1], lines[0] = lines[-1][:last[3]], (lines[-1][:last[3]] if len(lines) == 1 else lines[0])[first[2]:]
    return "(" + b"".join(lines).decode() + ")"


def _parse(fn: Any) -> tuple[list[ast.stmt], dict[str, Any]] | None:  # its statements; globals and closure cells
    if (tree := _quiet(lambda: ast.parse(_source(fn)))) is None:
        return None
    cells = zip(fn.__code__.co_freevars, fn.__closure__ or ())
    return tree.body, {**fn.__globals__, **{name: _quiet(lambda c=cell: c.cell_contents) for name, cell in cells}}


def _assigns(nodes: Iterable[ast.AST]) -> dict[str, list[ast.AST]]:  # name -> every value it was given
    found: dict[str, list[ast.AST]] = defaultdict(list)
    for n in (n for n in nodes if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)):
        found[n.targets[0].id].append(n.value)
    return found


class Reader:  # the operations one body, and the helpers it calls, reach
    def __init__(self, scope: dict[str, Any], bound: dict[str, str] | None = None) -> None:
        self.scope, self.seen, self.bound = scope, set(), bound or {}

    def function(self, fn: Any, depth: int = 0, args: Iterable[str | None] = ()) -> set[Op]:
        if not inspect.isfunction(fn := inspect.unwrap(fn)) or fn in self.seen or depth > 2 or not (parsed := _parse(fn)):
            return set()
        self.seen.add(fn)
        bound = {p: s for p, s in zip(fn.__code__.co_varnames[: fn.__code__.co_argcount], args) if s}
        return Reader(parsed[1], bound).nodes(parsed[0], depth, self.seen)

    def nodes(self, body: Iterable[ast.AST], depth: int, seen: set | None = None, around: Iterable[ast.AST] = ()) -> set[Op]:
        self.seen = self.seen if seen is None else seen
        body, ops = list(body), set()
        assigns = _assigns(n for stmt in [*body, *around] for n in ast.walk(stmt))
        for node in (n for stmt in [*body, *around] for n in ast.walk(stmt) if isinstance(n, ast.ImportFrom)):
            for alias in node.names if node.module and node.level == 0 else ():  # a local import's live object
                found = _quiet(lambda: getattr(importlib.import_module(node.module), alias.name))
                self.scope.setdefault(alias.asname or alias.name, found)
        for node in (n for stmt in body for n in ast.walk(stmt) if isinstance(n, ast.Call)):
            func = node.func
            passed = [a for a in node.args if isinstance(a, (ast.Attribute, ast.Name))]  # run_in_threadpool(x.invoke, p, "op")
            if any(word in getattr(f, "attr", getattr(f, "id", "")) for f in (func, *passed) for word in ("invoke", "operation")):
                # an operation name: a string, or a local name assigned one (``name = "agent_hooks.install"``)
                names = [_text(a) or next((_text(v) for v in assigns.get(getattr(a, "id", ""), ()) if _text(v)), None)
                         for a in node.args]
                ops.update(DESCRIPTORS[n] for n in names if n in DESCRIPTORS)
            for ref in (a for a in node.args if isinstance(a, ast.Attribute)):  # run_in_threadpool(service.method, ...)
                if (service := self.service(ref.value, assigns)) and not ref.attr.startswith(("_", "bind_")) \
                        and "invoke" not in ref.attr:
                    ops.add((service, ref.attr))
            # invoke(p, "op"), and a route's own helper handed the name: call(request, "note.outcome.edit", ...)
            if isinstance(func, ast.Name) or any(word in getattr(func, "attr", getattr(func, "id", ""))
                                                 for word in ("invoke", "operation")):
                ops.update(DESCRIPTORS[n] for n in map(_text, node.args) if n in DESCRIPTORS)
            if isinstance(func, ast.Call) and getattr(func.func, "id", "") == "getattr" and len(func.args) > 1:
                if (service := self.service(func.args[0], assigns)) and isinstance(func.args[1], ast.JoinedStr):
                    ops.add((service, _text(func.args[1])))  # getattr(service, f"list_{kind}s") -> list_*s
            if isinstance(func, ast.Attribute):
                service = self.service(func.value, assigns)
                if service and not func.attr.startswith(("_", "bind_")):
                    ops.add((service, func.attr))
            elif isinstance(func, ast.Name) and depth < 2:
                helper = self.scope.get(func.id)
                if inspect.isfunction(helper) and not _norm(func.id) and helper.__module__.startswith("holdspeak"):
                    ops |= self.function(helper, depth + 1, [self.service(a, assigns) for a in node.args])
        return ops

    def service(self, expr: ast.AST, assigns: dict[str, list[ast.AST]], guard: int = 0) -> str | None:
        if guard > 6 or not isinstance(expr, (ast.Name, ast.Attribute, ast.Lambda, ast.Call)):
            return None
        if isinstance(expr, ast.Name):
            if expr.id in self.bound:
                return self.bound[expr.id]
            rest = {k: v for k, v in assigns.items() if k != expr.id}
            for value in assigns.get(expr.id, ()):
                if found := self.service(value, rest, guard + 1):
                    return found
            value = self.scope.get(expr.id)  # a live instance or class names its service
            live = None if value is None or inspect.isfunction(value) or inspect.ismodule(value) else value
            return (live is not None and _norm(getattr(live, "__name__", type(live).__name__))) or _norm(expr.id)
        if isinstance(expr, ast.Attribute):
            return _norm(expr.attr)
        if isinstance(expr, ast.Lambda):
            return self.service(expr.body, assigns, guard + 1)
        if expr.args and isinstance(expr.args[0], ast.Constant) and _norm(str(expr.args[0].value)):
            return _norm(str(expr.args[0].value))  # runtime_service("meeting_service", ...)
        helper = self.scope.get(expr.func.id) if isinstance(expr.func, ast.Name) else None
        if isinstance(helper, type):
            return _norm(helper.__name__)
        if inspect.isfunction(helper) and not _norm(expr.func.id) and (parsed := _parse(helper)):
            reader, returns = Reader(parsed[1]), [n for s in parsed[0] for n in ast.walk(s)]
            for node in (n for n in returns if isinstance(n, ast.Return) and n.value is not None):
                if found := reader.service(node.value, _assigns(returns), guard + 1):
                    return found
            return _norm(helper.__name__)
        return self.service(expr.func, assigns, guard + 1)


def _returns_html(fn: Any, seen: set[Any] | None = None) -> bool:
    """Follow a route's shell reader, including a shell returned in a worker.

    The response class and the called helper's return type are executable
    evidence. A path named /settings or /docs is not evidence of a page.
    """
    from starlette.responses import HTMLResponse

    seen = set() if seen is None else seen
    if not inspect.isfunction(fn) or fn in seen:
        return False
    seen.add(fn)
    if inspect.signature(fn).return_annotation in (HTMLResponse, "HTMLResponse"):
        return True
    if not (parsed := _parse(fn)):
        return False
    body, scope = parsed
    for node in (n for stmt in body for n in ast.walk(stmt) if isinstance(n, ast.Call)):
        # run_in_threadpool(shell_reader): the helper is an argument.
        for expr in (node.func, *node.args):
            target = scope.get(expr.id) if isinstance(expr, ast.Name) else None
            if target is HTMLResponse or (inspect.isfunction(target) and _returns_html(target, seen)):
                return True
    return False


def route_kind(route: Any, app: Any) -> str:
    from starlette.responses import HTMLResponse
    from starlette.routing import WebSocketRoute

    if isinstance(route, WebSocketRoute):
        return "socket"
    docs = {getattr(app, attr, None) for attr in
            ("openapi_url", "docs_url", "redoc_url", "swagger_ui_oauth2_redirect_url")}
    if route.path in docs:
        return "docs"
    response = getattr(route, "response_class", None)
    if (isinstance(response, type) and issubclass(response, HTMLResponse)) or _returns_html(route.endpoint):
        return "page"
    return "API"


def web_routes() -> list[tuple[str, str, set[Op]]]:
    rows = []
    app = importlib.import_module("gen_api_surface").build_reference_app()
    ROUTE_KINDS.clear()
    for route in app.routes:
        if (endpoint := getattr(route, "endpoint", None)) is not None and type(route).__name__ != "Mount":
            methods = ",".join(sorted((getattr(route, "methods", None) or {"WS"}) - {"HEAD", "OPTIONS"}))
            ROUTE_KINDS[(methods, route.path)] = route_kind(route, app)
            declared = HTTP_OPS.get((methods, route.path))  # a route produced from a descriptor
            rows.append((methods, route.path, {declared} if declared else Reader({}).function(endpoint)))
    return rows


def _branches(fn: Any, names: set[str]) -> tuple[dict[str, list[ast.AST]], list[ast.AST]]:  # tool -> if-branch
    whole = ast.parse(textwrap.dedent(inspect.getsource(fn))).body[0].body
    out, tail = defaultdict(list), []

    def tested(test: ast.AST) -> set[str]:  # name == "a" / name in {"a", "b"}, never != or not in
        positive = (n for n in ast.walk(test) if isinstance(n, ast.Compare) and all(isinstance(o, (ast.Eq, ast.In)) for o in n.ops))
        return {n.value for c in positive for n in ast.walk(c) if isinstance(n, ast.Constant)} & names

    def walk(stmts: list[ast.AST]) -> None:
        for stmt in stmts:
            if isinstance(stmt, ast.If) and (hit := tested(stmt.test)):
                for name in hit:
                    out[name].extend(stmt.body)
                walk(stmt.orelse)
            else:
                tail.append(stmt)
    walk(whole)
    for node in (n for s in tail for n in ast.walk(s) if isinstance(n, ast.Dict)):
        for key, value in zip(node.keys, node.values):  # a {"tool.name": handler} table
            # A handler, never a label: {"thought.attach_context": "attach"} names the branch below it.
            if isinstance(key, ast.Constant) and key.value in names and not isinstance(value, ast.Constant):
                out[key.value].append(value)
    out.update({name: tail for name in names - set(out)})
    return out, whole


def mcp_tools() -> dict[str, set[Op]]:
    tools, FAMILIES = importlib.import_module("holdspeak.mcp.tools"), importlib.import_module("holdspeak.mcp.families").FAMILIES
    owners, result = [(family, family.dispatch, {t["name"] for t in family.TOOLS}) for family in FAMILIES], {}
    owners.append((tools, tools._dispatch, {t["name"] for t in tools.TOOLS} - set().union(*(o[2] for o in owners))))
    # A public tool the root hands to a family (steward.nudges -> the project family's _room_tool) maps by the
    # family's own table.
    handed = {k: v for f in FAMILIES for k, v in getattr(f, "TOOL_OPERATIONS", {}).items() if isinstance(v, str)}
    for module, dispatch, names in owners:
        mapped = {**TOOL_OPS, **getattr(module, "TOOL_OPERATIONS", {}), **getattr(module, "ROOM_TOOL_OPERATIONS", {}),
                  **getattr(module, "_OPERATION_TOOLS", {}),  # a family whose tools ARE declared operations
                  **(handed if module is tools else {})}
        branches, whole = _branches(dispatch, names)
        for name, stmts in sorted(branches.items()):
            result[name] = Reader(dict(vars(module))).nodes(stmts, 0, around=whole)
            if isinstance(mapped.get(name), str) and mapped[name] in DESCRIPTORS:
                result[name].add(DESCRIPTORS[mapped[name]])
    return result


def cli_ops(routes: list[tuple[str, str, set[Op]]]) -> set[Op]:
    ops: set[Op] = set()
    for path in sorted((REPO / "holdspeak" / "commands").glob("*.py")):
        module, tree = importlib.import_module(f"holdspeak.commands.{path.stem}"), ast.parse(path.read_text())
        ops |= Reader(dict(vars(module))).nodes(tree.body, 1)
        for call in (n for n in ast.walk(tree) if isinstance(n, ast.Call)):  # call("POST", "/api/...")
            words = [_text(a) for a in call.args if _text(a)]
            verb = next((w for w in words if w in ("GET", "POST", "PATCH", "PUT", "DELETE")), None)
            for target in (w for w in words if w.startswith("/api/")):
                ops.update(op for m, p, found in routes if re.sub(r"\{[^}]*\}", "*", p) == target
                           and (verb is None or verb in m.split(",")) for op in found)
    return ops


def _expand(ops: set[Op], universe: set[Op]) -> set[Op]:
    out = {op for op in ops if "*" not in op[1]}
    for service, pattern in (op for op in ops if "*" in op[1]):
        shape = re.compile(re.escape(pattern).replace(r"\*", r"\w+") + "$")
        out |= {op for op in universe if op[0] == service and "*" not in op[1] and shape.match(op[1])} or {(service, pattern)}
    return out


def main() -> int:
    _load_descriptors()
    routes, tools = web_routes(), mcp_tools()
    web, mcp, cli = {op for r in routes for op in r[2]}, {op for ops in tools.values() for op in ops}, cli_ops(routes)
    mcp |= RESOURCE_OPS  # an MCP resource reaches its operation as a tool does
    web, mcp, cli = (_expand(ops, web | mcp | cli) for ops in (web, mcp, cli))  # list_*s: each method it matches
    tools = {name: _expand(ops, web | mcp | cli) for name, ops in tools.items()}
    bypasses = [(m, p, o) for m, p, o in routes if not o and ROUTE_KINDS[(m, p)] == "API"]
    infrastructure = Counter(kind for kind in ROUTE_KINDS.values() if kind != "API")
    blind_routes = Counter("/".join(p.split("/")[:3]) for _m, p, _o in bypasses)
    blind_tools = sorted(n for n, o in tools.items() if not o)
    http_only = (web - mcp) & HTTP_ONLY.keys()
    undeclared = web - mcp - http_only
    print(f"# Operation parity census\n\nGenerated by `scripts/operation_parity.py`. An operation is one "
          f"`<service>.<method>` call.\n\n- API routes that bypass a service: {len(bypasses)}"
          f"\n- web-only operations NOT declared HTTP-only: {len(undeclared)}"
          f"\n- operations declared HTTP-only by their row: {len(http_only)}"
          f"\n- pages, docs and sockets (not capabilities): {sum(infrastructure.values())} "
          f"(pages {infrastructure['page']}, docs {infrastructure['docs']}, sockets {infrastructure['socket']})"
          f"\n- live HTTP routes: {len(routes)} ({sum(bool(o) for _m, _p, o in routes)} reach a service operation)"
          f"\n- MCP tools: {len(tools)} ({len(tools) - len(blind_tools)} reach a service "
          f"operation)\n- operations: {len(web | mcp | cli)}; web only {len(web - mcp)}, MCP only "
          f"{len(mcp - web)}, both {len(web & mcp)}, CLI {len(cli)}\n\n"
          "| service | web only | MCP only | both | CLI |\n|---|---:|---:|---:|---:|")
    by = {name: Counter(s for s, _ in ops) for name, ops in (("web", web - mcp), ("mcp", mcp - web), ("both", web & mcp), ("cli", cli))}
    rank = sorted({s for s, _ in web | mcp | cli}, key=lambda s: (-by["web"][s], s))
    print("\n".join(f"| {s} | {by['web'][s]} | {by['mcp'][s]} | {by['both'][s]} | {by['cli'][s]} |" for s in rank))
    print("\n## Web-only operations without an HTTP-only declaration\n\n" + "\n".join(
        f"- **{s}**: " + ", ".join(f"`{m}`" for m in sorted(m for v, m in undeclared if v == s))
        for s in rank if any(v == s for v, _m in undeclared)))
    print("\n## Declared HTTP-only operations (not defects)\n\n" + "\n".join(
        f"- `{s}.{m}` — `{name}`: {reason}"
        for s, m in sorted(http_only) for name, reason in HTTP_ONLY[(s, m)]))
    print(f"\n## Not read ({len(bypasses)} API routes, {len(blind_tools)} tools)\n\nNo service operation was "
          "found in these API bodies: a probe, a store or ledger called without a service, or a shape "
          "the reader misses.\n\n- tools: " + ", ".join(f"`{n}`" for n in blind_tools) + "\n- routes: " + ", ".join(f"`{k}` {v}" for k, v in sorted(blind_routes.items(), key=lambda kv: (-kv[1], kv[0]))))
    print("\n## Pages, docs and sockets (not capabilities)\n\n" + "\n".join(
        f"- {kind}: {m} {p}" for (m, p), kind in ROUTE_KINDS.items() if kind != "API"))
    if "--rows" in sys.argv:
        print("\n## Route rows\n\n" + "\n".join(f"- {m} {p}: " + ", ".join(sorted(f"{s}.{x}" for s, x in o)) for m, p, o in routes))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
