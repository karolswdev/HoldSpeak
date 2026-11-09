# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_mcp_sidecar_doc_drift.py to restore.

# ruff: noqa


# --- test_the_page_is_not_in_git: P8/P6: pins a .gitignore line and floor counts of the generated doc roster, no value a reader sees
def test_the_page_is_not_in_git() -> None:
    """The page is on demand: ignored, and the generator is in gen_docs.sh."""
    assert "docs/MCP_SIDECAR.md" in (REPO / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert "scripts/gen_mcp_sidecar_doc.py" in (REPO / "scripts" / "gen_docs.sh").read_text(encoding="utf-8")


# --- test_roster_is_not_vacuous: P8/P6: pins a .gitignore line and floor counts of the generated doc roster, no value a reader sees
def test_roster_is_not_vacuous(roster: dict) -> None:
    """The roster must carry the load-bearing families and tool count."""
    assert roster["total_tools"] >= 150, "registry went dark"
    assert roster["total_families"] >= 25, "family count collapsed"
    for expected in ("desk", "project", "thought", "people", "cadence"):
        assert expected in roster["families"], f"family {expected} missing"
