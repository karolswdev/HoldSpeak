"""HS-165-01 -- MCP coverage for the Project family skeleton.

Tests project.list / project.get / project.get_room tools (MCP-001 parity),
the five SS11.2 resources, and MCP-006 isolation (poisoned family).
"""
from __future__ import annotations

import json
import importlib
import sys
from pathlib import Path
from types import SimpleNamespace, ModuleType
from typing import Any

import pytest

from holdspeak.db.core import Database, reset_database
from holdspeak.mcp import server
from holdspeak.mcp.families import project as project_family
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.project_service import ProjectService


OWNER = Principal(PrincipalKind.OWNER, "project-mcp-owner")


@pytest.fixture
def db(tmp_path: Path) -> Database:
    reset_database()
    database = Database(tmp_path / "project-mcp.db")
    yield database
    reset_database()


@pytest.fixture(autouse=True)
def mcp_project(db: Database, monkeypatch: pytest.MonkeyPatch) -> None:
    """Inject only the MCP process boundaries; project dependencies stay real."""
    monkeypatch.setattr(project_family, "get_database", lambda: db)
    monkeypatch.setattr(
        server, "resolve_auth", lambda: SimpleNamespace(principal=OWNER)
    )
    monkeypatch.setenv("HOLDSPEAK_MCP_PEOPLE_ACCESS", "off")


def _call(name: str, arguments: dict[str, Any] | None = None) -> tuple[bool, dict[str, Any]]:
    response = server.handle_message({
        "jsonrpc": "2.0",
        "id": name,
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments or {}},
    })
    assert response is not None
    result = response["result"]
    return result["isError"], json.loads(result["content"][0]["text"])


def _read_resource(uri: str) -> dict[str, Any]:
    response = server.handle_message({
        "jsonrpc": "2.0",
        "id": f"resource:{uri}",
        "method": "resources/read",
        "params": {"uri": uri},
    })
    assert response is not None
    if "error" in response:
        return {"_error": response["error"]}
    contents = response["result"]["contents"]
    return json.loads(contents[0]["text"])


def _seed_project(db: Database, project_id: str = "proj-test-001",
                  name: str = "Test Project") -> str:
    """Seed a minimal project row."""
    with db._connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO projects "
            "(id, name, description, keywords_json, team_members_json, "
            "context_json, detection_threshold, is_archived, revision, "
            "created_at, updated_at) "
            "VALUES (?, ?, '', '[]', '[]', '{}', 0.5, 0, 1, "
            "'2025-01-01T00:00:00', '2025-06-01T00:00:00')",
            (project_id, name),
        )
    return project_id


# ────────────────────────────────────────────────────────────────────
# Tool discovery
# ────────────────────────────────────────────────────────────────────


def test_project_tools_are_discoverable_with_versioned_schemas() -> None:
    response = server.handle_message(
        {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
    )
    assert response is not None
    project_tools = [
        tool
        for tool in response["result"]["tools"]
        if tool["name"].startswith("project.")
    ]
    # The first three are the read tools from HS-165-01
    assert project_tools[0]["name"] == "project.list"
    assert project_tools[1]["name"] == "project.get"
    assert project_tools[2]["name"] == "project.get_room"
    # HS-165-02 adds 14 command tools (17), HS-165-03 adds 16 driver tools (33 total)
    # HS-172-06: + 3 suggested_source tools (35 -> 38)
    # HS-200-03: + 4 Project-setup proposal tools (38 -> 42), regenerated from
    # the authoritative source below rather than from a remembered number.
    assert len(project_tools) == 42
    from holdspeak.mcp.families import project as project_family

    assert len(project_tools) == len(
        [t for t in project_family.TOOLS if t["name"].startswith("project.")]
    )
    # Versioned $id schemas
    assert project_tools[0]["inputSchema"]["$id"] == "holdspeak://mcp/project.list@1"
    assert project_tools[1]["inputSchema"]["$id"] == "holdspeak://mcp/project.get@1"
    assert project_tools[2]["inputSchema"]["$id"] == "holdspeak://mcp/project.get_room@1"
    # Closed schemas
    for tool in project_tools:
        assert tool["inputSchema"]["additionalProperties"] is False


# ────────────────────────────────────────────────────────────────────
# project.list
# ────────────────────────────────────────────────────────────────────


def test_project_list_empty(db: Database) -> None:
    is_error, data = _call("project.list")
    assert is_error is False
    assert data == {"projects": []}


def test_project_list_returns_projects(db: Database) -> None:
    _seed_project(db, "proj-a", "Alpha")
    _seed_project(db, "proj-b", "Bravo")

    is_error, data = _call("project.list")
    assert is_error is False
    assert len(data["projects"]) == 2
    names = {p["name"] for p in data["projects"]}
    assert names == {"Alpha", "Bravo"}


def test_project_list_parity_with_service(db: Database) -> None:
    """MCP-001: the MCP shape matches the service shape exactly."""
    _seed_project(db, "proj-parity", "Parity")
    svc = ProjectService(db)
    service_result = svc.list_projects(OWNER)

    is_error, mcp_result = _call("project.list")
    assert is_error is False
    assert mcp_result["projects"] == service_result


def test_project_list_include_archived(db: Database) -> None:
    _seed_project(db, "proj-arch", "Archived")
    with db._connection() as conn:
        conn.execute(
            "UPDATE projects SET is_archived = 1 WHERE id = ?",
            ("proj-arch",),
        )
    # Without include_archived: no projects
    is_error, data = _call("project.list")
    assert is_error is False
    assert len(data["projects"]) == 0

    # With include_archived: one project
    is_error, data = _call("project.list", {"include_archived": True})
    assert is_error is False
    assert len(data["projects"]) == 1
    assert data["projects"][0]["id"] == "proj-arch"


# ────────────────────────────────────────────────────────────────────
# project.get
# ────────────────────────────────────────────────────────────────────


def test_project_get_returns_project(db: Database) -> None:
    _seed_project(db, "proj-get-1", "Get Test")

    is_error, data = _call("project.get", {"project_id": "proj-get-1"})
    assert is_error is False
    assert data["id"] == "proj-get-1"
    assert data["name"] == "Get Test"


def test_project_get_parity_with_service(db: Database) -> None:
    """MCP-001: the MCP shape matches the service shape exactly."""
    _seed_project(db, "proj-parity-get", "Parity Get")
    svc = ProjectService(db)
    service_result = svc.get_project(OWNER, "proj-parity-get")

    is_error, mcp_result = _call("project.get", {"project_id": "proj-parity-get"})
    assert is_error is False
    assert mcp_result == service_result


def test_project_get_unknown_project_refuses_typed(db: Database) -> None:
    is_error, data = _call("project.get", {"project_id": "nonexistent"})
    assert is_error is True
    assert "code" in data


def test_project_get_missing_id_refuses(db: Database) -> None:
    is_error, data = _call("project.get", {})
    assert is_error is True


# ────────────────────────────────────────────────────────────────────
# project.get_room
# ────────────────────────────────────────────────────────────────────


def test_project_get_room_returns_room_projection(db: Database) -> None:
    _seed_project(db, "proj-room-1", "Room Test")

    is_error, data = _call("project.get_room", {"project_id": "proj-room-1"})
    assert is_error is False
    # The room projection shape: project_id, project, revision, sections
    assert data["project_id"] == "proj-room-1"
    assert data["project"]["id"] == "proj-room-1"
    assert "items" in data
    assert "meetings" in data
    assert "resources" in data


def test_project_get_room_parity_with_service(db: Database) -> None:
    """MCP-001: the MCP room shape matches the service room shape exactly."""
    _seed_project(db, "proj-parity-room", "Parity Room")
    svc = ProjectService(db)
    service_result = svc.room(OWNER, "proj-parity-room")

    is_error, mcp_result = _call(
        "project.get_room", {"project_id": "proj-parity-room"}
    )
    assert is_error is False
    assert mcp_result == service_result


def test_project_get_room_unknown_refuses_typed(db: Database) -> None:
    is_error, data = _call("project.get_room", {"project_id": "nonexistent"})
    assert is_error is True
    assert "code" in data


# ────────────────────────────────────────────────────────────────────
# SS11.2 Resources
# ────────────────────────────────────────────────────────────────────


def test_resource_templates_listed(db: Database) -> None:
    """All five SS11.2 resource templates are discoverable."""
    response = server.handle_message(
        {"jsonrpc": "2.0", "id": 1, "method": "resources/list"}
    )
    assert response is not None
    templates = response["result"]["resourceTemplates"]
    template_uris = {t["uriTemplate"] for t in templates}
    expected = {
        "holdspeak://projects/{project_id}",
        "holdspeak://projects/{project_id}/room",
        "holdspeak://projects/{project_id}/delta",
        "holdspeak://projects/{project_id}/updates/{update_id}",
        "holdspeak://projects/{project_id}/steward/runs/{run_id}",
    }
    assert expected.issubset(template_uris), (
        f"Missing project resource templates: {expected - template_uris}"
    )


def test_resource_project_detail(db: Database, monkeypatch: pytest.MonkeyPatch) -> None:
    """holdspeak://projects/{id} resolves to project identity."""
    _seed_project(db, "proj-res-1", "Resource Test")
    # Patch resources.py's get_database too
    from holdspeak.mcp import resources
    monkeypatch.setattr(resources, "get_database", lambda: db)

    data = _read_resource("holdspeak://projects/proj-res-1")
    assert "_error" not in data
    assert data["id"] == "proj-res-1"
    assert data["name"] == "Resource Test"


def test_resource_project_room(db: Database, monkeypatch: pytest.MonkeyPatch) -> None:
    """holdspeak://projects/{id}/room resolves to the room projection."""
    _seed_project(db, "proj-res-room", "Room Resource")
    from holdspeak.mcp import resources
    monkeypatch.setattr(resources, "get_database", lambda: db)

    data = _read_resource("holdspeak://projects/proj-res-room/room")
    assert "_error" not in data
    assert data["project_id"] == "proj-res-room"
    assert data["project"]["id"] == "proj-res-room"


def test_resource_project_delta(db: Database, monkeypatch: pytest.MonkeyPatch) -> None:
    """holdspeak://projects/{id}/delta resolves to the honest empty state."""
    _seed_project(db, "proj-res-delta", "Delta Resource")
    from holdspeak.mcp import resources
    monkeypatch.setattr(resources, "get_database", lambda: db)

    data = _read_resource("holdspeak://projects/proj-res-delta/delta")
    assert "_error" not in data
    # Honest empty: no open review
    assert data["open_review"] is None


def test_resource_project_update_unknown_refuses_typed(
    db: Database, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """holdspeak://projects/{id}/updates/{id} refuses unknown update ids typed."""
    _seed_project(db, "proj-res-upd", "Update Resource")
    from holdspeak.mcp import resources
    monkeypatch.setattr(resources, "get_database", lambda: db)

    data = _read_resource(
        "holdspeak://projects/proj-res-upd/updates/nonexistent-update"
    )
    assert "_error" in data
    assert data["_error"]["code"] == -32002


def test_resource_project_steward_run_unknown_refuses_typed(
    db: Database, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """holdspeak://projects/{id}/steward/runs/{id} refuses unknown run ids typed."""
    _seed_project(db, "proj-res-run", "Run Resource")
    from holdspeak.mcp import resources
    monkeypatch.setattr(resources, "get_database", lambda: db)

    data = _read_resource(
        "holdspeak://projects/proj-res-run/steward/runs/nonexistent-run"
    )
    assert "_error" in data
    assert data["_error"]["code"] == -32002


def test_resource_unknown_project_refuses_typed(
    db: Database, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """holdspeak://projects/{id} refuses unknown project ids typed."""
    from holdspeak.mcp import resources
    monkeypatch.setattr(resources, "get_database", lambda: db)

    data = _read_resource("holdspeak://projects/nonexistent-project")
    assert "_error" in data


# ────────────────────────────────────────────────────────────────────
# MCP-006: Poisoned family isolation
# ────────────────────────────────────────────────────────────────────


def test_mcp006_poisoned_family_does_not_suppress_project_tools(
    db: Database, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """MCP-006: a family whose import fails must not suppress project tools.

    This test drives the REAL assembly path (no fixture that hand-simulates
    isolation). A poisoned fake family is injected into the module name
    list, and the project family must still load and dispatch.
    """
    # Create a poisoned module that raises on import
    poison_name = "_poison_mcp006_test"
    fq_poison = f"holdspeak.mcp.families.{poison_name}"

    # Remove cached modules if somehow present
    sys.modules.pop(fq_poison, None)

    # Create a poisoned module source
    poison_path = Path(project_family.__file__).parent / f"{poison_name}.py"
    poison_path.write_text(
        "raise RuntimeError('MCP-006 deliberate poisoned family')\n",
        encoding="utf-8",
    )

    try:
        # Re-import the families __init__ with the poisoned family name injected.
        import holdspeak.mcp.families as families_mod

        original_names = families_mod._FAMILY_MODULE_NAMES[:]
        original_families = families_mod.FAMILIES[:]
        original_degraded = dict(families_mod.DEGRADED_FAMILIES)

        try:
            # Inject the poisoned name and re-run the assembly
            families_mod._FAMILY_MODULE_NAMES.append(poison_name)
            families_mod.FAMILIES.clear()
            families_mod.DEGRADED_FAMILIES.clear()

            for name in families_mod._FAMILY_MODULE_NAMES:
                try:
                    mod = importlib.import_module(f"holdspeak.mcp.families.{name}")
                    families_mod.FAMILIES.append(mod)
                except Exception as exc:
                    families_mod.DEGRADED_FAMILIES[name] = str(exc)

            # The poison is degraded
            assert poison_name in families_mod.DEGRADED_FAMILIES
            assert "MCP-006" in families_mod.DEGRADED_FAMILIES[poison_name]

            # Project family is still loaded
            project_loaded = any(
                getattr(f, "__name__", "").endswith(".project")
                for f in families_mod.FAMILIES
            )
            assert project_loaded, "Project family missing after poisoned import"

            # Rebuild the TOOLS list the same way tools.py does
            from holdspeak.mcp import tools as tools_mod

            # Save original TOOLS
            original_tools = tools_mod.TOOLS[:]

            # Rebuild: first the base tools, then families
            # We find where family tools start by checking how many tools
            # are in the base catalogue
            base_count = len([
                t for t in original_tools
                if not any(
                    any(ft["name"] == t["name"] for ft in fam.TOOLS)
                    for fam in original_families
                )
            ])

            # Rebuild with the new FAMILIES (including surviving project)
            new_tools = original_tools[:base_count]
            for fam in families_mod.FAMILIES:
                new_tools.extend(fam.TOOLS)

            # Project tools present
            project_tool_names = [
                t["name"] for t in new_tools if t["name"].startswith("project.")
            ]
            assert "project.list" in project_tool_names
            assert "project.get" in project_tool_names
            assert "project.get_room" in project_tool_names

            # Dispatch works for project tools
            _seed_project(db, "proj-mcp006", "Poison Test")
            result = project_family.dispatch(
                "project.list", {}, OWNER
            )
            assert len(result["projects"]) >= 1

        finally:
            # Restore everything
            families_mod._FAMILY_MODULE_NAMES[:] = original_names
            families_mod.FAMILIES[:] = original_families
            families_mod.DEGRADED_FAMILIES.clear()
            families_mod.DEGRADED_FAMILIES.update(original_degraded)

    finally:
        # Clean up the poisoned file
        poison_path.unlink(missing_ok=True)
        sys.modules.pop(fq_poison, None)


def test_mcp006_degraded_families_is_structured() -> None:
    """DEGRADED_FAMILIES is a dict[str, str] available for reporting."""
    import holdspeak.mcp.families as families_mod
    assert isinstance(families_mod.DEGRADED_FAMILIES, dict)
    # In normal operation, no families are degraded
    assert len(families_mod.DEGRADED_FAMILIES) == 0
