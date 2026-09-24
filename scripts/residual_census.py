#!/usr/bin/env python3
"""The Phase 5 residual set: what still bypasses the operation contract (PHILO-5-01).

A residual identity is ``(transport, entry point, discriminator)``:

* **mcp** — every tool the MCP dispatcher wires by hand (``holdspeak/mcp/tools.py``
  branches and the per-family dispatchers). ``desk.list/get/create/update/delete``
  are split by ``kind``; ``desk.verb`` by server verb and kind. An identity that
  an operation descriptor exposes (``holdspeak.operations``) is NOT residual.
* **http** — every syntactic ``*Service(...)`` construction in a route module
  (``holdspeak/web/routes``), keyed by module and enclosing function.

This is the charter's counting basis (main ``4b4f8d94``: 67 constructions across
46 route files; 225 assembled tools). The committed set lives in
``docs/internal/philo/phase-5/residual-set.json``. ``--check`` fails when the
tree has an identity the set does not list (a NEW residual) or the set lists an
identity the tree no longer has (a PAID entry left behind).

    uv run python scripts/residual_census.py --check [--root <tree>]
    uv run python scripts/residual_census.py --write
"""
from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SET_PATH = REPO / "docs" / "internal" / "philo" / "phase-5" / "residual-set.json"

_KINDED = ("desk.list", "desk.get", "desk.create", "desk.update", "desk.delete")
_VERB_KINDED = ("desk.create", "desk.update", "desk.delete")
_VERB_PLAIN = ("workbench.add_item", "workbench.run")

# Runs inside the tree under census, so it reads THAT tree's catalogue.
_MCP_PROBE = r"""
import json, sys
sys.path.insert(0, sys.argv[1])
from holdspeak.mcp.tools import TOOLS, PRIMITIVE_KINDS
from holdspeak.mcp.families import FAMILIES
family_of = {}
for family in FAMILIES:
    for tool in family.TOOLS:
        family_of[tool["name"]] = family.__name__
try:
    from holdspeak.operations import DESCRIPTORS
    exposure = [e for d in DESCRIPTORS for e in d.exposure]
except ImportError:  # a tree with no contract exposes nothing through it
    exposure = []
print(json.dumps({"tools": sorted({t["name"] for t in TOOLS}), "kinds": list(PRIMITIVE_KINDS),
                  "family_of": family_of, "exposure": exposure}))
"""


def _mcp(root: Path) -> list[dict[str, str]]:
    out = subprocess.run([sys.executable, "-c", _MCP_PROBE, str(root)], cwd=str(root),
                         check=True, capture_output=True, text=True).stdout
    probe = json.loads(out.strip().splitlines()[-1])
    covered = {e.split(":", 1)[1] for e in probe["exposure"] if e.startswith("mcp:")}
    entries: list[dict[str, str]] = []

    def add(tool: str, discriminator: str, reason: str) -> None:
        key = f"{tool}[{discriminator}]" if discriminator else tool
        if key not in covered:
            entries.append({"transport": "mcp", "entry_point": tool,
                            "discriminator": discriminator, "reason": reason})

    for tool in probe["tools"]:
        family = probe["family_of"].get(tool)
        reason = (f"hand-wired family dispatcher ({family.replace('.', '/')}.py)" if family
                  else "hand-wired branch in holdspeak/mcp/tools.py dispatch")
        if tool in _KINDED:
            for kind in probe["kinds"]:
                add(tool, f"kind={kind}", reason + "; generic getattr over PrimitiveService")
        elif tool == "desk.verb":
            for verb in _VERB_KINDED:
                for kind in probe["kinds"]:
                    add(tool, f"verb_id={verb},kind={kind}", reason + " (_dispatch_verb)")
            for verb in _VERB_PLAIN:
                add(tool, f"verb_id={verb}", reason + " (_dispatch_verb)")
        else:
            add(tool, "", reason)
    return entries


def _public_tools(root: Path) -> int:
    out = subprocess.run([sys.executable, "-c", _MCP_PROBE, str(root)], cwd=str(root),
                         check=True, capture_output=True, text=True).stdout
    return len(json.loads(out.strip().splitlines()[-1])["tools"])


def _enclosing(tree: ast.AST) -> dict[int, str]:
    names: dict[int, str] = {}

    def walk(node: ast.AST, scope: str) -> None:
        for child in ast.iter_child_nodes(node):
            inner = scope
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                inner = f"{scope}.{child.name}" if scope else child.name
            if isinstance(child, ast.Call):
                names[id(child)] = scope or "<module>"
            walk(child, inner)

    walk(tree, "")
    return names


def _http(root: Path) -> list[dict[str, str]]:
    seen: dict[tuple[str, str], int] = {}
    for path in sorted((root / "holdspeak" / "web" / "routes").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        scopes = _enclosing(tree)
        rel = path.relative_to(root).as_posix()
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else ""
            if name.endswith("Service"):
                key = (f"{rel}::{scopes.get(id(node), '<module>')}", name)
                seen[key] = seen.get(key, 0) + 1
    return [{"transport": "http", "entry_point": entry, "discriminator": cls,
             "reason": "route builds its own service instance instead of the hub's bound one"
             + (f" ({count} constructions)" if count > 1 else "")}
            for (entry, cls), count in sorted(seen.items())]


def census(root: Path) -> dict[str, object]:
    http, mcp = _http(root), _mcp(root)
    constructions = 0
    for entry in http:
        reason = entry["reason"]
        constructions += int(reason.rsplit("(", 1)[1].split()[0]) if reason.endswith("constructions)") else 1
    return {"entries": mcp + http, "http_constructions": constructions, "public_tools": _public_tools(root)}


def _key(entry: dict[str, str]) -> tuple[str, str, str]:
    return (entry["transport"], entry["entry_point"], entry["discriminator"])


def check(root: Path, committed: dict) -> list[str]:
    now = {_key(e) for e in census(root)["entries"]}  # type: ignore[index]
    listed = {_key(e) for e in committed["entries"]}
    problems = [f"NEW residual identity (not in the set): {k}" for k in sorted(now - listed)]
    problems += [f"PAID entry still listed (the tree no longer has it): {k}" for k in sorted(listed - now)]
    return problems


def main(argv: list[str]) -> int:
    root = REPO
    if "--root" in argv:
        root = Path(argv[argv.index("--root") + 1]).resolve()
    if "--write" in argv:
        current = SET_PATH.exists() and json.loads(SET_PATH.read_text()) or {}
        result = census(root)
        payload = {
            "pinned_at": current.get("pinned_at", "4b4f8d94"),
            "counting": ("mcp: every assembled tool dispatched by hand, desk.* split by kind and "
                         "desk.verb by verb and kind, minus the identities an operation descriptor "
                         "exposes; http: every syntactic *Service(...) construction in "
                         "holdspeak/web/routes, keyed by module::function"),
            "baseline": current.get("baseline", {}),
            "paid": current.get("paid", []),
            # PHILO-5-02: a newly exposed tool raises the public count while
            # the residual set shrinks -- two measurements, reported apart.
            "public_tools_added": current.get("public_tools_added", []),
            # An identity that changed name without being paid (its reason says why).
            "moved": current.get("moved", []),
            "measurements": {
                "residual_identities": len(result["entries"]),  # type: ignore[arg-type]
                "residual_mcp": sum(1 for e in result["entries"] if e["transport"] == "mcp"),  # type: ignore[union-attr]
                "residual_http": sum(1 for e in result["entries"] if e["transport"] == "http"),  # type: ignore[union-attr]
                "http_constructions": result["http_constructions"],
                "public_tools": result["public_tools"],
            },
            "entries": result["entries"],
        }
        SET_PATH.parent.mkdir(parents=True, exist_ok=True)
        SET_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(f"WROTE {SET_PATH.relative_to(REPO)} ({len(result['entries'])} identities)")  # type: ignore[arg-type]
        return 0
    committed = json.loads(SET_PATH.read_text(encoding="utf-8"))
    problems = check(root, committed)
    for line in problems:
        print(line)
    if problems:
        print(f"RESIDUAL FENCE RED: {len(problems)} problem(s) against {root}")
        return 1
    print(f"RESIDUAL FENCE GREEN: {len(committed['entries'])} identities match {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
