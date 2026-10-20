"""P10 regressions for watch offers and transport boundaries."""
from __future__ import annotations

import ast
from importlib.util import resolve_name
from pathlib import Path
from typing import Any

import pytest


def _imported_modules(tree: ast.AST, package: str) -> set[str]:
    """Resolve absolute, relative, and imported-alias module names."""
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
            continue
        if not isinstance(node, ast.ImportFrom):
            continue
        if node.level:
            relative = "." * node.level + (node.module or "")
            try:
                base = resolve_name(relative, package)
            except ImportError:
                base = ""
        else:
            base = node.module or ""
        if base:
            modules.add(base)
        for alias in node.names:
            if alias.name != "*" and base:
                modules.add(f"{base}.{alias.name}")
    return modules


def _package_for_mcp_file(path: Path, mcp_root: Path) -> str:
    relative_parts = path.relative_to(mcp_root).parts[:-1]
    return ".".join(("holdspeak", "mcp", *relative_parts))


def _web_route_imports(tree: ast.AST, package: str) -> set[str]:
    return {
        module for module in _imported_modules(tree, package)
        if module == "holdspeak.web.routes" or module.startswith("holdspeak.web.routes.")
    }


@pytest.mark.parametrize(
    ("source", "package", "expected"),
    [
        (
            "from ..web.routes import providers",
            "holdspeak.mcp",
            {"holdspeak.web.routes", "holdspeak.web.routes.providers"},
        ),
        ("from ...web import routes", "holdspeak.mcp.families", {"holdspeak.web.routes"}),
        ("from holdspeak.web import routes", "holdspeak.mcp", {"holdspeak.web.routes"}),
    ],
)
def test_web_route_detector_resolves_relative_and_alias_imports(
    source: str, package: str, expected: set[str],
) -> None:
    tree = ast.parse(source)
    assert _web_route_imports(tree, package) == expected

def test_mcp_python_sources_have_no_web_route_imports() -> None:
    """MCP modules stay below the web transport boundary."""
    mcp_root = Path(__file__).parents[2] / "holdspeak" / "mcp"
    violations: list[str] = []
    for path in sorted(mcp_root.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        package = _package_for_mcp_file(path, mcp_root)
        for module in sorted(_web_route_imports(tree, package)):
            violations.append(f"{path}: {module}")
    assert violations == [], "MCP imports a web route module: " + "; ".join(violations)


def test_provider_and_steward_helpers_have_one_wire_source() -> None:
    """HTTP, MCP, resources, and services use the same helper objects."""
    from holdspeak.mcp.families import project as project_family
    from holdspeak.mcp import resources
    from holdspeak.services import provider_manifest_service as provider_service
    from holdspeak.services import steward_serialization_service as steward_service
    from holdspeak.services import project_service
    from holdspeak.services import steward_contract
    from holdspeak.web.routes import providers as provider_route
    from holdspeak.web.routes import steward as steward_route

    assert provider_route.collect_provider_manifests is provider_service.collect_provider_manifests
    assert project_family.collect_provider_manifests is provider_service.collect_provider_manifests
    assert provider_route._NATIVE_PROVIDERS is provider_service._NATIVE_PROVIDERS

    for name in ("_serialize_policy", "_serialize_run", "_serialize_step", "_serialize_steps"):
        assert getattr(steward_route, name) is getattr(steward_service, name)
        assert getattr(project_family, name) is getattr(steward_service, name)
    assert steward_route._serialize_runs is steward_service._serialize_runs
    assert resources._serialize_run is steward_service._serialize_run
    assert resources._serialize_steps is steward_service._serialize_steps
    assert project_service._serialize_run is steward_service._serialize_run
    assert steward_contract._serialize_policy is steward_service._serialize_policy
    assert steward_contract._serialize_run is steward_service._serialize_run
    assert steward_contract._serialize_steps is steward_service._serialize_steps

    class Adapter:
        def __init__(self, provider_id: str) -> None:
            self.provider_id = provider_id

        def manifest(self) -> dict[str, Any]:
            return {"provider_id": self.provider_id, "transport": "test"}

        def readiness(self, principal: Any) -> dict[str, Any]:
            return {"principal": principal, "ready": True}

    kwargs = {
        "github_adapter": Adapter("github"),
        "jira_adapter": Adapter("jira"),
        "principal": "owner:test",
    }
    assert provider_route.collect_provider_manifests(**kwargs) == project_family.collect_provider_manifests(**kwargs)

    run = {
        "id": "run-1",
        "project_id": "project-1",
        "policy_id": None,
        "state": "completed",
        "phase": "done",
        "summary_json": '{"changed": 1}',
        "requested_by": "owner:test",
        "watermark": "wm-1",
        "created_at": "2026-10-19T00:00:00Z",
        "updated_at": "2026-10-19T00:01:00Z",
        "started_at": None,
        "completed_at": "2026-10-19T00:01:00Z",
        "stop_requested_at": None,
    }
    assert steward_route._serialize_run(run) == steward_service._serialize_run(run)
    assert project_family._serialize_run(run) == steward_service._serialize_run(run)
    assert resources._serialize_run(run) == steward_service._serialize_run(run)

    step = {
        "id": "step-1",
        "phase": "read",
        "seq": 1,
        "state": "completed",
        "effect_kind": "project.observe",
        "idempotency_key": "step-key",
        "expected_state_json": '{"state": "pending"}',
        "observed_state_json": '{"state": "completed"}',
        "receipt_json": '{"ok": true}',
        "error_json": "",
    }
    assert steward_route._serialize_step(step) == project_family._serialize_step(step)
    assert resources._serialize_steps([step]) == steward_service._serialize_steps([step])

    policy = {
        "id": "policy-1",
        "project_id": "project-1",
        "eligible_effect_kinds_json": '["project.observe"]',
        "yolo_flags_json": "{}",
        "max_retries": 2,
        "max_actions_per_run": 4,
        "cooldown_seconds": 60,
        "bounds_json": "{}",
        "enabled": 1,
        "unattended_enabled": 0,
        "created_at": "2026-10-19T00:00:00Z",
        "updated_at": "2026-10-19T00:00:00Z",
    }
    assert steward_route._serialize_policy(policy) == project_family._serialize_policy(policy)
    assert steward_contract._serialize_policy(policy) == steward_service._serialize_policy(policy)

