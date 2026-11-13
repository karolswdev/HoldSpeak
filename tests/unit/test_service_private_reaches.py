"""Service collaborators supply facts through public methods."""
from __future__ import annotations

import ast

from tests._tree import ROOT, ast_of, python_files

# Scope exclusions from this brief: credential custody and gate/control policy.
# Each entry must still be observed; removal of a reach removes its entry too.
LEFT = {
    # Credential custody: expressly excluded by the brief.
    ("github_provider.py", "CredentialService._require_owner"),
    ("github_provider.py", "self._credentials._remove_github_login"),
    # Launch, gate/control and egress paths: preserve their current authority.
    ("agent_review.py", "self.hand_service._launch_service"),
    ("agent_review.py", "launcher._registry"),
    ("agent_review.py", "self.hand_service._control_mode"),
    ("agent_helpers.py", "hand_service._db"),
    ("agent_hand_service.py", "launcher._ledger"),
    ("agent_hand_service.py", "launcher._preflight"),
    ("agent_hand_service.py", "launcher._profiles"),
    ("agent_hand_service.py", "launcher._registry"),
    ("program_service.py", "phone._reaches"),
    ("program_runner.py", "self.hand()._launch_service()._ledger"),
    ("program_service.py", "hand._launch_service"),
    ("program_service.py", "hand._launch_service()._registry"),
    ("workbench_service.py", "service._answer_binding"),
    ("workbench_service.py", "service._require_owner"),
    # Same-owner implementation pieces, not sibling-service reads.
    ("agent_hand_preview.py", "service._control_mode"),
    ("agent_hand_preview.py", "service._db"),
    ("agent_hand_preview.py", "service._project_map"),
    # Inference family: excluded from this second-pass lane.
    ("concierge_service.py", "setup._db"),
    ("concierge_service.py", "setup._home_provider"),
    ("assignment_migration.py", "ModelProfileService(self._db)._profile_payload"),
    ("meeting_route_projection.py", "service._registry"),
    ("meeting_route_projection.py", "service._resolve"),
    ("setup_service.py", "self._defaults._db"),
}


def _service_name(name: str) -> bool:
    return name.endswith(("Service", "Conductor", "_service", "_conductor"))


def private_reaches(tree: ast.Module) -> set[tuple[int, str]]:
    """Follow constructor/parameter/field aliases within each function.

    The receiver must be a service, rather than a repository or an owner's
    split implementation helper. An own-class factory remains that owner.
    """
    nodes = list(ast.walk(tree))
    own = {node.name for node in tree.body if isinstance(node, ast.ClassDef)}
    own_factories = {
        node.name for node in nodes if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and ((node.returns is not None and ast.unparse(node.returns).strip("'\"") in own)
             or any(isinstance(child, ast.Return) and isinstance(child.value, ast.Call)
                    and isinstance(child.value.func, ast.Name) and child.value.func.id in own
                    for child in ast.walk(node)))
    }
    imported = {
        alias.asname or alias.name
        for node in nodes if isinstance(node, ast.ImportFrom)
        for alias in node.names if _service_name(alias.name) and alias.name not in own
    }
    fields = set()
    for node in nodes:
        if (isinstance(node, ast.Assign) and isinstance(node.value, ast.Name)
                and _service_name(node.value.id)):
            fields.update(ast.unparse(target) for target in node.targets
                          if isinstance(target, ast.Attribute))
    reaches = set()
    functions = [node for node in nodes if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
    for function in functions:
        collaborators = imported.copy()
        aliases = fields.copy()

        def sibling(node: ast.AST) -> bool:
            word = ast.unparse(node)
            if isinstance(node, ast.Name):
                return (word not in own | own_factories
                        and (word in collaborators or _service_name(word)))
            if isinstance(node, ast.Attribute):
                return word in aliases or (isinstance(node.value, ast.Name)
                                          and node.value.id == "self" and _service_name(node.attr))
            if isinstance(node, ast.Call):
                # Composition lookups and factory methods name their service.
                return (sibling(node.func)
                        or (isinstance(node.func, ast.Attribute) and _service_name(node.func.attr))
                        or any(isinstance(arg, ast.Constant) and isinstance(arg.value, str)
                               and arg.value.endswith("_service") for arg in node.args))
            return False

        for arg in function.args.args + function.args.kwonlyargs:
            if arg.annotation is not None and ast.unparse(arg.annotation).strip("'\"") in imported:
                collaborators.add(arg.arg)
        local_nodes = list(ast.walk(function))
        assignments = [node for node in local_nodes if isinstance(node, (ast.Assign, ast.AnnAssign))]
        while True:
            before = collaborators.copy(), aliases.copy()
            for node in assignments:
                if node.value is not None and sibling(node.value):
                    for target in node.targets if isinstance(node, ast.Assign) else [node.target]:
                        if isinstance(target, ast.Name):
                            collaborators.add(target.id)
                        elif isinstance(target, ast.Attribute):
                            aliases.add(ast.unparse(target))
            if before == (collaborators, aliases):
                break
        for node in local_nodes:
            if (isinstance(node, ast.Attribute) and node.attr.startswith("_")
                    and not node.attr.startswith("__") and sibling(node.value)):
                reaches.add((node.lineno, ast.unparse(node)))
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                    and node.func.id in {"getattr", "setattr", "hasattr"} and len(node.args) >= 2
                    and sibling(node.args[0]) and isinstance(node.args[1], ast.Constant)
                    and isinstance(node.args[1].value, str) and node.args[1].value.startswith("_")
                    and not node.args[1].value.startswith("__")):
                reaches.add((node.lineno, f"{ast.unparse(node.args[0])}.{node.args[1].value}"))
    return reaches


def test_service_modules_do_not_read_another_services_private_state():
    observed = {}
    for path in python_files("holdspeak/services", exclude=("_parked",)):
        for line, expression in private_reaches(ast_of(path)):
            observed[(path.name, expression)] = f"{path.relative_to(ROOT)}:{line}: {expression}"
    assert not observed.keys() - LEFT, "Use the owner's public method:\n" + "\n".join(
        observed[key] for key in sorted(observed.keys() - LEFT))
    assert not LEFT - observed.keys(), "Remove retired exclusions: " + repr(LEFT - observed.keys())


def test_census_follows_aliases_and_dynamic_attribute_reads():
    tree = ast.parse('''
from .sibling import SiblingService
class CallerService:
    def read(self, sibling_service):
        self.port = sibling_service
        alias = self.port
        other = SiblingService()
        return alias._cache, getattr(other, "_db"), self._own
''')
    assert {expression for _, expression in private_reaches(tree)} == {"alias._cache", "other._db"}
