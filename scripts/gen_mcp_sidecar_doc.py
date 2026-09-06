#!/usr/bin/env python3
"""Generate docs/MCP_SIDECAR.md from the MCP tool registry.

The MCP sidecar doc's header totals and per-family tool roster are
derived from the ONE source of truth: the assembled TOOLS list in
holdspeak.mcp.tools (which aggregates tools.py + every family module).

The generator updates three machine-verifiable parts of the doc:
1. The header paragraph's "N tools across M families" count.
2. The PROJECT_PALETTE section's tool count.
3. A fenced roster block listing every tool grouped by name-prefix
   family -- the drift guard checks this block against the registry.

Narrative sections (per-family descriptions, trust model, etc.) are
hand-written and not touched by the generator.

Regenerate after any tool change:

    uv run python scripts/gen_mcp_sidecar_doc.py

The snapshot guard (tests/unit/test_mcp_sidecar_doc_drift.py) fails when
the committed doc drifts from the live registry.
"""
from __future__ import annotations

import re
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DOC_PATH = REPO / "docs" / "MCP_SIDECAR.md"


def collect_tools() -> list[str]:
    """Return the sorted list of all MCP tool names from the registry."""
    from holdspeak.db import get_database, reset_database

    reset_database()
    with tempfile.TemporaryDirectory(prefix="holdspeak-mcp-sidecar-") as tmp:
        get_database(Path(tmp) / "mcp-sidecar-gen.db")
        try:
            from holdspeak.mcp.tools import TOOLS
            names = sorted(t["name"] for t in TOOLS)
        finally:
            reset_database()
    return names


def group_by_family(tool_names: list[str]) -> dict[str, list[str]]:
    """Group tool names by their first-dot prefix (the doc 'family')."""
    families: dict[str, list[str]] = {}
    for name in tool_names:
        prefix = name.split(".")[0]
        families.setdefault(prefix, []).append(name)
    return dict(sorted(families.items()))


def build_roster(tool_names: list[str]) -> dict:
    """Build the machine-verifiable roster: totals + per-family tool lists."""
    families = group_by_family(tool_names)
    return {
        "total_tools": len(tool_names),
        "total_families": len(families),
        "families": {
            name: {"count": len(tools), "tools": tools}
            for name, tools in families.items()
        },
    }


# ── The roster fence ──────────────────────────────────────────────────
# The fence is a machine-generated block inside the doc that the drift
# guard can compare against.  Everything outside it is hand-written
# narrative and is NOT checked by the guard (so it can be edited freely).

_FENCE_START = "<!-- BEGIN MCP TOOL ROSTER (machine-generated -- do not edit) -->"
_FENCE_END = "<!-- END MCP TOOL ROSTER -->"

# The header line pattern: "N tools across M families"
_HEADER_RE = re.compile(r"(\d+)\s+tools\s+across\s+(\d+)\s+families")


def render_roster_block(roster: dict) -> str:
    """Render the machine-verifiable roster fence block."""
    lines = [_FENCE_START, ""]
    lines.append(
        f"**Registry totals:** {roster['total_tools']} tools across "
        f"{roster['total_families']} families."
    )
    lines.append("")
    for family_name, data in sorted(roster["families"].items()):
        lines.append(f"#### {family_name} ({data['count']})")
        lines.append("")
        for tool in data["tools"]:
            lines.append(f"- `{tool}`")
        lines.append("")
    lines.append(_FENCE_END)
    return "\n".join(lines)


def update_header_totals(text: str, roster: dict) -> str:
    """Update the header paragraph's tool/family counts."""
    total = roster["total_tools"]
    families = roster["total_families"]

    def _replace(m: re.Match) -> str:
        return f"{total} tools across {families} families"

    return _HEADER_RE.sub(_replace, text, count=1)


def update_palette_count(text: str, roster: dict) -> str:
    """Update the PROJECT_PALETTE frozen-set size in the palette section."""
    project_count = roster["families"].get("project", {}).get("count", 0)
    provider_count = roster["families"].get("provider", {}).get("count", 0)
    connection_count = roster["families"].get("connection", {}).get("count", 0)
    palette_size = project_count + provider_count + connection_count
    # The "frozen set of the NN\nproject.*" may wrap across lines.
    # HS-168-02: connection.* tools are also in the palette.
    text = re.sub(
        r"a frozen set of the \d+\s+project\.\*[^\n]*tool\s*names",
        f"a frozen set of the {palette_size}\nproject.*, provider.* and connection.* tool names",
        text,
        count=1,
    )
    text = re.sub(
        r"sees \d+ tools\s+instead of \d+",
        f"sees {palette_size} tools\ninstead of {roster['total_tools']}",
        text,
        count=1,
    )
    return text


def regenerate(doc_text: str | None = None) -> str:
    """Regenerate MCP_SIDECAR.md from the registry.

    If doc_text is None, reads the committed file.
    Returns the updated doc text.
    """
    if doc_text is None:
        doc_text = DOC_PATH.read_text(encoding="utf-8")

    tool_names = collect_tools()
    roster = build_roster(tool_names)

    # 1. Update header totals
    result = update_header_totals(doc_text, roster)

    # 2. Update palette count
    result = update_palette_count(result, roster)

    # 3. Insert or replace the roster fence block
    if _FENCE_START in result:
        pattern = re.compile(
            re.escape(_FENCE_START) + r".*?" + re.escape(_FENCE_END),
            re.DOTALL,
        )
        result = pattern.sub(render_roster_block(roster), result)
    else:
        # Insert before "## Model-invoking tools"
        insert_before = "## Model-invoking tools"
        if insert_before in result:
            result = result.replace(
                insert_before,
                render_roster_block(roster) + "\n\n" + insert_before,
            )
        else:
            result += "\n\n" + render_roster_block(roster) + "\n"

    return result


def main() -> int:
    result = regenerate()
    DOC_PATH.write_text(result, encoding="utf-8")
    print(f"wrote {DOC_PATH.relative_to(REPO)}")

    tool_names = collect_tools()
    roster = build_roster(tool_names)
    print(f"  {roster['total_tools']} tools across {roster['total_families']} families")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
