"""The service layer and two hub helpers import nothing from the web layer.

`holdspeak/services/` sits under the routes (MCP and HTTP are thin transports
over it), so a service never imports `holdspeak.web`. The skills library and
the workbench conductor make ids with their own `_new_id`, not the HTTP
primitives' copy. Parsed with `ast`, so a function-level import counts too.
"""
from __future__ import annotations

from tests import _tree
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "holdspeak"


def _web_imports(path: Path) -> list[str]:
    tree = _tree.ast_of(path)
    package = path.relative_to(ROOT.parent).with_suffix("").parts[:-1]
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.level:
                base = list(package[: len(package) - node.level + 1])
                module = ".".join(base + ([node.module] if node.module else []))
            else:
                module = node.module or ""
            if module == "holdspeak.web" or module.startswith("holdspeak.web."):
                found.append(f"{path.relative_to(ROOT.parent)}:{node.lineno} {module}")
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "holdspeak.web" or alias.name.startswith("holdspeak.web."):
                    found.append(f"{path.relative_to(ROOT.parent)}:{node.lineno} {alias.name}")
    return found


def test_services_import_nothing_from_the_web_layer() -> None:
    found = [hit for path in _tree.python_files(ROOT / "services") for hit in _web_imports(path)]
    assert found == []


def test_skills_library_and_conductor_import_nothing_from_the_web_layer() -> None:
    found = _web_imports(ROOT / "skills_library" / "__init__.py") + _web_imports(ROOT / "workbench_conductor.py")
    assert found == []
