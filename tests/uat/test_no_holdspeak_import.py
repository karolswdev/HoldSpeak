"""The subprocess boundary, enforced.

The conductor must never import the ``holdspeak`` package into its own
process — it can only drive the product as a subprocess. Two checks: a
static AST scan of ``uat/conductor/`` for any ``holdspeak`` import, and a
clean-subprocess import that asserts ``holdspeak`` never lands in
``sys.modules`` when the conductor is imported.
"""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

CONDUCTOR = Path(__file__).resolve().parents[2] / "uat" / "conductor"


def _imports_holdspeak(tree: ast.AST) -> list[str]:
    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "holdspeak" or alias.name.startswith("holdspeak."):
                    hits.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if mod == "holdspeak" or mod.startswith("holdspeak."):
                hits.append(mod)
    return hits


def test_conductor_source_never_imports_holdspeak():
    offenders: dict[str, list[str]] = {}
    for py in CONDUCTOR.rglob("*.py"):
        tree = ast.parse(py.read_text(), filename=str(py))
        hits = _imports_holdspeak(tree)
        if hits:
            offenders[str(py.relative_to(CONDUCTOR.parents[1]))] = hits
    assert not offenders, f"conductor imports holdspeak: {offenders}"


def test_importing_conductor_does_not_load_holdspeak():
    code = (
        "import sys\n"
        "import uat.conductor\n"
        "leaked = [m for m in sys.modules "
        "if m == 'holdspeak' or m.startswith('holdspeak.')]\n"
        "assert not leaked, leaked\n"
        "print('clean')\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(CONDUCTOR.parents[1]),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "clean" in result.stdout
