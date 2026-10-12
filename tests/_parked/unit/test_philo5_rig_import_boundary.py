"""PHILO-5-04: the rig stays outside the operation registry process."""
from __future__ import annotations

import ast
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
RIG_SCRIPTS = (
    REPO / "scripts/graph_walk.py",
    REPO / "scripts/philo5_pairs.py",
)
FORBIDDEN_MODULE = "holdspeak.operations"


def _literal_module(value: ast.AST | None) -> str | None:
    if isinstance(value, ast.Constant) and isinstance(value.value, str):
        return value.value
    return None


def _operation_import_violations(source: str, *, filename: str) -> list[str]:
    """Return source locations that would load the operation registry."""
    tree = ast.parse(source, filename=filename)
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == FORBIDDEN_MODULE or alias.name.startswith(
                    f"{FORBIDDEN_MODULE}."
                ):
                    violations.append(
                        f"{filename}:{node.lineno}: import {alias.name}"
                    )
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module == FORBIDDEN_MODULE or module.startswith(
                f"{FORBIDDEN_MODULE}."
            ):
                violations.append(
                    f"{filename}:{node.lineno}: from {module} import ..."
                )
            elif module == "holdspeak" and any(
                alias.name == "operations" for alias in node.names
            ):
                violations.append(
                    f"{filename}:{node.lineno}: from holdspeak import operations"
                )
        elif isinstance(node, ast.Call):
            function = node.func
            dynamic = (
                isinstance(function, ast.Name)
                and function.id in {"__import__", "import_module"}
            ) or (
                isinstance(function, ast.Attribute)
                and function.attr == "import_module"
                and isinstance(function.value, ast.Name)
                and function.value.id == "importlib"
            )
            if dynamic and node.args:
                imported = _literal_module(node.args[0])
                if imported == FORBIDDEN_MODULE or (
                    imported and imported.startswith(f"{FORBIDDEN_MODULE}.")
                ):
                    violations.append(
                        f"{filename}:{node.lineno}: dynamic import {imported}"
                    )
    return violations


def test_rig_scripts_do_not_import_operation_registry() -> None:
    violations = [
        violation
        for path in RIG_SCRIPTS
        for violation in _operation_import_violations(
            path.read_text(encoding="utf-8"), filename=str(path.relative_to(REPO))
        )
    ]
    assert not violations, "rig import boundary crossed:\n" + "\n".join(violations)


def test_same_fence_rejects_forbidden_source_mutations() -> None:
    mutations = (
        "import holdspeak.operations",
        "from holdspeak.operations import OperationRegistry",
        "from holdspeak import operations",
        "import importlib\nimportlib.import_module('holdspeak.operations')",
        "__import__('holdspeak.operations')",
    )
    for path in RIG_SCRIPTS:
        source = path.read_text(encoding="utf-8")
        for mutation in mutations:
            violations = _operation_import_violations(
                source + "\n" + mutation + "\n", filename=str(path.relative_to(REPO))
            )
            assert violations, f"mutation was accepted for {path}: {mutation}"
