#!/usr/bin/env python3
"""Write docs/MCP_SIDECAR.md from its template and the live MCP registry.

The page is generated on demand and is not in git (2026-11-08, like
docs/API_SURFACE.md). The hand-written text is in
``scripts/mcp_sidecar_doc.template.md``; the generator fills its
placeholders from the live server:

- ``{{TOOLS}}``: the number of tools in ``holdspeak.mcp.tools.TOOLS``.
- ``{{PALETTE}}``: the project.*, provider.* and connection.* tools.
- ``{{ROSTER}}``: every tool, grouped by name-prefix family.
- ``{{OWNER_STATIC}}``, ``{{OWNER_TEMPLATES}}``, ``{{OTHER_STATIC}}``,
  ``{{OTHER_TEMPLATES}}``, ``{{OTHER_TOTAL}}``: the resource discovery counts
  for the owner and for the default non-owner principal.

Write it:

    uv run python scripts/gen_mcp_sidecar_doc.py

(``scripts/gen_docs.sh`` runs it with every other generator.)
"""
from __future__ import annotations

import re
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DOC_PATH = REPO / "docs" / "MCP_SIDECAR.md"
TEMPLATE_PATH = Path(__file__).resolve().parent / "mcp_sidecar_doc.template.md"


def _with_scratch_database(read):
    """Run ``read`` against a disposable database, never the owner's."""
    from holdspeak.db import get_database, reset_database

    reset_database()
    with tempfile.TemporaryDirectory(prefix="holdspeak-mcp-sidecar-") as tmp:
        get_database(Path(tmp) / "mcp-sidecar-gen.db")
        try:
            return read()
        finally:
            reset_database()


def collect_tools() -> list[str]:
    """Return the sorted list of all MCP tool names from the registry."""
    def read() -> list[str]:
        from holdspeak.mcp.tools import TOOLS

        return sorted(t["name"] for t in TOOLS)

    return _with_scratch_database(read)


def collect_resource_counts() -> dict[str, int]:
    """Static and template resource counts, for the owner and the default non-owner."""
    def read() -> dict[str, int]:
        from holdspeak.mcp import resources
        from holdspeak.principals import Principal, PrincipalKind

        owner = resources.list_resources(Principal(PrincipalKind.OWNER, "mcp-sidecar-doc"))
        other = resources.list_resources(None)
        return {
            "OWNER_STATIC": len(owner["resources"]),
            "OWNER_TEMPLATES": len(owner["resourceTemplates"]),
            "OTHER_STATIC": len(other["resources"]),
            "OTHER_TEMPLATES": len(other["resourceTemplates"]),
            "OTHER_TOTAL": len(other["resources"]) + len(other["resourceTemplates"]),
        }

    return _with_scratch_database(read)


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
# The roster block that fills ``{{ROSTER}}`` in the template.

_FENCE_START = "<!-- BEGIN MCP TOOL ROSTER (machine-generated -- do not edit) -->"
_FENCE_END = "<!-- END MCP TOOL ROSTER -->"

_PLACEHOLDER = re.compile(r"\{\{([A-Z_]+)\}\}")


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


def palette_size(roster: dict) -> int:
    """The PROJECT_PALETTE size: project.*, provider.* and connection.* tools."""
    return sum(
        roster["families"].get(family, {}).get("count", 0)
        for family in ("project", "provider", "connection")
    )


def render(template: str, roster: dict, resource_counts: dict[str, int]) -> str:
    """The template with every placeholder filled. An unknown placeholder fails."""
    values = {
        "TOOLS": str(roster["total_tools"]),
        "PALETTE": str(palette_size(roster)),
        "ROSTER": render_roster_block(roster),
        **{key: str(value) for key, value in resource_counts.items()},
    }

    def fill(match: re.Match) -> str:
        key = match.group(1)
        if key not in values:
            raise KeyError(f"{TEMPLATE_PATH.name}: unknown placeholder {{{{{key}}}}}")
        return values[key]

    return _PLACEHOLDER.sub(fill, template)


def regenerate() -> str:
    """The whole docs/MCP_SIDECAR.md text, from the template and the live server."""
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    return render(template, build_roster(collect_tools()), collect_resource_counts())


def main() -> int:
    result = regenerate()
    DOC_PATH.write_text(result, encoding="utf-8")
    roster = build_roster(collect_tools())
    print(f"wrote {DOC_PATH.relative_to(REPO)}")
    print(f"  {roster['total_tools']} tools across {roster['total_families']} families")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
