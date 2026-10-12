"""The test files a change affects, for scripts/quick_check.sh.

    python scripts/quick_check_affected.py < changed-files

Prints one test file per line:
  * every changed test file (tests/**/test_*.py, tests/uat and tests/e2e included);
  * every test file that imports a changed holdspeak module, by its AST:
    `import holdspeak.pkg.mod`, `from holdspeak.pkg.mod import x` and
    `from holdspeak.pkg import mod` (the package plus the module name);
    a changed package `__init__` matches its package;
  * every test file that imports a changed scripts/*.py (`scripts.name`,
    `import name` or `from name import`, or names `scripts/name.py`);
  * the files in QUICK_TESTS (space separated), the author's override.
"""
from __future__ import annotations

import ast
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEARCH = ["tests/unit", "tests/integration", "tests/critical", "tests/web", "tests/mcp", "tests/uat"]


def module_of(path: str) -> str | None:
    if not (path.startswith("holdspeak/") and path.endswith(".py")):
        return None
    mod = path[:-3].replace("/", ".")
    return mod[: -len(".__init__")] if mod.endswith(".__init__") else mod


def imports_of(source: str) -> tuple[set[str], set[str]]:
    """(dotted modules imported, bare top-level names imported)."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return set(), set()
    mods: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mods.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            mods.add(node.module)
            for alias in node.names:
                mods.add(f"{node.module}.{alias.name}")
    return mods, {m.split(".")[0] for m in mods}


def main() -> int:
    changed = [line.strip() for line in sys.stdin if line.strip()]
    out: set[str] = set()
    for path in changed:
        name = Path(path).name
        if path.startswith("tests/") and name.startswith("test_") and name.endswith(".py") and "/_parked/" not in path:
            if (ROOT / path).exists():  # a moved or parked test file is not a missing one
                out.add(path)
    modules = {m for m in (module_of(p) for p in changed) if m}
    scripts = {Path(p).stem for p in changed if p.startswith("scripts/") and p.endswith(".py") and "/" not in p[len("scripts/"):]}
    if modules or scripts:
        for top in SEARCH:
            for test in sorted((ROOT / top).rglob("test_*.py")):
                rel = test.relative_to(ROOT).as_posix()
                if "/_parked/" in rel:
                    continue
                source = test.read_text(encoding="utf-8", errors="replace")
                mods, tops = imports_of(source)
                if modules & mods:
                    out.add(rel)
                    continue
                for s in scripts:
                    if f"scripts.{s}" in mods or s in tops or f"scripts/{s}.py" in source:
                        out.add(rel)
                        break
    for extra in os.environ.get("QUICK_TESTS", "").split():
        out.add(extra)
    for path in sorted(out):
        if (ROOT / path.split("::")[0]).exists():
            print(path)
        else:
            print(f"quick_check: QUICK_TESTS names a missing file: {path}", file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
