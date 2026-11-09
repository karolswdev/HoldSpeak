# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_brief_mcp.py to restore.

# ruff: noqa


# --- test_monday_brief_tool_returns_persisted_brief_structure: P6: checks the brief has keys, not any value the owner reads
def test_monday_brief_tool_returns_persisted_brief_structure(mcp_db: Database) -> None:
    generated = tools.dispatch("monday_brief.generate", {}, OWNER)

    latest = tools.dispatch("monday_brief.get", {}, OWNER)

    # HS-150-03: the adapter may add person_sections or person_sections_state;
    # strip adapter-composed keys before comparing persisted structure.
    _ADAPTER_KEYS = {"person_sections", "person_sections_state"}
    persisted_keys = set(latest) - _ADAPTER_KEYS
    assert persisted_keys == {
        "id", "period_start", "period_end", "headline", "sections", "generated_at",
        "is_empty", "shelf", "ledger",
    }
    assert set(latest["sections"]) == {"this_week", "changed", "broke", "waiting", "decisions"}
