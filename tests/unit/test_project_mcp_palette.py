"""HS-165-04 -- PROJECT_PALETTE: agent-safe by construction.

Tests:
1. Palette constant completeness and boundary.
2. Palette-scoped dispatch isolation (agent cannot reach unrelated tools).
3. Project thread mode wired the house way (thread_modes.py species).
4. MCP-006 widening: every registered family survives a poisoned neighbor.
5. Error-shape sweep: every project-family tool returns structured
   {code, message}-bearing shapes on its failure paths (MCP-004).
"""
from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace, ModuleType
from typing import Any

import pytest

from holdspeak.db.core import Database, reset_database
from holdspeak.mcp import server
from holdspeak.mcp.families import project as project_family
from holdspeak.mcp.families.project import PROJECT_PALETTE, TOOLS as PROJECT_TOOLS
from holdspeak.mcp.tools import (
    TOOLS as ALL_TOOLS,
    ToolError,
    dispatch,
    dispatch_for_palette,
    tools_for_palette,
)
from holdspeak.principals import Principal, PrincipalKind


OWNER = Principal(PrincipalKind.OWNER, "palette-mcp-owner")


@pytest.fixture
def db(tmp_path: Path) -> Database:
    reset_database()
    database = Database(tmp_path / "palette-mcp.db")
    yield database
    reset_database()


@pytest.fixture(autouse=True)
def mcp_project(db: Database, monkeypatch: pytest.MonkeyPatch) -> None:
    """Inject DB + auth into the MCP process boundaries."""
    monkeypatch.setattr(project_family, "get_database", lambda: db)
    monkeypatch.setattr(
        server, "resolve_auth", lambda: SimpleNamespace(principal=OWNER),
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


# ────────────────────────────────────────────────────────────────────
# 1. Palette constant completeness and boundary
# ────────────────────────────────────────────────────────────────────


def test_palette_contains_all_family_tools() -> None:
    """PROJECT_PALETTE == the exact set of tool names in the project family."""
    family_names = frozenset(t["name"] for t in PROJECT_TOOLS)
    assert PROJECT_PALETTE == family_names


def test_palette_is_subset_of_global_tools() -> None:
    """Every palette name exists in the global MCP registry."""
    global_names = frozenset(t["name"] for t in ALL_TOOLS)
    missing = PROJECT_PALETTE - global_names
    assert not missing, f"Palette names not in global registry: {sorted(missing)}"


def test_palette_contains_project_and_provider_only() -> None:
    """The palette holds only project.* and provider.* -- no companions."""
    for name in PROJECT_PALETTE:
        prefix = name.split(".")[0]
        assert prefix in {"project", "provider"}, (
            f"Unexpected tool prefix in palette: {name!r}"
        )


def test_palette_size_is_44() -> None:
    """Pin: the project family has 44 tools (34 project.* + 10 provider.*; HS-166)."""
    assert len(PROJECT_PALETTE) == 44


# ────────────────────────────────────────────────────────────────────
# 2. Palette-scoped dispatch isolation
# ────────────────────────────────────────────────────────────────────


def test_tools_for_palette_returns_only_palette_tools() -> None:
    """tools_for_palette filters the global catalogue to the palette."""
    filtered = tools_for_palette(PROJECT_PALETTE)
    filtered_names = {t["name"] for t in filtered}
    assert filtered_names == PROJECT_PALETTE


def test_tools_for_palette_excludes_non_palette_tools() -> None:
    """tools_for_palette does NOT return tools outside the palette."""
    filtered = tools_for_palette(PROJECT_PALETTE)
    filtered_names = {t["name"] for t in filtered}
    global_names = {t["name"] for t in ALL_TOOLS}
    excluded = global_names - PROJECT_PALETTE
    assert excluded, "There should be tools outside the palette"
    assert not (filtered_names & excluded), (
        f"tools_for_palette leaked: {sorted(filtered_names & excluded)}"
    )


def test_dispatch_for_palette_rejects_non_palette_tool(db: Database) -> None:
    """dispatch_for_palette raises typed ToolError for tools outside the palette."""
    # desk.list is a valid global tool but NOT in PROJECT_PALETTE
    assert "desk.list" not in PROJECT_PALETTE
    with pytest.raises(ToolError, match="not in the configured palette"):
        dispatch_for_palette("desk.list", {"kind": "notes"}, OWNER, PROJECT_PALETTE)


def test_dispatch_for_palette_accepts_palette_tool(db: Database) -> None:
    """dispatch_for_palette passes through to dispatch for palette tools."""
    result = dispatch_for_palette(
        "project.list", {}, OWNER, PROJECT_PALETTE,
    )
    assert "projects" in result


def test_agent_session_isolation_no_unrelated_tools_reachable(db: Database) -> None:
    """Acceptance: an agent session over the palette cannot reach unrelated tools.

    Walk every non-palette tool and prove dispatch_for_palette refuses it.
    """
    global_names = frozenset(t["name"] for t in ALL_TOOLS)
    non_palette = global_names - PROJECT_PALETTE
    assert len(non_palette) > 100, "Sanity: most tools should be outside the palette"

    for name in sorted(non_palette):
        with pytest.raises(ToolError, match="not in the configured palette"):
            dispatch_for_palette(name, {}, OWNER, PROJECT_PALETTE)


# ────────────────────────────────────────────────────────────────────
# 3. Project thread mode wired the house way
# ────────────────────────────────────────────────────────────────────


def test_project_mode_seed_exists() -> None:
    """The Project mode seed follows the house species (thread_modes.py)."""
    from holdspeak.services.thread_modes import MODE_SEEDS

    project_modes = [m for m in MODE_SEEDS if m.id == "hs-seed-mode-project"]
    assert len(project_modes) == 1, "Exactly one Project mode seed expected"
    mode = project_modes[0]
    assert mode.name == "Project"
    assert mode.avatar  # Non-empty color
    assert mode.system_prompt  # Non-empty prompt


def test_project_mode_is_a_mode_dataclass() -> None:
    """The Project mode is the same Mode dataclass as Desk/Chase/Draft/Plan."""
    from holdspeak.services.thread_modes import MODE_SEEDS, Mode

    project_mode = next(m for m in MODE_SEEDS if m.id == "hs-seed-mode-project")
    assert isinstance(project_mode, Mode)
    # Frozen dataclass
    with pytest.raises(AttributeError):
        project_mode.name = "Hacked"  # type: ignore[misc]


def test_project_mode_tools_are_empty_or_forward() -> None:
    """Project mode has no thread-side tools (MCP-only); tools are empty."""
    from holdspeak.services.thread_modes import MODE_SEEDS

    project_mode = next(m for m in MODE_SEEDS if m.id == "hs-seed-mode-project")
    # Currently empty -- project.* tools are MCP-only
    assert project_mode.tools == frozenset()


def test_project_mode_can_be_seeded(db: Database) -> None:
    """seed_modes creates the Project mode recipe when absent."""
    from holdspeak.services.thread_modes import seed_modes

    created = seed_modes(db)
    assert created >= 1  # At least the new Project mode

    # Verify it landed
    recipe = db.recipes.get("hs-seed-mode-project")
    assert recipe is not None
    assert recipe.kind == "mode"
    assert recipe.name == "Project"


def test_no_second_mode_mechanism() -> None:
    """The Project mode uses the same Mode dataclass and MODE_SEEDS tuple
    as the existing Desk/Chase/Draft/Plan modes -- no second species."""
    from holdspeak.services.thread_modes import MODE_SEEDS, Mode

    assert isinstance(MODE_SEEDS, tuple)
    for mode in MODE_SEEDS:
        assert isinstance(mode, Mode), f"{mode.id} is not a Mode instance"
    # Project is in the tuple, not in a separate registry
    ids = {m.id for m in MODE_SEEDS}
    assert "hs-seed-mode-project" in ids


# ────────────────────────────────────────────────────────────────────
# 4. MCP-006 widening: every family survives a poisoned neighbor
# ────────────────────────────────────────────────────────────────────


def test_mcp006_all_families_survive_poisoned_neighbor() -> None:
    """MCP-006 widened: for every registered family, a poisoned neighbor
    cannot suppress it.

    Strategy: inject ONE poisoned family into the name list, re-run the
    assembly, and verify every healthy family still loads.  This proves
    the registry pattern (individual guards) works for the WHOLE list.
    """
    import holdspeak.mcp.families as families_mod

    original_names = families_mod._FAMILY_MODULE_NAMES[:]
    original_families = families_mod.FAMILIES[:]
    original_degraded = dict(families_mod.DEGRADED_FAMILIES)

    # Create a poisoned module
    poison_name = "_poison_mcp006_widened"
    fq_poison = f"holdspeak.mcp.families.{poison_name}"
    sys.modules.pop(fq_poison, None)

    poison_path = Path(project_family.__file__).parent / f"{poison_name}.py"
    poison_path.write_text(
        "raise RuntimeError('MCP-006 widened deliberate poison')\n",
        encoding="utf-8",
    )

    try:
        # Inject poison and re-run assembly
        families_mod._FAMILY_MODULE_NAMES.append(poison_name)
        families_mod.FAMILIES.clear()
        families_mod.DEGRADED_FAMILIES.clear()

        for name in families_mod._FAMILY_MODULE_NAMES:
            try:
                mod = importlib.import_module(f"holdspeak.mcp.families.{name}")
                families_mod.FAMILIES.append(mod)
            except Exception as exc:
                families_mod.DEGRADED_FAMILIES[name] = str(exc)

        # Poison is degraded
        assert poison_name in families_mod.DEGRADED_FAMILIES

        # EVERY original family survived
        loaded_names = {
            f.__name__.rsplit(".", 1)[-1] for f in families_mod.FAMILIES
        }
        for orig_name in original_names:
            assert orig_name in loaded_names, (
                f"Family {orig_name!r} was suppressed by the poisoned neighbor"
            )

    finally:
        # Restore
        families_mod._FAMILY_MODULE_NAMES[:] = original_names
        families_mod.FAMILIES[:] = original_families
        families_mod.DEGRADED_FAMILIES.clear()
        families_mod.DEGRADED_FAMILIES.update(original_degraded)
        poison_path.unlink(missing_ok=True)
        sys.modules.pop(fq_poison, None)


def test_mcp006_project_tools_survive_arbitrary_poisoned_neighbor(
    db: Database,
) -> None:
    """MCP-006: project tools survive AND dispatch correctly when an
    arbitrary other family is poisoned."""
    import holdspeak.mcp.families as families_mod

    original_names = families_mod._FAMILY_MODULE_NAMES[:]
    original_families = families_mod.FAMILIES[:]
    original_degraded = dict(families_mod.DEGRADED_FAMILIES)

    poison_name = "_poison_mcp006_project"
    fq_poison = f"holdspeak.mcp.families.{poison_name}"
    sys.modules.pop(fq_poison, None)

    poison_path = Path(project_family.__file__).parent / f"{poison_name}.py"
    poison_path.write_text(
        "raise RuntimeError('MCP-006 project dispatch test')\n",
        encoding="utf-8",
    )

    try:
        families_mod._FAMILY_MODULE_NAMES.append(poison_name)
        families_mod.FAMILIES.clear()
        families_mod.DEGRADED_FAMILIES.clear()

        for name in families_mod._FAMILY_MODULE_NAMES:
            try:
                mod = importlib.import_module(f"holdspeak.mcp.families.{name}")
                families_mod.FAMILIES.append(mod)
            except Exception as exc:
                families_mod.DEGRADED_FAMILIES[name] = str(exc)

        # Project family dispatch works
        result = project_family.dispatch("project.list", {}, OWNER)
        assert "projects" in result

    finally:
        families_mod._FAMILY_MODULE_NAMES[:] = original_names
        families_mod.FAMILIES[:] = original_families
        families_mod.DEGRADED_FAMILIES.clear()
        families_mod.DEGRADED_FAMILIES.update(original_degraded)
        poison_path.unlink(missing_ok=True)
        sys.modules.pop(fq_poison, None)


# ────────────────────────────────────────────────────────────────────
# 5. Error-shape sweep: MCP-004 proven for every project-family tool
# ────────────────────────────────────────────────────────────────────

# Build a minimally-invalid argument set per tool from its schema:
# for each required property, omit it or supply an invalid value.
# This forces the first error path (usually _require_id or schema
# validation) and we verify the structured shape.

def _tool_names() -> list[str]:
    """All tool names in the project family."""
    return [t["name"] for t in PROJECT_TOOLS]


@pytest.mark.parametrize("tool_name", _tool_names(), ids=_tool_names())
def test_error_shape_sweep(db: Database, tool_name: str) -> None:
    """MCP-004: every project-family tool returns a structured error
    (with a 'code' or 'error' key) when called with empty arguments.

    The MCP server wraps all tool errors as isError=True with a JSON
    body.  This test drives each tool with {} and asserts the error
    response has the structured shape.
    """
    is_error, data = _call(tool_name, {})

    # Most tools require at least one argument (project_id, watch_id,
    # etc.), so they should error.  For tools that legitimately
    # succeed with empty arguments (project.list, provider.list),
    # they return a successful structured result.
    if is_error:
        # MCP-004: structured error shape -- must have at least 'error'
        assert "error" in data, (
            f"{tool_name}: error response missing 'error' key: {data}"
        )
        # Verify the error is a string (not None or a dict)
        assert isinstance(data["error"], str), (
            f"{tool_name}: error value is not a string: {type(data['error'])}"
        )
        # For ServiceError paths, we also get 'code'
        # (ToolError paths may not have 'code' -- e.g. schema validation)
        # Both shapes are acceptable structured responses per MCP-004.
    else:
        # Tool succeeded with empty args -- verify it returned structured data
        assert isinstance(data, dict), (
            f"{tool_name}: success response is not structured: {type(data)}"
        )


# A focused subset: tools that require project_id MUST return typed
# (code-bearing) errors, not just a prose error string.

_TOOLS_REQUIRING_PROJECT_ID = [
    t["name"] for t in PROJECT_TOOLS
    if "project_id" in (t.get("inputSchema", {}).get("required") or [])
]


@pytest.mark.parametrize(
    "tool_name",
    _TOOLS_REQUIRING_PROJECT_ID,
    ids=_TOOLS_REQUIRING_PROJECT_ID,
)
def test_error_shape_typed_code_on_missing_project_id(
    db: Database, tool_name: str,
) -> None:
    """Tools with required project_id return a coded error, not just prose."""
    is_error, data = _call(tool_name, {})
    assert is_error is True, f"{tool_name} should error with empty args"
    assert "error" in data
    assert "code" in data, (
        f"{tool_name}: missing 'code' in error response: {data}"
    )


# Tools that have no required args should succeed cleanly with {}.

_TOOLS_NO_REQUIRED_ARGS = [
    t["name"] for t in PROJECT_TOOLS
    if not (t.get("inputSchema", {}).get("required") or [])
]


# Tools with no required args that always succeed with {} (no external deps).
_TOOLS_NO_REQUIRED_ARGS_PURE = [
    name for name in _TOOLS_NO_REQUIRED_ARGS
    if not name.startswith("provider.github")
]

# Provider tools with no required args that may error on missing config.
_TOOLS_NO_REQUIRED_ARGS_PROVIDER = [
    name for name in _TOOLS_NO_REQUIRED_ARGS
    if name.startswith("provider.github")
]


@pytest.mark.parametrize(
    "tool_name",
    _TOOLS_NO_REQUIRED_ARGS_PURE,
    ids=_TOOLS_NO_REQUIRED_ARGS_PURE,
)
def test_no_required_args_tools_succeed_with_empty(
    db: Database, tool_name: str,
) -> None:
    """Tools with no required args (and no external deps) succeed with {}."""
    is_error, data = _call(tool_name, {})
    assert is_error is False, (
        f"{tool_name} should succeed with empty args: {data}"
    )
    assert isinstance(data, dict)


@pytest.mark.parametrize(
    "tool_name",
    _TOOLS_NO_REQUIRED_ARGS_PROVIDER,
    ids=_TOOLS_NO_REQUIRED_ARGS_PROVIDER,
)
def test_provider_tools_return_structured_error_when_unconfigured(
    db: Database, tool_name: str,
) -> None:
    """Provider tools with no required args return structured errors
    when the provider is not configured (MCP-004)."""
    is_error, data = _call(tool_name, {})
    # These tools fail because GitHub is not configured in the test env
    assert is_error is True
    assert "code" in data, f"{tool_name}: missing 'code' in error: {data}"
    assert data["code"] == "provider_not_configured"
