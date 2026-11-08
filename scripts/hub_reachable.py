#!/usr/bin/env python3
"""Which holdspeak/ modules does no entry point reach?

Roots: the console scripts in pyproject.toml ([project.scripts]),
holdspeak/web_server.py, every __main__.py and every module with an
``if __name__ == "__main__"`` block (run as ``python -m``).

Edges, read from the AST of each reached module (imports inside functions
count, so lazy route builders and conductor starts are followed):
  * ``import a.b`` and ``from a import b`` (b as a submodule when it is one),
    relative imports resolved; every parent package of a module is reached;
  * ``__import__("holdspeak.x")`` / ``importlib.import_module("holdspeak.x")``
    and any string literal that names a module exactly;
  * the dynamic tables: an f-string ``f"holdspeak.<prefix>.{name}"`` reaches
    ``holdspeak.<prefix>.<s>`` (and ``<prefix>.<s before the first dot>``) for
    every string literal ``s`` in the same module. That reads the MCP family
    list (mcp/families/__init__.py) and the conductor stops table
    (runtime/background.py).

Tests and _parked/ are never listed.

  uv run python scripts/hub_reachable.py            # unreached, by package
  uv run python scripts/hub_reachable.py --list     # one path per line
  uv run python scripts/hub_reachable.py --why holdspeak/x.py
"""
from __future__ import annotations

import argparse
import ast
import re
import sys
import tomllib
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PKG = REPO / "holdspeak"


def module_name(path: Path) -> str:
    rel = path.relative_to(REPO).with_suffix("")
    parts = list(rel.parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def all_modules() -> dict[str, Path]:
    return {module_name(p): p for p in sorted(PKG.rglob("*.py"))}


def is_parked(path: Path) -> bool:
    return "_parked" in path.relative_to(REPO).parts


def roots(mods: dict[str, Path]) -> list[str]:
    found = []
    project = tomllib.loads((REPO / "pyproject.toml").read_text())["project"]
    for target in project.get("scripts", {}).values():
        found.append(target.split(":", 1)[0])
    for group in project.get("entry-points", {}).values():
        found.extend(t.split(":", 1)[0] for t in group.values())
    found.append("holdspeak.web_server")
    for name, path in mods.items():
        if is_parked(path):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if path.name == "__main__.py" or re.search(r"""__name__\s*==\s*["']__main__["']""", text):
            found.append(name)
    return [r for r in dict.fromkeys(found) if r in mods]


def resolve_from(current: str, is_pkg: bool, level: int, module: str | None) -> str:
    if level == 0:
        return module or ""
    base = current.split(".")
    if not is_pkg:
        base = base[:-1]
    if level > 1:
        base = base[: len(base) - (level - 1)]
    return ".".join(base + ([module] if module else []))


def edges(name: str, path: Path, mods: dict[str, Path]) -> set[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return set()
    is_pkg = path.name == "__init__.py"
    out: set[str] = set()
    strings: list[str] = []
    prefixes: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            out.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            base = resolve_from(name, is_pkg, node.level, node.module)
            out.add(base)
            out.update(f"{base}.{alias.name}" for alias in node.names)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            strings.append(node.value)
        elif isinstance(node, ast.JoinedStr) and node.values:
            head = node.values[0]
            if isinstance(head, ast.Constant) and isinstance(head.value, str) and head.value.startswith("holdspeak."):
                prefixes.append(head.value)
    for s in strings:
        if s.startswith("holdspeak.") and s in mods:
            out.add(s)
    for prefix in prefixes:
        for s in strings:
            for tail in {s, s.split(".", 1)[0]}:
                if re.fullmatch(r"[A-Za-z_][\w.]*", tail):
                    out.add(prefix + tail)
    reached = set()
    for target in out:
        while target:
            if target in mods:
                reached.add(target)
            target = target.rpartition(".")[0]
    return reached


def walk(mods: dict[str, Path], start: list[str]) -> dict[str, str | None]:
    parent: dict[str, str | None] = {r: None for r in start}
    queue = list(start)
    while queue:
        node = queue.pop()
        for nxt in edges(node, mods[node], mods):
            if nxt not in parent:
                parent[nxt] = node
                queue.append(nxt)
    return parent


def lines(path: Path) -> int:
    return path.read_text(encoding="utf-8", errors="replace").count("\n")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list", action="store_true", help="print unreached paths only")
    ap.add_argument("--why", help="one import chain from a root to this path")
    ap.add_argument("--roots", action="store_true", help="print the roots")
    args = ap.parse_args()
    mods = all_modules()
    start = roots(mods)
    if args.roots:
        print("\n".join(start))
        return 0
    parent = walk(mods, start)
    if args.why:
        node: str | None = module_name((REPO / args.why).resolve())
        if node not in parent:
            print("unreached")
            return 1
        while node is not None:
            print(mods[node].relative_to(REPO).as_posix())
            node = parent[node]
        return 0
    live = {n: p for n, p in mods.items() if not is_parked(p)}
    unreached = sorted(p for n, p in live.items() if n not in parent)
    if args.list:
        for p in unreached:
            print(p.relative_to(REPO).as_posix())
        return 0
    groups: dict[str, list[int]] = defaultdict(lambda: [0, 0, 0, 0])
    for n, p in live.items():
        parts = p.relative_to(PKG).parts
        key = parts[0] if len(parts) > 1 else "."
        row = groups[key]
        size = lines(p)
        if n in parent:
            row[0] += 1
            row[1] += size
        else:
            row[2] += 1
            row[3] += size
    print(f"{'package':28} {'reached':>8} {'lines':>8} {'unreached':>10} {'lines':>8}")
    total = [0, 0, 0, 0]
    for key in sorted(groups):
        row = groups[key]
        total = [a + b for a, b in zip(total, row)]
        if row[2]:
            print(f"{key:28} {row[0]:>8} {row[1]:>8} {row[2]:>10} {row[3]:>8}")
    print(f"{'TOTAL':28} {total[0]:>8} {total[1]:>8} {total[2]:>10} {total[3]:>8}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
