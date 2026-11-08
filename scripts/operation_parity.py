#!/usr/bin/env python3
"""Operation parity census: the service operations (``<service>.<method>`` calls) that HTTP, MCP and the
CLI reach, read statically from every live route handler, every MCP tool's dispatch branch and
``holdspeak/commands`` (a CLI ``/api/...`` call reaches that route's). ``registry.invoke(p, "op")`` resolves
through its ``OperationDescriptor``; helpers are followed two calls deep; ``--rows`` adds every route.
"""
from __future__ import annotations

import ast
import importlib
import inspect
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
    OperationDescriptor = importlib.import_module("holdspeak.operations").OperationDescriptor
    for path in sorted((REPO / "holdspeak").glob("*operations.py")):
        module = importlib.import_module(f"holdspeak.{path.stem}")
        TOOL_OPS.update({k: v for k, v in getattr(module, "TOOL_OPERATIONS", {}).items() if isinstance(v, str)})
        for value in vars(module).values():
            for item in value if isinstance(value, (tuple, list)) else (value,):
                if isinstance(item, OperationDescriptor):
                    DESCRIPTORS[item.name] = (_norm(item.service) or item.service, item.method)


def _text(node: ast.AST) -> str | None:  # a string constant, or an f-string with * for each hole
    if isinstance(node, ast.JoinedStr):
        return "".join(v.value if isinstance(v, ast.Constant) else "*" for v in node.values)
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


def _parse(fn: Any) -> tuple[list[ast.stmt], dict[str, Any]] | None:
    """A function's source statements and its scope (globals plus closure cells)."""
    if (tree := _quiet(lambda: ast.parse(textwrap.dedent(inspect.getsource(fn))))) is None:
        return None
    cells = zip(fn.__code__.co_freevars, fn.__closure__ or ())
    return tree.body, {**fn.__globals__, **{name: _quiet(lambda c=cell: c.cell_contents) for name, cell in cells}}


def _assigns(nodes: Iterable[ast.AST]) -> dict[str, list[ast.AST]]:  # name -> every value it was given
    found: dict[str, list[ast.AST]] = defaultdict(list)
    for n in nodes:
        if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name):
            found[n.targets[0].id].append(n.value)
    return found


class Reader:
    """Collect the operations one body (and the helpers it calls) reaches."""

    def __init__(self, scope: dict[str, Any], bound: dict[str, str] | None = None) -> None:
        self.scope, self.seen, self.bound = scope, set(), bound or {}

    def function(self, fn: Any, depth: int = 0, args: Iterable[str | None] = ()) -> set[Op]:
        if not inspect.isfunction(fn := inspect.unwrap(fn)) or fn in self.seen or depth > 2 or not (parsed := _parse(fn)):
            return set()
        self.seen.add(fn)
        bound = {p: s for p, s in zip(fn.__code__.co_varnames[: fn.__code__.co_argcount], args) if s}
        return Reader(parsed[1], bound).nodes(parsed[0], depth, self.seen)

    def nodes(self, body: Iterable[ast.AST], depth: int, seen: set | None = None,
              around: Iterable[ast.AST] = ()) -> set[Op]:
        self.seen = self.seen if seen is None else seen
        body, ops = list(body), set()
        assigns = _assigns(n for stmt in [*body, *around] for n in ast.walk(stmt))
        for node in (n for stmt in [*body, *around] for n in ast.walk(stmt) if isinstance(n, ast.ImportFrom)):
            for alias in node.names if node.module and node.level == 0 else ():  # a local import's live object
                found = _quiet(lambda: getattr(importlib.import_module(node.module), alias.name))
                self.scope.setdefault(alias.asname or alias.name, found)
        for node in (n for stmt in body for n in ast.walk(stmt) if isinstance(n, ast.Call)):
            func = node.func
            if any(word in getattr(func, "attr", getattr(func, "id", "")) for word in ("invoke", "operation")):
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


def web_routes() -> list[tuple[str, str, set[Op]]]:
    gen, rows = importlib.import_module("gen_api_surface"), []
    for route in gen.build_reference_app().routes:
        if (endpoint := getattr(route, "endpoint", None)) is not None and type(route).__name__ != "Mount":
            methods = ",".join(sorted((getattr(route, "methods", None) or {"WS"}) - {"HEAD", "OPTIONS"}))
            rows.append((methods, route.path, Reader({}).function(endpoint)))
    return rows


def _branches(fn: Any, names: set[str]) -> tuple[dict[str, list[ast.AST]], list[ast.AST]]:
    """Each tool name -> its ``if name == ...`` branch (unnamed tools get the fall-through)."""
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
            if isinstance(key, ast.Constant) and key.value in names:
                out[key.value].append(value)
    out.update({name: tail for name in names - set(out)})
    return out, whole


def mcp_tools() -> dict[str, set[Op]]:
    from holdspeak.mcp import tools
    from holdspeak.mcp.families import FAMILIES

    owners, result = [(family, family.dispatch, {t["name"] for t in family.TOOLS}) for family in FAMILIES], {}
    owners.append((tools, tools._dispatch, {t["name"] for t in tools.TOOLS} - set().union(*(o[2] for o in owners))))
    for module, dispatch, names in owners:
        mapped = {**TOOL_OPS, **getattr(module, "TOOL_OPERATIONS", {}), **getattr(module, "ROOM_TOOL_OPERATIONS", {})}
        branches, whole = _branches(dispatch, names)
        for name, stmts in sorted(branches.items()):
            result[name] = Reader(dict(vars(module))).nodes(stmts, 0, around=whole)
            if isinstance(mapped.get(name), str) and mapped[name] in DESCRIPTORS:
                result[name].add(DESCRIPTORS[mapped[name]])
    return result


def cli_ops(routes: list[tuple[str, str, set[Op]]]) -> set[Op]:
    ops: set[Op] = set()
    for path in sorted((REPO / "holdspeak" / "commands").glob("*.py")):
        tree = ast.parse(path.read_text())
        ops |= Reader(dict(vars(importlib.import_module(f"holdspeak.commands.{path.stem}")))).nodes(tree.body, 1)
        for call in (n for n in ast.walk(tree) if isinstance(n, ast.Call)):  # call("POST", "/api/...")
            words = [_text(a) for a in call.args if _text(a)]
            verb = next((w for w in words if w in ("GET", "POST", "PATCH", "PUT", "DELETE")), None)
            for target in (w for w in words if w.startswith("/api/")):
                ops.update(op for m, p, found in routes if re.sub(r"\{[^}]*\}", "*", p) == target
                           and (verb is None or verb in m.split(",")) for op in found)
    return ops


def _expand(ops: set[Op], universe: set[Op]) -> set[Op]:  # list_*s: every concrete method it matches
    out = {op for op in ops if "*" not in op[1]}
    for service, pattern in (op for op in ops if "*" in op[1]):
        shape = re.compile(re.escape(pattern).replace(r"\*", r"\w+") + "$")
        found = {op for op in universe if op[0] == service and "*" not in op[1] and shape.match(op[1])}
        out |= found or {(service, pattern)}
    return out


def main() -> int:
    _load_descriptors()
    routes, tools = web_routes(), mcp_tools()
    web, mcp, cli = {op for r in routes for op in r[2]}, {op for ops in tools.values() for op in ops}, cli_ops(routes)
    web, mcp, cli = (_expand(ops, web | mcp | cli) for ops in (web, mcp, cli))
    tools = {name: _expand(ops, web | mcp | cli) for name, ops in tools.items()}
    blind_routes, blind_tools = Counter("/".join(p.split("/")[:3]) for _m, p, o in routes if not o), sorted(
        n for n, ops in tools.items() if not ops)
    print(f"# Operation parity census\n\nGenerated by `scripts/operation_parity.py`. An operation is one "
          f"`<service>.<method>` call.\n\n- live HTTP routes: {len(routes)} ({len(routes) - blind_routes.total()} "
          f"reach a service operation)\n- MCP tools: {len(tools)} ({len(tools) - len(blind_tools)} reach a service "
          f"operation)\n- operations: {len(web | mcp | cli)}; web only {len(web - mcp)}, MCP only "
          f"{len(mcp - web)}, both {len(web & mcp)}, CLI {len(cli)}\n\n"
          "| service | web only | MCP only | both | CLI |\n|---|---:|---:|---:|---:|")
    by = {name: Counter(s for s, _ in ops) for name, ops in
          (("web", web - mcp), ("mcp", mcp - web), ("both", web & mcp), ("cli", cli))}
    rank = sorted({s for s, _ in web | mcp | cli}, key=lambda s: (-by["web"][s], s))
    for s in rank:
        print(f"| {s} | {by['web'][s]} | {by['mcp'][s]} | {by['both'][s]} | {by['cli'][s]} |")
    print("\n## Web-only operations, by service (largest first)\n")
    for s in (s for s in rank if by["web"][s]):
        print(f"- **{s}** ({by['web'][s]}): " + ", ".join(f"`{m}`" for m in sorted(m for v, m in web - mcp if v == s)))
    print(f"\n## Not read ({blind_routes.total()} routes, {len(blind_tools)} tools)\n\nNo service operation was "
          "found in these bodies: a page, a socket, a probe, a store or ledger called without a service, or a shape "
          "the reader misses.\n\n- tools: " + ", ".join(f"`{n}`" for n in blind_tools) + "\n- routes: " + ", ".join(f"`{k}` {v}" for k, v in sorted(blind_routes.items(), key=lambda kv: (-kv[1], kv[0]))))
    if "--rows" in sys.argv:
        print("\n## Route rows\n\n" + "\n".join(f"- {m} {p}: " + ", ".join(sorted(f"{s}.{x}" for s, x in ops))
                                              for m, p, ops in routes))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
