"""HS-167-07 -- the MCP sidecar page, written from the live registry.

docs/MCP_SIDECAR.md is generated on demand and is not in git (2026-11-08,
like docs/API_SURFACE.md): ``scripts/gen_mcp_sidecar_doc.py`` fills the
template ``scripts/mcp_sidecar_doc.template.md`` from holdspeak.mcp.tools.TOOLS
and holdspeak.mcp.resources. These tests read no committed copy. They render
the page from the live tree and assert what must hold.
"""
from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import pytest

REPO = Path(__file__).parents[2]

_spec = importlib.util.spec_from_file_location(
    "gen_mcp_sidecar_doc", REPO / "scripts" / "gen_mcp_sidecar_doc.py"
)
gen = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
_spec.loader.exec_module(gen)  # type: ignore[union-attr]


@pytest.fixture(scope="module")
def roster() -> dict:
    return gen.build_roster(gen.collect_tools())


@pytest.fixture(scope="module")
def page(roster: dict) -> str:
    template = gen.TEMPLATE_PATH.read_text(encoding="utf-8")
    return gen.render(template, roster, gen.collect_resource_counts())


def test_every_placeholder_is_filled(page: str) -> None:
    assert not gen._PLACEHOLDER.search(page)


def test_an_unknown_placeholder_fails(roster: dict) -> None:
    with pytest.raises(KeyError):
        gen.render("{{NOT_A_PLACEHOLDER}}", roster, {})


def test_the_roster_names_every_registered_tool(page: str, roster: dict) -> None:
    assert gen.render_roster_block(roster) in page
    listed = set(re.findall(r"^- `([a-z_]+\.[a-z_.]+)`$", page, re.MULTILINE))
    assert listed == {tool for data in roster["families"].values() for tool in data["tools"]}


def test_the_counts_are_the_live_counts(page: str, roster: dict) -> None:
    assert f"{roster['total_tools']} tools across {roster['total_families']} families" in page
    palette = gen.palette_size(roster)
    assert re.search(rf"a frozen set of the {palette}\s+project\.\*", page)
    assert re.search(rf"sees {palette} tools\s+instead of {roster['total_tools']}\.", page)
    counts = gen.collect_resource_counts()
    assert (
        f"Owner discovery exposes {counts['OWNER_STATIC']} static resources and "
        f"{counts['OWNER_TEMPLATES']} resource templates." in page
    )
    assert re.search(
        rf"filters that to {counts['OTHER_STATIC']} static resources and\s+"
        rf"{counts['OTHER_TEMPLATES']} templates, or {counts['OTHER_TOTAL']} total\.",
        page,
    )


