"""Inference collaborators expose facts through public ports, never private state."""
from __future__ import annotations

import ast
from pathlib import Path


SERVICES = Path(__file__).resolve().parents[2] / "holdspeak" / "services"


def test_inference_services_do_not_read_collaborators_private_state() -> None:
    violations = []
    # Discover the family from the tree, so new inference/model services join
    # the check without a second inventory. Persistence's _connection remains
    # the repository boundary; self's own private implementation is permitted.
    for path in sorted(SERVICES.glob("*service.py")):
        if not path.stem.startswith(("inference_", "model_")):
            continue
        tree = ast.parse(path.read_text())
        imported_services = {
            alias.asname or alias.name
            for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
            for alias in node.names if alias.name.endswith("Service")
        }
        registry_variables = {
            target.id
            for node in ast.walk(tree) if isinstance(node, ast.Assign)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and node.value.func.id.endswith("_registry")
            for target in node.targets if isinstance(target, ast.Name)
        }
        collaborators = imported_services | registry_variables
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Attribute):
                receiver = node.value
                if (isinstance(receiver.value, ast.Name) and receiver.value.id == "self"
                        and receiver.attr != "_db"):
                    collaborators.update(t.id for t in node.targets if isinstance(t, ast.Name))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Attribute) or not node.attr.startswith("_"):
                continue
            receiver = node.value
            sibling = (
                isinstance(receiver, ast.Attribute)
                and isinstance(receiver.value, ast.Name)
                and receiver.value.id == "self"
                and receiver.attr != "_db"
            ) or (isinstance(receiver, ast.Name) and receiver.id in collaborators)
            if sibling:
                violations.append(f"{path.name}:{node.lineno}: {ast.unparse(node)}")
    assert not violations, "Use the owning service's public port:\n" + "\n".join(violations)
