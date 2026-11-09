"""Parked 2026-11-08: docs/MCP_SIDECAR.md is generated on demand.

scripts/gen_mcp_sidecar_doc.py now fills the resource counts in that page from
holdspeak.mcp.resources.list_resources, so a claim that reads them back is
always true. The claim row and its predicates, verbatim from
tests/unit/doc_claims/registry.py. Kept, not collected.
"""
# ruff: noqa

PARKED_CLAIMS = """
    Claim(
        doc="docs/MCP_SIDECAR.md",
        anchor="Owner discovery exposes 16 static resources and 21 resource templates.",
        sentence=(
            "Owner discovery exposes 16 static resources and 21 resource templates. "
            "The default non-owner discovery filters that to 15 static resources and "
            "19 templates, or 34 total."
        ),
        predicate=lambda: _sidecar_counts_match_doc(),
        state="holds",
        truth=(
            "the sentence's four numbers are read back out of the document and "
            "compared to holdspeak.mcp.resources.list_resources for OWNER and for the "
            "default non-owner principal, so they cannot drift again silently"
        ),
        story="",
    ),
"""

PARKED_PREDICATES = r'''
def mcp_resource_counts() -> dict[str, int]:
    """Static/template counts for owner and default non-owner discovery."""
    from holdspeak.mcp import resources

    owner = resources.list_resources(_owner_principal())
    other = resources.list_resources(None)
    return {
        "owner_static": len(owner["resources"]),
        "owner_templates": len(owner["resourceTemplates"]),
        "nonowner_static": len(other["resources"]),
        "nonowner_templates": len(other["resourceTemplates"]),
        "nonowner_total": len(other["resources"]) + len(other["resourceTemplates"]),
    }


def _sidecar_counts_match_doc() -> bool:
    """Compare the four counts written in MCP_SIDECAR.md to the live server.

    The numbers are parsed back OUT of the document rather than typed here, so
    editing the prose without re-measuring fails, and a change in the real
    resource list fails too.
    """
    text = _read("docs/MCP_SIDECAR.md")
    match = re.search(
        r"Owner discovery exposes (\d+) static resources and (\d+) resource templates\."
        r"\s+The\s+default non-owner discovery filters that to (\d+) static resources and\s+"
        r"(\d+) templates, or (\d+) total\.",
        text,
    )
    if not match:
        return False
    written = [int(group) for group in match.groups()]
    live = mcp_resource_counts()
    return written == [
        live["owner_static"],
        live["owner_templates"],
        live["nonowner_static"],
        live["nonowner_templates"],
        live["nonowner_total"],
    ]


'''
