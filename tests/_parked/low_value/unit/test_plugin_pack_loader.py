# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_plugin_pack_loader.py to restore.

# ruff: noqa


# --- test_first_party_registry_is_empty_today: P1/P8: pins that no first-party packs ship today
def test_first_party_registry_is_empty_today() -> None:
    """The 14 built-ins stay hardcoded; no first-party packs ship yet."""
    result = build_registry(user_packs_dir=Path("/nonexistent/plugin/packs"))
    assert result.packs == ()
    assert result.errors == ()
