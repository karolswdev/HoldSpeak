# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_mcp_auth.py to restore.

# ruff: noqa


# --- test_mcpauth_has_no_url_attribute: P8: asserts a field removed in HS-133-08 is still absent (hasattr)
def test_mcpauth_has_no_url_attribute():
    """MCPAuth no longer carries a url field (removed in HS-133-08)."""
    assert not hasattr(MCPAuth, "url")
    auth = resolve_auth(environ={})
    assert not hasattr(auth, "url")
