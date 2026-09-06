"""HS-167-07 -- MCP sidecar doc drift guard.

The committed docs/MCP_SIDECAR.md carries a machine-generated roster
fence block listing every MCP tool grouped by name-prefix family.
This guard regenerates the roster from the live registry and fails on
ANY difference from the committed doc: a stale count, a missing family,
an extra tool, or a renamed tool.

Mechanics mirror test_api_surface.py: import the generator, build the
expected output, compare against the committed file.  The one source
of truth is holdspeak.mcp.tools.TOOLS.
"""
from __future__ import annotations

import importlib.util
import re
from pathlib import Path

REPO = Path(__file__).parents[2]
DOC = REPO / "docs" / "MCP_SIDECAR.md"

_spec = importlib.util.spec_from_file_location(
    "gen_mcp_sidecar_doc", REPO / "scripts" / "gen_mcp_sidecar_doc.py"
)
gen = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
_spec.loader.exec_module(gen)  # type: ignore[union-attr]

_FENCE_START = gen._FENCE_START
_FENCE_END = gen._FENCE_END
_FENCE_RE = re.compile(
    re.escape(_FENCE_START) + r"(.*?)" + re.escape(_FENCE_END),
    re.DOTALL,
)


def _extract_fence(text: str) -> str | None:
    m = _FENCE_RE.search(text)
    return m.group(0) if m else None


def test_committed_roster_matches_the_live_registry() -> None:
    """The roster fence in the committed doc must equal the live registry."""
    committed_text = DOC.read_text(encoding="utf-8")
    committed_fence = _extract_fence(committed_text)
    assert committed_fence is not None, (
        "docs/MCP_SIDECAR.md is missing the roster fence block -- "
        "regenerate: uv run python scripts/gen_mcp_sidecar_doc.py"
    )

    tool_names = gen.collect_tools()
    roster = gen.build_roster(tool_names)
    expected_fence = gen.render_roster_block(roster)

    assert committed_fence == expected_fence, (
        "the committed MCP_SIDECAR.md roster drifted from the live "
        "registry -- regenerate: uv run python scripts/gen_mcp_sidecar_doc.py"
    )


def test_header_totals_match_roster() -> None:
    """The header's 'N tools across M families' must match the roster."""
    committed_text = DOC.read_text(encoding="utf-8")
    tool_names = gen.collect_tools()
    roster = gen.build_roster(tool_names)

    m = re.search(r"(\d+)\s+tools\s+across\s+(\d+)\s+families", committed_text)
    assert m is not None, "header totals line not found"
    header_tools = int(m.group(1))
    header_families = int(m.group(2))

    assert header_tools == roster["total_tools"], (
        f"header says {header_tools} tools but registry has "
        f"{roster['total_tools']} -- regenerate: "
        "uv run python scripts/gen_mcp_sidecar_doc.py"
    )
    assert header_families == roster["total_families"], (
        f"header says {header_families} families but registry has "
        f"{roster['total_families']} -- regenerate: "
        "uv run python scripts/gen_mcp_sidecar_doc.py"
    )


def test_palette_count_matches_registry() -> None:
    """The PROJECT_PALETTE size in the doc must match project + provider + connection tools."""
    committed_text = DOC.read_text(encoding="utf-8")
    tool_names = gen.collect_tools()
    roster = gen.build_roster(tool_names)

    project_count = roster["families"].get("project", {}).get("count", 0)
    provider_count = roster["families"].get("provider", {}).get("count", 0)
    connection_count = roster["families"].get("connection", {}).get("count", 0)
    expected_palette = project_count + provider_count + connection_count

    m = re.search(
        r"a frozen set of the (\d+)\s+project\.\*",
        committed_text,
    )
    assert m is not None, "palette count line not found"
    doc_palette = int(m.group(1))
    assert doc_palette == expected_palette, (
        f"palette section says {doc_palette} but registry has "
        f"{expected_palette} (project={project_count} + provider={provider_count} + connection={connection_count}) "
        "-- regenerate: uv run python scripts/gen_mcp_sidecar_doc.py"
    )


def test_roster_is_not_vacuous() -> None:
    """The roster must carry the load-bearing families and tool count."""
    tool_names = gen.collect_tools()
    roster = gen.build_roster(tool_names)
    assert roster["total_tools"] >= 150, "registry went dark"
    assert roster["total_families"] >= 25, "family count collapsed"
    for expected in ("desk", "project", "thought", "people", "cadence"):
        assert expected in roster["families"], f"family {expected} missing"
