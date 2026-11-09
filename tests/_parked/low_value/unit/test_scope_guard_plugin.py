# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_scope_guard_plugin.py to restore.

# ruff: noqa


# --- test_attributes: P1: asserts the plugin's declared id, kind and mode constants
def test_attributes() -> None:
    p = ScopeGuardPlugin()
    assert p.id == "scope_guard"
    assert p.kind == "validator"
    assert p.execution_mode == "deferred"
    assert p.required_capabilities == ["llm"]
